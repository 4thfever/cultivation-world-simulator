from enum import Enum


class WeaponType(Enum):
    """
    兵器类型枚举
    """
    SWORD = "SWORD"         # 剑
    SABER = "SABER"         # 刀
    SPEAR = "SPEAR"         # 枪
    STAFF = "STAFF"         # 棍
    FAN = "FAN"             # 扇
    WHIP = "WHIP"           # 鞭
    ZITHER = "ZITHER"       # 琴
    FLUTE = "FLUTE"         # 笛
    HIDDEN_WEAPON = "HIDDEN_WEAPON"  # 暗器
    
    def __str__(self) -> str:
        from src.i18n import t
        return t(weapon_type_msg_ids.get(self, self.value))

    @staticmethod
    def from_str(s: str) -> "WeaponType":
        s = str(s).strip().replace(" ", "_").upper()
        mapping = {
            "剑": "SWORD", "SWORD": "SWORD",
            "刀": "SABER", "SABER": "SABER",
            "枪": "SPEAR", "SPEAR": "SPEAR",
            "棍": "STAFF", "STAFF": "STAFF",
            "扇": "FAN", "FAN": "FAN",
            "鞭": "WHIP", "WHIP": "WHIP",
            "琴": "ZITHER", "ZITHER": "ZITHER",
            "笛": "FLUTE", "FLUTE": "FLUTE",
            "暗器": "HIDDEN_WEAPON", "HIDDEN_WEAPON": "HIDDEN_WEAPON", "HIDDEN WEAPON": "HIDDEN_WEAPON"
        }
        type_id = mapping.get(s, "SWORD")
        return WeaponType(type_id)


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

