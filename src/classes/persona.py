import random
from dataclasses import dataclass
from typing import List

from src.utils.df import game_configs
from src.utils.config import CONFIG

ids_separator = CONFIG.df.ids_separator

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
        
        persona = Persona(
            id=int(row["id"]),
            name=str(row["name"]),
            prompt=str(row["prompt"]),
            exclusion_ids=exclusion_ids,
            weight=weight,
        )
        personas_by_id[persona.id] = persona
        personas_by_name[persona.name] = persona
    
    return personas_by_id, personas_by_name

# 从配表加载persona数据
personas_by_id, personas_by_name = _load_personas()

def get_random_compatible_personas(num_personas: int = 2) -> List[Persona]:
    """
    随机选择指定数量的互相不冲突的persona
    
    Args:
        num_personas: 需要选择的persona数量，默认为2
    
    Returns:
        List[Persona]: 互相不冲突的persona列表
        
    Raises:
        ValueError: 如果无法找到足够数量的兼容persona
    """
    all_persona_ids = set(personas_by_id.keys())

    selected_personas: List[Persona] = []
    available_ids = all_persona_ids.copy()
    
    for i in range(num_personas):
        if not available_ids:
            raise ValueError(f"只能找到{i}个兼容的persona，无法满足需要的{num_personas}个")
        # 按权重从可用列表中选择一个
        candidates: List[Persona] = [personas_by_id[i] for i in available_ids]
        weights: List[float] = [max(0.0, c.weight) for c in candidates]
        selected_persona = random.choices(candidates, weights=weights, k=1)[0]
        selected_id = selected_persona.id
        selected_personas.append(selected_persona)
        
        # 更新可用列表：移除已选择的和与其互斥的
        available_ids.discard(selected_id)  # 移除自己
        
        # 移除所有与当前选择互斥的persona
        for exclusion_id in selected_persona.exclusion_ids:
            available_ids.discard(exclusion_id)
        
        # 移除所有将当前选择作为互斥对象的persona
        for persona_id in list(available_ids):
            if selected_id in personas_by_id[persona_id].exclusion_ids:
                available_ids.discard(persona_id)
    
    return selected_personas

