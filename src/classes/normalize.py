"""
名称规范化工具模块

提供统一的名称规范化函数，用于处理各类名称中的括号和附加信息。
"""

def remove_parentheses(name: str, recursive: bool = False) -> str:
    """
    通用括号移除函数。
    
    Args:
        name: 原始字符串
        recursive: 是否递归移除所有括号（处理嵌套括号）
    """
    s = str(name).strip()
    brackets = [
        ("(", ")"), ("（", "）"),
        ("[", "]"), ("【", "】"),
        ("「", "」"), ("『", "』"),
        ("<", ">"), ("《", "》")
    ]
    
    while True:
        found = False
        for left, right in brackets:
            # 查找最外层的左括号
            start = s.find(left)
            if start != -1:
                # 查找对应的右括号（从后往前找或者从前往后找匹配的）
                # 简单策略：找最后一个右括号，或者找匹配的。
                # 原有逻辑 region 使用的是 rfind，这里我们采用更稳健的逻辑：
                # 既然是 remove，通常是去除说明性文字，保留主体。
                
                # 策略：找到第一个左括号，和其对应的配对右括号（如果简单处理，直接找最后一个右括号可能误删）
                # 但为了保持和原有 region 逻辑一致（处理 "青云林海（千年古松（金丹））" -> "青云林海"），
                # 只要发现左括号，就切断到末尾或者切断到匹配的右括号。
                
                # 简化逻辑：找到第一个左括号，直接截断。这适用于绝大多数 "Name (Info)" 的情况。
                s = s[:start].strip()
                found = True
                break
        
        if not recursive or not found:
            break
            
    return s.strip()

def normalize_name(name: str) -> str:
    """
    最通用的规范化：去除括号及其内容。
    """
    return remove_parentheses(name)

# --- 兼容特定业务逻辑的别名或特化 ---

def normalize_avatar_name(name: str) -> str:
    return remove_parentheses(name)

def normalize_region_name(name: str) -> str:
    # 地区名可能包含多层嵌套，使用递归模式虽然在这里和非递归效果可能一样（因为都是截断），
    # 但保持接口定义清晰。对于截断策略，递归其实没有意义，因为第一次就截断了。
    # 除非括号在中间： "Region(Info) Suffix" -> "Region Suffix"？
    # 目前游戏里的命名习惯通常后缀是括号说明，所以直接截断是安全的。
    return remove_parentheses(name)

def normalize_goods_name(name: str) -> str:
    """物品名额外去除尾部的 ' -'"""
    s = remove_parentheses(name)
    return s.rstrip(" -").strip()

def normalize_weapon_type(name: str) -> str:
    s = str(name).strip()
    for suffix in ["类", "兵器", "武器"]:
        if s.endswith(suffix):
            s = s[:-len(suffix)].strip()
    return s
