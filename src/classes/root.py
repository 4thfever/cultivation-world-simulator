"""
灵根
五行元素与灵根组合：
- RootElement：金、木、水、火、土（恒定不变）
- Root：从 CSV 配置加载（单/双/天灵根等），每个成员包含（中文名, 元素列表）
"""
from enum import Enum
from typing import List, Tuple, Dict
from collections import defaultdict

from src.classes.essence import EssenceType
from src.utils.df import game_configs
from src.utils.config import CONFIG


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


def _build_root_members_from_csv() -> Dict[str, tuple]:
    """
    从 CSV 读取 Root 定义，返回用于创建枚举的 members 映射。
    CSV 列：id,key,name,element_list，其中 element_list 用分号分隔中文名（如：金;木）。
    """
    df = game_configs.get("root")
    sep = CONFIG.df.ids_separator
    members: Dict[str, tuple] = {}
    for _, row in df.iterrows():
        key = str(row["key"]).strip()
        cn_name = str(row["name"]).strip()
        elements_field = str(row["element_list"]).strip()
        element_names = [s.strip() for s in elements_field.split(sep) if str(s).strip()]
        element_members: List[RootElement] = []
        for en in element_names:
            try:
                # RootElement 的值即为中文名，因此可直接用中文构造
                element_members.append(RootElement(en))
            except Exception as e:
                raise ValueError(f"root.csv 中未知的元素名称: {en}") from e
        members[key] = (cn_name, tuple(element_members))
    return members


# 动态创建 Root 枚举（使用 mixin 作为 type，使 __new__ 生效）
Root = Enum("Root", _build_root_members_from_csv(), type=_RootMixin)


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


def _load_extra_breakthrough_success_rate_from_csv() -> Dict["Root", float]:
    """
    从 root.csv 载入各灵根的额外突破成功率，默认0。
    列名：extra_breakthrough_success_rate
    """
    df = game_configs.get("root")
    if df is None:
        return {}
    bonuses: Dict["Root", float] = {}
    for _, row in df.iterrows():
        key = str(row["key"]).strip()
        try:
            root_member = getattr(Root, key)
        except AttributeError:
            # CSV 中的 key 未在 Root 中注册（理论不可能），跳过
            continue
        try:
            bonus = float(row.get("extra_breakthrough_success_rate", 0) or 0)
        except Exception:
            bonus = 0.0
        bonuses[root_member] = bonus
    return bonuses


# 从配置构造带默认值的加成表
extra_breakthrough_success_rate = defaultdict(
    lambda: 0.0,
    _load_extra_breakthrough_success_rate_from_csv(),
)