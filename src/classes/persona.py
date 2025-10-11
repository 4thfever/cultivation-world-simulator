import random
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

from src.utils.df import game_configs
from src.utils.config import CONFIG

ids_separator = CONFIG.df.ids_separator

if TYPE_CHECKING:
    # 仅用于类型检查，避免运行时循环导入
    from src.classes.avatar import Avatar

@dataclass
class Persona:
    """
    角色个性
    """
    id: int
    name: str
    prompt: str
    exclusion_ids: List[int]
    weight: float
    condition: str

    def get_info(self) -> str:
        return self.name

    def get_detailed_info(self) -> str:
        return f"{self.name}（{self.prompt}）"

def _load_personas() -> tuple[dict[int, Persona], dict[str, Persona]]:
    """从配表加载persona数据"""
    personas_by_id: dict[int, Persona] = {}
    personas_by_name: dict[str, Persona] = {}
    
    persona_df = game_configs["persona"]
    for _, row in persona_df.iterrows():
        # 解析exclusion_ids字符串，转换为int列表
        exclusion_ids_str = str(row["exclusion_ids"]) if str(row["exclusion_ids"]) != "nan" else ""
        exclusion_ids = []
        if exclusion_ids_str:
            exclusion_ids = [int(x.strip()) for x in exclusion_ids_str.split(ids_separator) if x.strip()]
        # 解析权重（缺失或为 NaN 时默认为 1.0），避免不必要的异常
        weight_val = row.get("weight", 1)
        weight_str = str(weight_val).strip()
        weight = float(weight_str) if weight_str and weight_str.lower() != "nan" else 1.0
        # 条件：可为空
        condition_val = row.get("condition", "")
        condition = "" if str(condition_val) == "nan" else str(condition_val).strip()
        
        persona = Persona(
            id=int(row["id"]),
            name=str(row["name"]),
            prompt=str(row["prompt"]),
            exclusion_ids=exclusion_ids,
            weight=weight,
            condition=condition,
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
    - 互斥：与已选 persona 双向互斥。
    """
    persona = personas_by_id[persona_id]
    # 条件判定
    if avatar is not None and persona.condition:
        allowed = bool(eval(persona.condition, {"__builtins__": {}}, {"avatar": avatar}))
        if not allowed:
            return False
    # 与已选互斥检查（双向）
    for sid in already_selected_ids:
        other = personas_by_id[sid]
        if (persona_id in other.exclusion_ids) or (sid in persona.exclusion_ids):
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

