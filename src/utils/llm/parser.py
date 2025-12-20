"""JSON 解析逻辑"""

import re
import json5
from .exceptions import ParseError


def parse_json(text: str) -> dict:
    """
    解析 JSON，支持从 markdown 代码块提取或直接解析
    """
    text = (text or '').strip()
    if not text:
        return {}
    
    # 策略1: 尝试从 Markdown 代码块提取
    # 优先匹配 json/json5 块，如果没有指定语言的块也尝试
    blocks = _extract_code_blocks(text)
    for lang, content in blocks:
        if not lang or lang in ("json", "json5"):
            try:
                obj = json5.loads(content)
                if isinstance(obj, dict):
                    return obj
            except Exception:
                continue
    
    # 策略2: 尝试整体解析
    # 有时候 LLM 不会输出 markdown，直接输出 json
    try:
        obj = json5.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    
    # 失败
    raise ParseError(
        "无法解析 JSON: 未找到有效的 JSON 对象或代码块",
        raw_text=text[:500]
    )


def _extract_code_blocks(text: str) -> list[tuple[str, str]]:
    """提取 markdown 代码块"""
    pattern = re.compile(r"```([^\n`]*)\n([\s\S]*?)```", re.DOTALL)
    blocks = []
    for lang, content in pattern.findall(text):
        blocks.append((lang.strip().lower(), content.strip()))
    return blocks
