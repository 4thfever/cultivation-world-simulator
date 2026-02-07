import random
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

from src.utils.df import game_configs, get_str, get_list_str, get_int
from src.utils.config import CONFIG
from src.classes.effect import load_effect_from_str
from src.classes.rarity import Rarity, get_rarity_from_str

if TYPE_CHECKING:
    # 仅用于类型检查，避免运行时循环导入
    from src.classes.core.avatar import Avatar

@dataclass
class Persona:
    """
    角色特质
    包含个性、天赋等角色特征
    """
    id: int
    key: str
    name: str
    desc: str
    exclusion_keys: List[str]
    rarity: Rarity
    condition: str
    effects: dict[str, object]
    effect_desc: str = ""
    
    @property
    def weight(self) -> float:
        """根据稀有度获取采样权重"""
        return self.rarity.weight

    def get_info(self) -> str:
        return self.name

    def get_detailed_info(self) -> str:
        from src.i18n import t
        desc_part = t(" ({desc})", desc=self.desc) if self.desc else ""
        effect_part = t("\nEffect: {effect_desc}", effect_desc=self.effect_desc) if self.effect_desc else ""
        return f"{self.name}{desc_part}{effect_part}"
    
    def get_colored_info(self) -> str:
        """获取带颜色标记的信息，供前端渲染使用"""
        r, g, b = self.rarity.color_rgb
        return f"<color:{r},{g},{b}>{self.name}</color>"

    def get_structured_info(self) -> dict:
        return {
            "name": self.name,
            "desc": self.desc,
            "key": self.key,
            "rarity": self.rarity.level.value,
            "color": self.rarity.color_rgb,
            "effect_desc": self.effect_desc,
        }

def _load_personas() -> tuple[dict[int, Persona], dict[str, Persona]]:
    """从配表加载persona数据"""
    personas_by_id: dict[int, Persona] = {}
    personas_by_name: dict[str, Persona] = {}
    
    persona_df = game_configs["persona"]
    for row in persona_df:
        # 解析exclusion_keys字符串，转换为字符串列表
        exclusion_keys = get_list_str(row, "exclusion_keys")
        
        # 解析稀有度
        rarity_str = get_str(row, "rarity", "N").upper()
        rarity = get_rarity_from_str(rarity_str)
        
        # 解析effects
        effects = load_effect_from_str(get_str(row, "effects"))
        from src.classes.effect import format_effects_to_text
        effect_desc = format_effects_to_text(effects)
        
        persona = Persona(
            id=get_int(row, "id"),
            key=get_str(row, "key").upper(),
            name=get_str(row, "name"),
            desc=get_str(row, "desc"),
            exclusion_keys=exclusion_keys,
            rarity=rarity,
            condition=get_str(row, "condition"),
            effects=effects,
            effect_desc=effect_desc,
        )
        personas_by_id[persona.id] = persona
        personas_by_name[persona.name] = persona
    
    return personas_by_id, personas_by_name

# 从配表加载persona数据
personas_by_id: dict[int, Persona] = {}
personas_by_name: dict[str, Persona] = {}

def reload():
    """重新加载数据，保留全局字典引用"""
    new_id, new_name = _load_personas()
    
    personas_by_id.clear()
    personas_by_id.update(new_id)
    
    personas_by_name.clear()
    personas_by_name.update(new_name)

# 模块初始化时执行一次
reload()

def _is_persona_allowed(persona_id: int, already_selected_ids: set[int], avatar: Optional["Avatar"]) -> bool:
    """
    统一判断：persona 是否允许被选择（条件 + 互斥）。
    """
    persona = personas_by_id[persona_id]
    # 条件判定
    if avatar is not None and persona.condition:
        allowed = bool(eval(persona.condition, {"__builtins__": {}}, {"avatar": avatar}))
        if not allowed:
            return False
    # 与已选互斥检查（双向，通过 Key）
    for sid in already_selected_ids:
        other = personas_by_id[sid]
        if (persona.key in other.exclusion_keys) or (other.key in persona.exclusion_keys):
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
