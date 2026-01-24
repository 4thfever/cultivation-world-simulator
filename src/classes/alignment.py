from enum import Enum


class Alignment(Enum):
    """
    阵营：正/中立/邪。
    值使用英文，便于与代码/保存兼容；__str__ 返回翻译后的文本。
    """
    RIGHTEOUS = "RIGHTEOUS"  # 正
    NEUTRAL = "NEUTRAL"      # 中
    EVIL = "EVIL"            # 邪

    def __str__(self) -> str:
        from src.i18n import t
        return t(alignment_msg_ids.get(self, self.value))

    def get_info(self) -> str:
        # 简版：仅返回短文本
        from src.i18n import t
        return t(alignment_msg_ids[self])

    def get_detailed_info(self) -> str:
        # 详细版：短文本 + 详细描述
        from src.i18n import t
        return t("{alignment}: {description}", 
                 alignment=t(alignment_msg_ids[self]), 
                 description=t(alignment_info_msg_ids[self]))

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
            return other.upper() == self.value or other == str(self)
        return False

    @staticmethod
    def from_str(text: str) -> "Alignment":
        """
        将字符串解析为 Alignment，支持中文与英文别名。
        未识别时返回中立。
        """
        t = str(text).strip().upper()
        mapping = {
            "正": "RIGHTEOUS", "RIGHTEOUS": "RIGHTEOUS", "RIGHT": "RIGHTEOUS",
            "中": "NEUTRAL", "中立": "NEUTRAL", "NEUTRAL": "NEUTRAL", "MIDDLE": "NEUTRAL", "CENTER": "NEUTRAL",
            "邪": "EVIL", "EVIL": "EVIL"
        }
        align_id = mapping.get(t, "NEUTRAL")
        return Alignment(align_id)


alignment_msg_ids = {
    Alignment.RIGHTEOUS: "righteous",
    Alignment.NEUTRAL: "neutral",
    Alignment.EVIL: "evil",
}

alignment_info_msg_ids = {
    Alignment.RIGHTEOUS: "Righteous alignment follows the principles of helping the weak, maintaining order, and vanquishing evil.",
    Alignment.NEUTRAL: "Neutral alignment follows the principles of going with the flow, seeking benefit and avoiding harm, valuing self-cultivation and balance, and not easily taking sides.",
    Alignment.EVIL: "Evil alignment follows the principles of survival of the fittest, prioritizing self-interest above all, disdaining rules, and venerating power and fear. Acts ruthlessly, often resorting to murder and plunder.",
}

# 兼容性：保留旧的dict用于from_str方法
alignment_strs = {
    Alignment.RIGHTEOUS: "正",
    Alignment.NEUTRAL: "中立",
    Alignment.EVIL: "邪",
}
