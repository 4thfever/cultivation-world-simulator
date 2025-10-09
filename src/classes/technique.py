from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, List

from src.utils.df import game_configs
from src.classes.alignment import Alignment
from src.classes.root import Root, RootElement


class TechniqueAttribute(Enum):
    GOLD = "金"
    WOOD = "木"
    WATER = "水"
    FIRE = "火"
    EARTH = "土"
    ICE = "冰"
    WIND = "风"
    DARK = "暗"
    THUNDER = "雷"
    EVIL = "邪"

    def __str__(self) -> str:
        return self.value


class TechniqueGrade(Enum):
    LOWER = "下品"
    MIDDLE = "中品"
    UPPER = "上品"

    @staticmethod
    def from_str(s: str) -> "TechniqueGrade":
        s = str(s).strip()
        if s == "上品":
            return TechniqueGrade.UPPER
        if s == "中品":
            return TechniqueGrade.MIDDLE
        return TechniqueGrade.LOWER


@dataclass
class Technique:
    id: int
    name: str
    attribute: TechniqueAttribute
    grade: TechniqueGrade
    prompt: str
    weight: float
    condition: str
    # 归属宗门名称；None/空表示无宗门要求（散修可修）
    sect: Optional[str] = None

    def is_allowed_for(self, avatar) -> bool:
        if not self.condition:
            return True
        return bool(eval(self.condition, {"__builtins__": {}}, {"avatar": avatar, "Alignment": Alignment}))


# 五行与扩展属性的克制关系
# - 五行：金克木，木克土，土克水，水克火，火克金
# - 雷克邪；邪、冰、风、暗不克任何人
SUPPRESSION: dict[TechniqueAttribute, set[TechniqueAttribute]] = {
    TechniqueAttribute.GOLD: {TechniqueAttribute.WOOD},
    TechniqueAttribute.WOOD: {TechniqueAttribute.EARTH},
    TechniqueAttribute.EARTH: {TechniqueAttribute.WATER},
    TechniqueAttribute.WATER: {TechniqueAttribute.FIRE},
    TechniqueAttribute.FIRE: {TechniqueAttribute.GOLD},
    TechniqueAttribute.THUNDER: {TechniqueAttribute.EVIL},
    TechniqueAttribute.ICE: set(),
    TechniqueAttribute.WIND: set(),
    TechniqueAttribute.DARK: set(),
    TechniqueAttribute.EVIL: set(),
}


def loads() -> tuple[dict[int, Technique], dict[str, Technique]]:
    techniques_by_id: dict[int, Technique] = {}
    techniques_by_name: dict[str, Technique] = {}
    df = game_configs["technique"]
    for _, row in df.iterrows():
        attr = TechniqueAttribute(str(row["technique_root"]).strip())
        name = str(row["name"]).strip()
        grade = TechniqueGrade.from_str(row.get("grade", "下品"))
        cond_val = row.get("condition", "")
        condition = "" if str(cond_val) == "nan" else str(cond_val).strip()
        weight_val = row.get("weight", 1)
        weight = float(str(weight_val)) if str(weight_val) != "nan" else 1.0
        sect_val = row.get("sect", "")
        sect = None if str(sect_val) == "nan" or str(sect_val).strip() == "" else str(sect_val).strip()
        t = Technique(
            id=int(row["id"]),
            name=name,
            attribute=attr,
            grade=grade,
            prompt=str(row.get("prompt", "")),
            weight=weight,
            condition=condition,
            sect=sect,
        )
        techniques_by_id[t.id] = t
        techniques_by_name[t.name] = t
    return techniques_by_id, techniques_by_name


techniques_by_id, techniques_by_name = loads()


def is_attribute_compatible_with_root(attr: TechniqueAttribute, root: Root) -> bool:
    if attr == TechniqueAttribute.EVIL:
        # 邪功法仅由阵营约束，这里视为与灵根无关
        return True

    # 天灵根：除邪外全系可修
    if root == Root.HEAVEN:
        return attr != TechniqueAttribute.EVIL

    # 单属性灵根：只能修行对应属性
    single_map = {
        Root.GOLD: TechniqueAttribute.GOLD,
        Root.WOOD: TechniqueAttribute.WOOD,
        Root.WATER: TechniqueAttribute.WATER,
        Root.FIRE: TechniqueAttribute.FIRE,
        Root.EARTH: TechniqueAttribute.EARTH,
    }
    if root in single_map:
        return attr == single_map[root]

    # 复合/扩展灵根：根名属性 + 其元素列表中的属性
    complex_map: dict[Root, set[TechniqueAttribute]] = {
        Root.ICE: {TechniqueAttribute.ICE, TechniqueAttribute.GOLD, TechniqueAttribute.WATER},
        Root.WIND: {TechniqueAttribute.WIND, TechniqueAttribute.WOOD, TechniqueAttribute.WATER},
        Root.DARK: {TechniqueAttribute.DARK, TechniqueAttribute.FIRE, TechniqueAttribute.EARTH},
        Root.THUNDER: {TechniqueAttribute.THUNDER, TechniqueAttribute.WATER, TechniqueAttribute.EARTH},
    }
    if root in complex_map:
        return attr in complex_map[root]

    return False


