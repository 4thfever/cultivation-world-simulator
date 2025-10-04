"""
灵根
五行元素与灵根组合：
- RootElement：金、木、水、火、土（恒定不变）
- Root：硬编码定义（单/双/天灵根等），每个成员包含（中文名, 元素列表）
"""
from enum import Enum
from typing import List, Tuple, Dict
from collections import defaultdict

from src.classes.essence import EssenceType


class RootElement(Enum):
    GOLD = "金"
    WOOD = "木"
    WATER = "水"
    FIRE = "火"
    EARTH = "土"

    def __str__(self) -> str:
        return self.value


class _RootMixin:
    """
    Root 的基础实现：成员值为 (中文名, 元素元组)。
    通过功能式 API 动态创建真正的 Root 枚举。
    """

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


class Root(_RootMixin, Enum):
    """
    灵根（硬编码）：成员值为 (中文名, 元素元组)。
    数据来源原为 CSV，现改为内置：
    - GOLD: 金灵根 -> 金
    - WOOD: 木灵根 -> 木
    - WATER: 水灵根 -> 水
    - FIRE: 火灵根 -> 火
    - EARTH: 土灵根 -> 土
    - THUNDER: 雷灵根 -> 水;土
    - ICE: 冰灵根 -> 金;水
    - WIND: 风灵根 -> 木;水
    - DARK: 暗灵根 -> 火;土
    - HEAVEN: 天灵根 -> 金;木;水;火;土（额外突破+0.1）
    """

    GOLD = ("金灵根", (RootElement.GOLD,))
    WOOD = ("木灵根", (RootElement.WOOD,))
    WATER = ("水灵根", (RootElement.WATER,))
    FIRE = ("火灵根", (RootElement.FIRE,))
    EARTH = ("土灵根", (RootElement.EARTH,))
    THUNDER = ("雷灵根", (RootElement.WATER, RootElement.EARTH))
    ICE = ("冰灵根", (RootElement.GOLD, RootElement.WATER))
    WIND = ("风灵根", (RootElement.WOOD, RootElement.WATER))
    DARK = ("暗灵根", (RootElement.FIRE, RootElement.EARTH))
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


# 元素到灵气类型的一一对应
_essence_by_element = {
    RootElement.GOLD: EssenceType.GOLD,
    RootElement.WOOD: EssenceType.WOOD,
    RootElement.WATER: EssenceType.WATER,
    RootElement.FIRE: EssenceType.FIRE,
    RootElement.EARTH: EssenceType.EARTH,
}


def get_essence_types_for_root(root: "Root") -> List[EssenceType]:
    """
    获取与该灵根匹配的灵气类型列表（任一元素匹配即视为可用）。
    """
    return [_essence_by_element[e] for e in root.elements]


# 额外突破成功率（默认 0.0），根据原 CSV 保留天灵根 0.1
extra_breakthrough_success_rate = defaultdict(
    lambda: 0.0,
    {
        Root.HEAVEN: 0.1,
    },
)


def format_root_cn(root: "Root") -> str:
    """
    将 Root 显示为中文短名 + 组成，例如：
    - 天（金、木、水、火、土）
    - 风（木、水）
    - 金（金）
    回退：若无法获取组成则仅显示短名。
    """
    # Root 成员的 value 为中文名（如“风灵根”、“天灵根”）
    name = getattr(root, "value", str(root))
    short_name = name.replace("灵根", "") if isinstance(name, str) else str(root)
    elements = getattr(root, "elements", None)
    if not elements:
        return short_name
    # RootElement.__str__ 返回其中文值，因此直接 str(e)
    elements_cn = "、".join(str(e) for e in elements)
    return f"{short_name}（{elements_cn}）"