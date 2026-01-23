"""
灵根
五行元素与灵根组合：
- RootElement：金、木、水、火、土（恒定不变）
- Root：硬编码定义（单/双/天灵根等），每个成员包含（中文名, 元素列表）
"""
from enum import Enum
from typing import List, Tuple, Dict
from collections import defaultdict
from src.utils.df import game_configs
from src.classes.effect import build_effects_map_from_df

from src.classes.essence import EssenceType


class RootElement(Enum):
    GOLD = "GOLD"  # 原：金
    WOOD = "WOOD"  # 原：木
    WATER = "WATER"  # 原：水
    FIRE = "FIRE"  # 原：火
    EARTH = "EARTH"  # 原：土

    def __str__(self) -> str:
        from src.i18n import t
        return t(root_element_msg_ids.get(self, self.value))


root_element_msg_ids = {
    RootElement.GOLD: "gold_element",
    RootElement.WOOD: "wood_element",
    RootElement.WATER: "water_element",
    RootElement.FIRE: "fire_element",
    RootElement.EARTH: "earth_element",
}


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

    GOLD = ("root_gold", (RootElement.GOLD,))
    WOOD = ("root_wood", (RootElement.WOOD,))
    WATER = ("root_water", (RootElement.WATER,))
    FIRE = ("root_fire", (RootElement.FIRE,))
    EARTH = ("root_earth", (RootElement.EARTH,))
    THUNDER = ("root_thunder", (RootElement.WATER, RootElement.EARTH))
    ICE = ("root_ice", (RootElement.GOLD, RootElement.WATER))
    WIND = ("root_wind", (RootElement.WOOD, RootElement.WATER))
    DARK = ("root_dark", (RootElement.FIRE, RootElement.EARTH))
    HEAVEN = (
        "root_heaven",
        (
            RootElement.GOLD,
            RootElement.WOOD,
            RootElement.WATER,
            RootElement.FIRE,
            RootElement.EARTH,
        ),
    )

    def get_info(self) -> str:
        return format_root_cn(self)

    def get_detailed_info(self) -> str:
        return self.get_info()

    @property
    def effects(self) -> dict[str, object]:
        """
        从 CSV 读取的该灵根效果。
        """
        return dict(_root_effects_by_root.get(self, {}))

    @property
    def effect_desc(self) -> str:
        """
        获取灵根效果的文本描述。
        """
        return _root_effect_desc_by_root.get(self, "")


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


def _parse_root_key(raw: str) -> "Root":
    return Root[raw]


_root_effects_by_root = build_effects_map_from_df(
    game_configs.get("root"),
    key_column="key",
    parse_key=_parse_root_key,
    effects_column="effects",
)

from src.classes.effect import format_effects_to_text
_root_effect_desc_by_root = {
    root: format_effects_to_text(effects)
    for root, effects in _root_effects_by_root.items()
}

def format_root_cn(root: "Root") -> str:
    """
    将 Root 显示为中文短名 + 组成，例如：
    - 天（金、木、水、火、土）
    - 风（木、水）
    - 金（金）
    回退：若无法获取组成则仅显示短名。
    """
    from src.i18n import t
    # Root 成员的 value 为 msgid (如 "root_wind")
    name_key = getattr(root, "value", str(root))
    translated_name = t(name_key)
    
    # 尝试获取短名（不带 "Root" 或 "灵根"）
    # 我们可以在翻译文件中另外定义短名 keys，或者在这里处理字符串
    # 为了简单优雅，我们可以假设 Root 的翻译不包含 "Root"/"灵根" 后缀，或者我们在 key 上区分
    # 方案：定义 root_short_wind -> "风" / "Wind"
    # 但为了兼容现有结构，我们先简单处理翻译后的字符串。
    
    short_name = translated_name.replace("灵根", "").replace(" Root", "")
    
    elements = getattr(root, "elements", None)
    if not elements:
        return short_name
    # RootElement.__str__ 返回翻译后的值
    elements_cn = t("element_separator").join(str(e) for e in elements)
    return t("{root_name} ({elements})", root_name=short_name, elements=elements_cn)