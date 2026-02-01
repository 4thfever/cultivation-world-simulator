from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List
import json
from src.classes.effect import load_effect_from_str
from src.classes.color import Color, TECHNIQUE_GRADE_COLORS

from src.utils.df import game_configs, get_str, get_float, get_int
from src.classes.alignment import Alignment
from src.classes.root import Root, RootElement


class TechniqueAttribute(Enum):
    GOLD = "GOLD"  # 金
    WOOD = "WOOD"  # 木
    WATER = "WATER"#水
    FIRE = "FIRE"  # 火
    EARTH = "EARTH"# 土
    ICE = "ICE"    # 冰
    WIND = "WIND"  # 风
    DARK = "DARK"  # 暗
    THUNDER = "THUNDER"  # 雷
    EVIL = "EVIL"  # 邪

    def __str__(self) -> str:
        from src.i18n import t
        return t(technique_attribute_msg_ids.get(self, self.value))


technique_attribute_msg_ids = {
    TechniqueAttribute.GOLD: "gold_attribute",
    TechniqueAttribute.WOOD: "wood_attribute",
    TechniqueAttribute.WATER: "water_attribute",
    TechniqueAttribute.FIRE: "fire_attribute",
    TechniqueAttribute.EARTH: "earth_attribute",
    TechniqueAttribute.ICE: "ice_attribute",
    TechniqueAttribute.WIND: "wind_attribute",
    TechniqueAttribute.DARK: "dark_attribute",
    TechniqueAttribute.THUNDER: "thunder_attribute",
    TechniqueAttribute.EVIL: "evil_attribute",
}


class TechniqueGrade(Enum):
    LOWER = "LOWER"    # 下品
    MIDDLE = "MIDDLE"  # 中品
    UPPER = "UPPER"    # 上品

    def __str__(self) -> str:
        from src.i18n import t
        return t(technique_grade_msg_ids.get(self, self.value))

    @staticmethod
    def from_str(s: str) -> "TechniqueGrade":
        s = str(s).strip().upper()
        # 兼容旧的中文配置（可选，但为了稳妥建议保留映射或直接转换）
        mapping = {
            "上品": "UPPER", "UPPER": "UPPER",
            "中品": "MIDDLE", "MIDDLE": "MIDDLE",
            "下品": "LOWER", "LOWER": "LOWER"
        }
        grade_id = mapping.get(s, "LOWER")
        return TechniqueGrade(grade_id)
    
    @property
    def color_rgb(self) -> tuple[int, int, int]:
        """返回功法品阶对应的RGB颜色值"""
        color_map = {
            TechniqueGrade.LOWER: TECHNIQUE_GRADE_COLORS["LOWER"],
            TechniqueGrade.MIDDLE: TECHNIQUE_GRADE_COLORS["MIDDLE"],
            TechniqueGrade.UPPER: TECHNIQUE_GRADE_COLORS["UPPER"],
        }
        return color_map.get(self, Color.COMMON_WHITE)


technique_grade_msg_ids = {
    TechniqueGrade.LOWER: "lower_grade",
    TechniqueGrade.MIDDLE: "middle_grade",
    TechniqueGrade.UPPER: "upper_grade",
}


@dataclass
class Technique:
    id: int
    name: str
    attribute: TechniqueAttribute
    grade: TechniqueGrade
    desc: str
    weight: float
    condition: str
    # 归属宗门ID；None 表示无宗门要求（散修可修）
    sect_id: Optional[int] = None
    # 影响角色或系统的效果
    effects: dict[str, object] = field(default_factory=dict)
    effect_desc: str = ""

    def is_allowed_for(self, avatar) -> bool:
        if not self.condition:
            return True
        return bool(eval(self.condition, {"__builtins__": {}}, {"avatar": avatar, "Alignment": Alignment}))

    def get_info(self, detailed: bool = False) -> str:
        if detailed:
            return self.get_detailed_info()
        from src.i18n import t
        return t("{name} ({attribute}) {grade}", name=self.name, attribute=str(self.attribute), grade=str(self.grade))

    def get_detailed_info(self) -> str:
        from src.i18n import t
        effect_part = t(" Effect: {effect_desc}", effect_desc=self.effect_desc) if self.effect_desc else ""
        return t("{name} ({attribute}) {grade} {desc}{effect}", 
                 name=self.name, attribute=str(self.attribute), grade=str(self.grade), 
                 desc=self.desc, effect=effect_part)
    
    def get_colored_info(self) -> str:
        """获取带颜色标记的信息，供前端渲染使用"""
        from src.i18n import t
        r, g, b = self.grade.color_rgb
        # 使用与 get_info 相同的格式，但带有颜色标签
        info = t("{name} ({attribute}·{grade})", name=self.name, attribute=str(self.attribute), grade=str(self.grade))
        return f"<color:{r},{g},{b}>{info}</color>"

    def get_structured_info(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "type": "technique",
            "desc": self.desc,
            "grade": str(self.grade),
            "color": self.grade.color_rgb,
            "attribute": str(self.attribute),
            "effect_desc": self.effect_desc,
        }

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


