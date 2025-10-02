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


alignment_strs = {
    Alignment.RIGHTEOUS: "正",
    Alignment.EVIL: "邪",
}


