import random
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from src.utils.df import game_configs
from src.classes.effect import load_effect_from_str

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


@dataclass
class Trait:
    """
    角色特质
    每个角色有且仅有一个特质（可能是占位特质"无"）
    """
    id: int
    name: str
    desc: str
    weight: float
    condition: str
    effects: dict[str, object]

    def get_info(self) -> str:
        return self.name

    def get_detailed_info(self) -> str:
        return f"{self.name}（{self.desc}）"


def _load_traits() -> tuple[dict[int, Trait], dict[str, Trait]]:
    """从配表加载trait数据"""
    traits_by_id: dict[int, Trait] = {}
    traits_by_name: dict[str, Trait] = {}
    
    trait_df = game_configs["trait"]
    for _, row in trait_df.iterrows():
        # 解析权重（缺失或为 NaN 时默认为 1.0）
        weight_val = row.get("weight", 1)
        weight_str = str(weight_val).strip()
        weight = float(weight_str) if weight_str and weight_str.lower() != "nan" else 1.0
        
        # 条件：可为空
        condition_val = row.get("condition", "")
        condition = "" if str(condition_val) == "nan" else str(condition_val).strip()
        
        # 解析effects
        raw_effects_val = row.get("effects", "")
        effects = load_effect_from_str(raw_effects_val)
        
        trait = Trait(
            id=int(row["id"]),
            name=str(row["name"]),
            desc=str(row["desc"]),
            weight=weight,
            condition=condition,
            effects=effects,
        )
        traits_by_id[trait.id] = trait
        traits_by_name[trait.name] = trait
    
    return traits_by_id, traits_by_name


# 从配表加载trait数据
traits_by_id, traits_by_name = _load_traits()


def _is_trait_allowed(trait_id: int, avatar: Optional["Avatar"]) -> bool:
    """
    判断特质是否允许被选择（条件判定）
    """
    trait = traits_by_id[trait_id]
    # 条件判定
    if avatar is not None and trait.condition:
        allowed = bool(eval(trait.condition, {"__builtins__": {}}, {"avatar": avatar}))
        if not allowed:
            return False
    return True


def get_random_trait(avatar: Optional["Avatar"] = None) -> Trait:
    """
    根据权重随机选择一个特质
    
    Args:
        avatar: 可选，若提供则按 trait.condition 过滤
    
    Returns:
        Trait: 选中的特质
    """
    # 初始候选：若提供 avatar，则先按条件过滤；否则全量
    available_ids = list(traits_by_id.keys())
    if avatar is not None:
        available_ids = [tid for tid in available_ids if _is_trait_allowed(tid, avatar)]
    
    if not available_ids:
        # 如果没有可用的特质，返回第一个（通常是"无"）
        return list(traits_by_id.values())[0]
    
    candidates = [traits_by_id[tid] for tid in available_ids]
    weights = [max(0.0, c.weight) for c in candidates]
    
    return random.choices(candidates, weights=weights, k=1)[0]

