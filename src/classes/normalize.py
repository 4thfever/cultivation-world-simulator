"""
名称规范化工具模块

提供统一的名称规范化函数，用于处理各类名称中的括号和附加信息。
适用于：角色名、地区名、物品名等。
"""


def _remove_parentheses(name: str) -> str:
    """
    通用的括号移除函数：去除字符串中首个括号及其内容。
    
    支持的括号类型：() （） [] 【】 「」 『』 <> 《》
    
    Args:
        name: 原始字符串
        
    Returns:
        去除首个括号后的字符串（去除前后空格）
        
    Examples:
        >>> _remove_parentheses("张三（元婴）")
        '张三'
        >>> _remove_parentheses("青云林海（千年古松（金丹））")
        '青云林海'
        >>> _remove_parentheses("青云鹿角 -（练气）")
        '青云鹿角 -'
    """
    s = str(name).strip()
    brackets = [
        ("(", ")"), ("（", "）"),
        ("[", "]"), ("【", "】"),
        ("「", "」"), ("『", "』"),
        ("<", ">"), ("《", "》")
    ]
    
    for left, right in brackets:
        idx = s.find(left)
        if idx != -1:
            # 找到左括号，去除从此开始到字符串末尾的内容
            s = s[:idx].strip()
            break
    
    return s


def normalize_avatar_name(name: str) -> str:
    """
    规范化角色名字：去除括号及其中的附加信息（如境界）。
    
    Args:
        name: 原始角色名字，可能包含境界等附加信息
        
    Returns:
        规范化后的角色名字
        
    Examples:
        >>> normalize_avatar_name("张三（元婴）")
        '张三'
        >>> normalize_avatar_name("张三，境界：元婴")
        '张三，境界：元婴'
    """
    return _remove_parentheses(name)


def normalize_region_name(name: str) -> str:
    """
    规范化地区名称：去除括号及其中的附加信息（如灵气密度、动植物等）。
    
    处理多层括号：递归去除所有括号及其内容。
    
    Args:
        name: 原始地区名称，可能包含资源等附加信息
        
    Returns:
        规范化后的地区名称
        
    Examples:
        >>> normalize_region_name("太白金府（金行灵气：10）")
        '太白金府'
        >>> normalize_region_name("青云林海（千年古松（金丹））")
        '青云林海'
    """
    s = str(name).strip()
    brackets = [
        ("(", ")"), ("（", "）"),
        ("[", "]"), ("【", "】"),
        ("「", "」"), ("『", "』"),
        ("<", ">"), ("《", "》")
    ]
    
    # 递归去除所有括号（用于处理嵌套括号）
    while True:
        found = False
        for left, right in brackets:
            start = s.find(left)
            end = s.rfind(right)
            if start != -1 and end != -1 and end > start:
                s = (s[:start] + s[end + 1:]).strip()
                found = True
                break
        if not found:
            break
    
    return s


def normalize_item_name(name: str) -> str:
    """
    规范化物品名称：去除境界标识等附加信息。
    
    处理格式：
    - "青云鹿角 -（练气）" -> "青云鹿角"
    - "风速马皮（筑基）" -> "风速马皮"
    
    Args:
        name: 原始物品名称，可能包含境界等附加信息
        
    Returns:
        规范化后的物品名称
        
    Examples:
        >>> normalize_item_name("青云鹿角 -（练气）")
        '青云鹿角'
        >>> normalize_item_name("风速马皮（筑基）")
        '风速马皮'
    """
    s = _remove_parentheses(name)
    # 额外处理：去除尾部的 " -" 标记
    s = s.rstrip(" -").strip()
    return s

