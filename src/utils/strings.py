def to_snake_case(name: str) -> str:
    """将驼峰/帕斯卡命名转换为蛇形命名。"""
    chars = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0:
            chars.append('_')
        chars.append(ch.lower())
    return ''.join(chars)