def get_random_technique_for_avatar(avatar) -> Technique:
    import random
    candidates: List[Technique] = []
    for t in techniques_by_id.values():
        if not t.is_allowed_for(avatar):
            continue
        if t.attribute == TechniqueAttribute.EVIL and avatar.alignment != Alignment.EVIL:
            continue
        if not is_attribute_compatible_with_root(t.attribute, avatar.root):
            continue
        candidates.append(t)
    if not candidates:
        # 回退：不考虑条件，仅按灵根兼容挑选（若仍为空，则全量）
        fallback = [
            t for t in techniques_by_id.values()
            if (t.attribute != TechniqueAttribute.EVIL) and is_attribute_compatible_with_root(t.attribute, avatar.root)
        ]
        candidates = fallback or list(techniques_by_id.values())
    weights = [max(0.0, t.weight) for t in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


def get_technique_by_sect(sect) -> Technique:
    """
    简化版：仅按宗门筛选并按权重抽样，不考虑灵根与 condition。
    - 散修（sect 为 None/空）：只从无宗门要求（sect 为空）的功法中抽样；
    - 有宗门：从“无宗门 + 该宗门”的功法中抽样；
    若集合为空，则退回全量功法。
    """
    import random

    sect_name: Optional[str] = None
    if sect is not None:
        sect_name = getattr(sect, "name", sect)
        if isinstance(sect_name, str):
            sect_name = sect_name.strip() or None

    allowed_sects: set[Optional[str]] = {None, ""}
    if sect_name is not None:
        allowed_sects.add(sect_name)

    def _in_allowed_sect(t: Technique) -> bool:
        return (t.sect in allowed_sects) or (t.sect is None) or (t.sect == "")

    candidates: List[Technique] = [t for t in techniques_by_id.values() if _in_allowed_sect(t)]
    if not candidates:
        candidates = list(techniques_by_id.values())
    weights = [max(0.0, t.weight) for t in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


def get_grade_bonus(grade: TechniqueGrade) -> float:
    if grade is TechniqueGrade.UPPER:
        return 0.10
    if grade is TechniqueGrade.MIDDLE:
        return 0.05
    return 0.0


def get_suppression_bonus(att_attr: TechniqueAttribute, def_attr: TechniqueAttribute) -> float:
    return 0.10 if def_attr in SUPPRESSION.get(att_attr, set()) else 0.0


# 相对品阶优势加成：按“品阶差×步进”的方式计算
# - 品阶映射：下品=0，中品=1，上品=2
# - 每级差距步进：5%（最大±10%）
_GRADE_RANK: dict[TechniqueGrade, int] = {
    TechniqueGrade.LOWER: 0,
    TechniqueGrade.MIDDLE: 1,
    TechniqueGrade.UPPER: 2,
}


def get_grade_advantage_bonus(attacker_grade: Optional[TechniqueGrade], defender_grade: Optional[TechniqueGrade]) -> float:
    """
    根据双方品阶差计算进攻方的相对加成：
    - diff = rank(att) - rank(def)
    - bonus = 0.05 × diff，夹紧到 [-0.10, 0.10]
    - 任一为空则视为无加成
    返回：进攻方概率或伤害的相对加成（可为负）。
    """
    if attacker_grade is None or defender_grade is None:
        return 0.0
    diff = _GRADE_RANK[attacker_grade] - _GRADE_RANK[defender_grade]
    bonus = 0.05 * diff
    if bonus > 0.10:
        bonus = 0.10
    if bonus < -0.10:
        bonus = -0.10
    return bonus



# 将功法属性映射为默认的灵根（邪功法不返回）
def attribute_to_root(attr: TechniqueAttribute) -> Optional[Root]:
    mapping: dict[TechniqueAttribute, Root] = {
        TechniqueAttribute.GOLD: Root.GOLD,
        TechniqueAttribute.WOOD: Root.WOOD,
        TechniqueAttribute.WATER: Root.WATER,
        TechniqueAttribute.FIRE: Root.FIRE,
        TechniqueAttribute.EARTH: Root.EARTH,
        TechniqueAttribute.THUNDER: Root.THUNDER,
        TechniqueAttribute.ICE: Root.ICE,
        TechniqueAttribute.WIND: Root.WIND,
        TechniqueAttribute.DARK: Root.DARK,
    }
    return mapping.get(attr)
