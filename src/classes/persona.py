import random
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

from src.utils.df import game_configs, get_str, get_list_str, get_int
from src.utils.config import CONFIG
from src.classes.effect import load_effect_from_str
from src.classes.rarity import Rarity, get_rarity_from_str

if TYPE_CHECKING:
    # 仅用于类型检查，避免运行时循环导入
    from src.classes.avatar import Avatar

@dataclass
class Persona:
    """
    角色特质
    包含个性、天赋等角色特征
    """
    id: int
    name: str
    desc: str
    exclusion_names: List[str]
    rarity: Rarity
    condition: str
    effects: dict[str, object]
    
    @property
    def weight(self) -> float:
        """根据稀有度获取采样权重"""
        return self.rarity.weight

    def get_info(self) -> str:
        return self.name

    def get_detailed_info(self) -> str:
        return f"{self.name}（{self.desc}）"
    
    def get_colored_info(self) -> str:
        """获取带颜色标记的信息，供前端渲染使用"""
        r, g, b = self.rarity.color_rgb
        return f"<color:{r},{g},{b}>{self.name}</color>"

    def get_structured_info(self) -> dict:
        from src.utils.effect_desc import format_effects_to_text
        return {
            "name": self.name,
            "desc": self.desc,
            "rarity": self.rarity.level.value,
            "color": self.rarity.color_rgb,
            "effect_desc": format_effects_to_text(self.effects),
        }

def _load_personas() -> tuple[dict[int, Persona], dict[str, Persona]]:
    """从配表加载persona数据"""
    personas_by_id: dict[int, Persona] = {}
    personas_by_name: dict[str, Persona] = {}
    
    persona_df = game_configs["persona"]
    for row in persona_df:
        # 解析exclusion_names字符串，转换为字符串列表
        exclusion_names = get_list_str(row, "exclusion_names")
        
        # 解析稀有度（缺失或为 NaN 时默认为 N）
        rarity_str = get_str(row, "rarity", "N").upper()
        rarity = get_rarity_from_str(rarity_str) if rarity_str and rarity_str != "NAN" else get_rarity_from_str("N")
        
        # 条件
        condition = get_str(row, "condition")
        
        # 解析effects
        effects = load_effect_from_str(get_str(row, "effects"))
        
        persona = Persona(
            id=get_int(row, "id"),
            name=get_str(row, "name"),
            desc=get_str(row, "desc"),
            exclusion_names=exclusion_names,
            rarity=rarity,
            condition=condition,
            effects=effects,
        )
        personas_by_id[persona.id] = persona
        personas_by_name[persona.name] = persona
    
    return personas_by_id, personas_by_name

# 从配表加载persona数据
personas_by_id, personas_by_name = _load_personas()

def _is_persona_allowed(persona_id: int, already_selected_ids: set[int], avatar: Optional["Avatar"]) -> bool:
    """
    统一判断：persona 是否允许被选择（条件 + 互斥）。
    - 条件：当存在 avatar 且配置了 condition 时，通过安全 eval 判断。
    - 互斥：与已选 persona 双向互斥（通过名字比较）。
    """
    persona = personas_by_id[persona_id]
    # 条件判定
    if avatar is not None and persona.condition:
        allowed = bool(eval(persona.condition, {"__builtins__": {}}, {"avatar": avatar}))
        if not allowed:
            return False
    # 与已选互斥检查（双向，通过名字）
    for sid in already_selected_ids:
        other = personas_by_id[sid]
        # 检查当前persona是否在对方的互斥列表中，或对方是否在当前persona的互斥列表中
        if (persona.name in other.exclusion_names) or (other.name in persona.exclusion_names):
            return False
    return True

def get_random_compatible_personas(num_personas: int = 2, avatar: Optional["Avatar"] = None) -> List[Persona]:
    """
    随机选择指定数量的互相不冲突的persona
    
    Args:
        num_personas: 需要选择的persona数量，默认为2
        avatar: 可选，若提供则按 persona.condition 过滤
    
    Returns:
        List[Persona]: 互相不冲突的persona列表
        
    Raises:
        ValueError: 如果无法找到足够数量的兼容persona
    """
    # 初始候选：若提供 avatar，则先按条件过滤；否则全量
    initial_ids = set(personas_by_id.keys())
    if avatar is not None:
        initial_ids = {pid for pid in initial_ids if _is_persona_allowed(pid, set(), avatar)}

    selected_personas: List[Persona] = []
    selected_ids: set[int] = set()

    for i in range(num_personas):
        # 按当前已选进行二次过滤（互斥 + 条件）
        available_ids = [pid for pid in initial_ids if pid not in selected_ids and _is_persona_allowed(pid, selected_ids, avatar)]
        if not available_ids:
            raise ValueError(f"只能找到{i}个兼容的persona，无法满足需要的{num_personas}个")

        candidates: List[Persona] = [personas_by_id[pid] for pid in available_ids]
        weights: List[float] = [max(0.0, c.weight) for c in candidates]
        selected_persona = random.choices(candidates, weights=weights, k=1)[0]
        selected_personas.append(selected_persona)
        selected_ids.add(selected_persona.id)

    return selected_personas
