from enum import Enum


class WeaponType(Enum):
    """
    兵器类型枚举
    """
    SWORD = "剑"         # 包括剑匣等
    SABER = "刀"
    SPEAR = "枪"         # 包括矛、戟
    STAFF = "棍"         # 包括杖、棒
    FAN = "扇"
    WHIP = "鞭"
    ZITHER = "琴"        # 音律武器
    FLUTE = "笛"         # 包括箫
    
    def __str__(self) -> str:
        return self.value

