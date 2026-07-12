from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from src.classes.core.sect import Sect
    from src.classes.core.world import World
    from src.sim.simulator import Simulator


@dataclass(slots=True)
class SaveContext:
    world: "World"
    simulator: "Simulator"
    existed_sects: list["Sect"]
    save_path: Path
    events_db_path: Path
    custom_name: str | None = None
    is_auto_save: bool = False


@dataclass(slots=True)
class LoadContext:
    save_path: Path
    save_data: dict[str, Any]
    world: Any = None
    simulator: Any = None
    existed_sects: list[Any] | None = None
    game_map: Any = None
    all_avatars: dict[str, Any] | None = None
    run_config_snapshot: dict[str, Any] | None = None
    world_data: dict[str, Any] | None = None


class SaveSection(Protocol):
    key: str

    def dump(self, context: SaveContext) -> Any:
        ...


class LoadSection(Protocol):
    key: str

    def load(self, context: LoadContext) -> None:
        ...
