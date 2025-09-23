"""
灵根
五行元素与灵根组合：
- RootElement：金、木、水、火、土
- Root：由一个或多个 RootElement 组成（单灵根、双灵根、天灵根）
"""
from enum import Enum
from typing import List, Tuple

from src.classes.essence import EssenceType


class RootElement(Enum):
    GOLD = "金"
    WOOD = "木"
    WATER = "水"
    FIRE = "火"
    EARTH = "土"

    def __str__(self) -> str:
        return self.value


class Root(Enum):
    """
    复合灵根定义：每个成员包含（中文名, 元素列表）
    """
    GOLD = ("金灵根", (RootElement.GOLD,))
    WOOD = ("木灵根", (RootElement.WOOD,))
    WATER = ("水灵根", (RootElement.WATER,))
    FIRE = ("火灵根", (RootElement.FIRE,))
    EARTH = ("土灵根", (RootElement.EARTH,))

    THUNDER = ("雷灵根", (RootElement.WATER, RootElement.EARTH))  # 水+土
    ICE = ("冰灵根", (RootElement.GOLD, RootElement.WATER))        # 金+水
    WIND = ("风灵根", (RootElement.WOOD, RootElement.WATER))        # 木+水
    DARK = ("暗灵根", (RootElement.FIRE, RootElement.EARTH))        # 火+土

    HEAVEN = (
        "天灵根",
        (
            RootElement.GOLD,
            RootElement.WOOD,
            RootElement.WATER,
            RootElement.FIRE,
            RootElement.EARTH,
        ),
    )

    def __new__(cls, cn_name: str, elements: Tuple[RootElement, ...]):
        obj = object.__new__(cls)
        obj._value_ = cn_name
        obj._elements = elements
        return obj

    @property
    def elements(self) -> Tuple[RootElement, ...]:
        return self._elements

    def __str__(self) -> str:
        return f"{self.value}({', '.join(str(e) for e in self.elements)})"

# 元素到灵气类型的一一对应
_essence_by_element = {
    RootElement.GOLD: EssenceType.GOLD,
    RootElement.WOOD: EssenceType.WOOD,
    RootElement.WATER: EssenceType.WATER,
    RootElement.FIRE: EssenceType.FIRE,
    RootElement.EARTH: EssenceType.EARTH,
}


def get_essence_types_for_root(root: Root) -> List[EssenceType]:
    """
    获取与该灵根匹配的灵气类型列表（任一元素匹配即视为可用）。
    """
    return [_essence_by_element[e] for e in root.elements]

roots = {
    "金": Root.GOLD,
    "木": Root.WOOD,
    "水": Root.WATER,
    "火": Root.FIRE,
    "土": Root.EARTH,
    "雷": Root.THUNDER,
    "冰": Root.ICE,
    "风": Root.WIND,
    "暗": Root.DARK,
    "天": Root.HEAVEN,
}