"""JSON 解析逻辑"""

import re
import json5
from .exceptions import ParseError


def parse_json(text: str) -> dict:
    """
    主解析入口，依次尝试多种策略
    
    Args:
        text: 待解析的文本
        
    Returns:
        dict: 解析结果
        
    Raises:
        ParseError: 所有策略均失败时抛出
    """
    text = (text or '').strip()
    if not text:
        return {}
    
    strategies = [
        try_parse_code_blocks,
        try_parse_balanced_json,
        try_parse_whole_text,
    ]
    
    errors = []
    for strategy in strategies:
        result = strategy(text)
        if result is not None:
            return result
        errors.append(f"{strategy.__name__}")
    
    # 抛出详细错误
    raise ParseError(
        f"所有解析策略均失败: {', '.join(errors)}",
        raw_text=text[:500]  # 只保留前 500 字符避免日志过长
    )


def try_parse_code_blocks(text: str) -> dict | None:
    """
    尝试从代码块解析 JSON
    
    Args:
        text: 待解析的文本
        
    Returns:
        dict | None: 解析成功返回字典，失败返回 None
    """
    blocks = _extract_code_blocks(text)
    
    # 只处理 json/json5 或未标注语言的代码块
    for lang, block in blocks:
        if lang and lang not in ("json", "json5"):
            continue
        
        # 先在块内找平衡对象
        span = _find_balanced_json_object(block)
        candidates = [span] if span else [block]
        
        for cand in candidates:
            if not cand:
                continue
            try:
                obj = json5.loads(cand)
                if isinstance(obj, dict):
                    return obj
            except Exception:
                continue
    
    return None


def try_parse_balanced_json(text: str) -> dict | None:
    """
    尝试提取并解析平衡的 JSON 对象
    
    Args:
        text: 待解析的文本
        
    Returns:
        dict | None: 解析成功返回字典，失败返回 None
    """
    json_span = _find_balanced_json_object(text)
    if json_span:
        try:
            obj = json5.loads(json_span)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
    
    return None


def try_parse_whole_text(text: str) -> dict | None:
    """
    尝试整体解析为 JSON
    
    Args:
        text: 待解析的文本
        
    Returns:
        dict | None: 解析成功返回字典，失败返回 None
    """
    try:
        obj = json5.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    
    return None


def _extract_code_blocks(text: str) -> list[tuple[str, str]]:
    """
    提取所有 markdown 代码块
    
    Args:
        text: 待提取的文本
        
    Returns:
        list[tuple[str, str]]: (语言, 内容) 元组列表
    """
    pattern = re.compile(r"```([^\n`]*)\n([\s\S]*?)```", re.DOTALL)
    blocks = []
    for lang, content in pattern.findall(text):
        blocks.append((lang.strip().lower(), content.strip()))
    return blocks


def _find_balanced_json_object(text: str) -> str | None:
    """
    在文本中扫描并返回首个平衡的花括号 {...} 片段
    忽略字符串中的括号
    
    Args:
        text: 待扫描的文本
        
    Returns:
        str | None: 找到则返回子串，否则返回 None
    """
    depth = 0
    start_index = None
    in_string = False
    string_char = ''
    escape = False
    
    for idx, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
                continue
            if ch == '\\':
                escape = True
                continue
            if ch == string_char:
                in_string = False
            continue
        
        if ch in ('"', "'"):
            in_string = True
            string_char = ch
            continue
        
        if ch == '{':
            if depth == 0:
                start_index = idx
            depth += 1
            continue
        
        if ch == '}':
            if depth > 0:
                depth -= 1
                if depth == 0 and start_index is not None:
                    return text[start_index:idx + 1]
    
    return None

