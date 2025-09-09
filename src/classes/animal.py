from dataclasses import dataclass

from src.utils.df import game_configs

@dataclass
class Animal:
    """
    动物
    """
    id: int
    name: str
    desc: str
    grade: int

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return self.name

def _load_animals() -> tuple[dict[int, Animal], dict[str, Animal]]:
    """从配表加载animal数据"""
    animals_by_id: dict[int, Animal] = {}
    animals_by_name: dict[str, Animal] = {}
    
    animal_df = game_configs["animal"]
    for _, row in animal_df.iterrows():
        animal = Animal(
            id=int(row["id"]),
            name=str(row["name"]),
            desc=str(row["desc"]),
            grade=int(row["grade"])
        )
        animals_by_id[animal.id] = animal
        animals_by_name[animal.name] = animal
    
    return animals_by_id, animals_by_name

# 从配表加载animal数据
animals_by_id, animals_by_name = _load_animals()