def _load_techniques_data() -> tuple[dict[int, Technique], dict[str, Technique]]:
    """从配表加载 technique 数据
    返回：新的 (techniques_by_id, techniques_by_name)
    """
    new_by_id: dict[int, Technique] = {}
    new_by_name: dict[str, Technique] = {}
    df = game_configs["technique"]
    for row in df:
        attr = TechniqueAttribute(get_str(row, "technique_root"))
        name = get_str(row, "name")
        grade = TechniqueGrade.from_str(get_str(row, "grade", "下品"))
        condition = get_str(row, "condition")
        weight = get_float(row, "weight", 1.0)
        
        sect_id_raw = get_int(row, "sect_id", -1)
        sect_id = sect_id_raw if sect_id_raw > 0 else None
            
        effects = load_effect_from_str(get_str(row, "effects"))
        from src.classes.effect import format_effects_to_text
        effect_desc = format_effects_to_text(effects)

        t = Technique(
            id=get_int(row, "id"),
            name=name,
            attribute=attr,
            grade=grade,
            desc=get_str(row, "desc"),
            weight=weight,
            condition=condition,
            sect_id=sect_id,
            effects=effects,
            effect_desc=effect_desc,
        )
        new_by_id[t.id] = t
        new_by_name[t.name] = t
    return new_by_id, new_by_name


# 全局容器（保持引用不变）
techniques_by_id: dict[int, Technique] = {}
techniques_by_name: dict[str, Technique] = {}

def reload():
    """重新加载数据，保留全局字典引用"""
    new_id, new_name = _load_techniques_data()
    
    techniques_by_id.clear()
    techniques_by_id.update(new_id)
    
    techniques_by_name.clear()
    techniques_by_name.update(new_name)

# 模块初始化时执行一次
reload()


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


def get_random_upper_technique_for_avatar(avatar) -> Technique | None:
    """
    返回一个与 avatar 灵根/阵营/条件相容的上品功法；若无则返回 None。
    仅用于奇遇奖励优先挑选上品功法。
    """
    import random
    candidates: List[Technique] = []
    for t in techniques_by_id.values():
        if t.grade is not TechniqueGrade.UPPER:
            continue
        if not t.is_allowed_for(avatar):
            continue
        if t.attribute == TechniqueAttribute.EVIL and avatar.alignment != Alignment.EVIL:
            continue
        if not is_attribute_compatible_with_root(t.attribute, avatar.root):
            continue
        candidates.append(t)
    if not candidates:
        return None
    weights = [max(0.0, t.weight) for t in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]

def get_technique_by_sect(sect) -> Technique:
    """
    简化版：仅按宗门筛选并按权重抽样，不考虑灵根与 condition。
    - 散修（sect 为 None）：只从无宗门要求（sect_id 为 None）的功法中抽样；
    - 有宗门：从"无宗门 + 该宗门"的功法中抽样；
    若集合为空，则退回全量功法。
    """
    import random

    target_sect_id: Optional[int] = None
    if sect is not None:
        target_sect_id = getattr(sect, "id", None)

    allowed_sect_ids: set[Optional[int]] = {None}
    if target_sect_id is not None:
        allowed_sect_ids.add(target_sect_id)

    def _in_allowed_sect(t: Technique) -> bool:
        return t.sect_id in allowed_sect_ids

    candidates: List[Technique] = [t for t in techniques_by_id.values() if _in_allowed_sect(t)]
    if not candidates:
        candidates = list(techniques_by_id.values())
    weights = [max(0.0, t.weight) for t in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


def get_suppression_bonus(att_attr: TechniqueAttribute, def_attr: TechniqueAttribute) -> float:
    return 0.10 if def_attr in SUPPRESSION.get(att_attr, set()) else 0.0



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
