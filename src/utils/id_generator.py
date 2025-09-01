"""
简化的ID生成器，替代UUID4
"""

import random
import string


def base62_id(length: int = 8) -> str:
    """
    生成base62编码的短ID（数字+大小写字母）
    默认8位，比UUID4的36位短很多
    """
    charset = string.ascii_letters + string.digits  # 0-9, a-z, A-Z (62个字符)
    return ''.join(random.choices(charset, k=length))


def get_avatar_id() -> str:
    """获取Avatar ID的默认函数"""
    return base62_id(8)
