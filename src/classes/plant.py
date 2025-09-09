from dataclasses import dataclass

from src.utils.df import game_configs

@dataclass
class Plant:
    """
    植物
    """
    id: int
    name: str
    desc: str
    grade: int

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return self.name

def _load_plants() -> tuple[dict[int, Plant], dict[str, Plant]]:
    """从配表加载plant数据"""
    plants_by_id: dict[int, Plant] = {}
    plants_by_name: dict[str, Plant] = {}
    
    plant_df = game_configs["plant"]
    for _, row in plant_df.iterrows():
        plant = Plant(
            id=int(row["id"]),
            name=str(row["name"]),
            desc=str(row["desc"]),
            grade=int(row["grade"])
        )
        plants_by_id[plant.id] = plant
        plants_by_name[plant.name] = plant
    
    return plants_by_id, plants_by_name

# 从配表加载plant数据
plants_by_id, plants_by_name = _load_plants()
