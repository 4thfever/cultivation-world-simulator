from enum import Enum


class Alignment(Enum):
    """
    阵营：正/中立/邪。
    值使用英文，便于与代码/保存兼容；__str__ 返回中文。
    """
    RIGHTEOUS = "righteous"  # 正
    NEUTRAL = "neutral"      # 中
    EVIL = "evil"            # 邪

    def __str__(self) -> str:
        return alignment_strs.get(self, self.value)

    def get_info(self) -> str:
        return alignment_strs[self] + ": " + alignment_infos[self]

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other) -> bool:
        """
        允许与同类或字符串比较：
        - Alignment: 恒等比较
        - str: 同时支持英文值（value）与中文显示（__str__）
        """
        if isinstance(other, Alignment):
            return self is other
        if isinstance(other, str):
            return other == self.value or other == str(self)
        return False

    @staticmethod
    def from_str(text: str) -> "Alignment":
        """
        将字符串解析为 Alignment，支持中文与英文别名。
        未识别时返回中立。
        """
        t = str(text).strip().lower()
        if t in {"正", "righteous", "right"}:
            return Alignment.RIGHTEOUS
        if t in {"中", "neutral", "middle", "center"}:
            return Alignment.NEUTRAL
        if t in {"邪", "evil"}:
            return Alignment.EVIL
        return Alignment.NEUTRAL


alignment_strs = {
    Alignment.RIGHTEOUS: "正",
    Alignment.NEUTRAL: "中",
    Alignment.EVIL: "邪",
}

alignment_infos = {
    Alignment.RIGHTEOUS: "正义阵营的理念是：扶助弱小，维护秩序，除魔卫道。",
    Alignment.NEUTRAL: "中立阵营的理念是：顺势而为，趋利避害，重视自度与平衡，不轻易站队。",
    Alignment.EVIL: "邪恶阵营的理念是：弱肉强食，以自身利益为先，蔑视规则，推崇权力与恐惧。",
}

