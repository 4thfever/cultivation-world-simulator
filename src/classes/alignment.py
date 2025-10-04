from enum import Enum


class Alignment(Enum):
    """
    阵营：正/邪。
    值使用英文，便于与代码/保存兼容；__str__ 返回中文。
    """
    RIGHTEOUS = "righteous"  # 正
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


alignment_strs = {
    Alignment.RIGHTEOUS: "正",
    Alignment.EVIL: "邪",
}

alignment_infos = {
    Alignment.RIGHTEOUS: "正义阵营的理念是：扶助弱小，维护秩序，除魔卫道。",
    Alignment.EVIL: "邪恶阵营的理念是：弱肉强食，以自身利益为先，蔑视规则，推崇权力与恐惧。",
}

