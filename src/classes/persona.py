from dataclasses import dataclass

from src.utils.df import game_configs

@dataclass
class Persona:
    """
    角色个性
    """
    id: int
    name: str
    prompt: str 

def _load_personas() -> tuple[dict[int, Persona], dict[str, Persona]]:
    """从配表加载persona数据"""
    personas_by_id: dict[int, Persona] = {}
    personas_by_name: dict[str, Persona] = {}
    
    persona_df = game_configs["persona"]
    for _, row in persona_df.iterrows():
        persona = Persona(
            id=int(row["id"]),
            name=str(row["name"]),
            prompt=str(row["prompt"])
        )
        personas_by_id[persona.id] = persona
        personas_by_name[persona.name] = persona
    
    return personas_by_id, personas_by_name

# 从配表加载persona数据
personas_by_id, personas_by_name = _load_personas()




