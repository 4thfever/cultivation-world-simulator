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
    HIDDEN_WEAPON = "暗器"  # 暗器，如飞针、袖箭等
    
    def __str__(self) -> str:
        from src.i18n import t
        return t(weapon_type_msg_ids.get(self, self.value))


weapon_type_msg_ids = {
    WeaponType.SWORD: "sword",
    WeaponType.SABER: "saber",
    WeaponType.SPEAR: "spear",
    WeaponType.STAFF: "staff",
    WeaponType.FAN: "fan",
    WeaponType.WHIP: "whip",
    WeaponType.ZITHER: "zither",
    WeaponType.FLUTE: "flute",
    WeaponType.HIDDEN_WEAPON: "hidden_weapon",
}

