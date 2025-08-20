from enum import Enum


class EssenceType(Enum):
    """
    灵气类型
    """
    GOLD = "gold" # 金
    WOOD = "wood" # 木
    WATER = "water" # 水
    FIRE = "fire" # 火
    EARTH = "earth" # 土

    def __str__(self) -> str:
        """返回灵气类型的中文名称"""
        return essence_names.get(self, self.value)

essence_names = {
    EssenceType.GOLD: "金",
    EssenceType.WOOD: "木",
    EssenceType.WATER: "水",
    EssenceType.FIRE: "火",
    EssenceType.EARTH: "土"
}

class Essence():
    """
    灵气，用来描述某个region的灵气情况。
    灵气分为五种：金木水火土（先这些，之后加新的）
    每个region有五种灵气，每种灵气有不同的浓度。
    浓度从0~10。
    """
    def __init__(self, density: dict[EssenceType, int]):
        self.density = density

    def get_density(self, essence_type: EssenceType) -> int:
        return self.density[essence_type]

    def set_density(self, essence_type: EssenceType, density: int):
        self.density[essence_type] = density
