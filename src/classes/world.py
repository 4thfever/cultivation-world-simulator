from dataclasses import dataclass

from src.classes.tile import Map

@dataclass
class World():
    map: Map