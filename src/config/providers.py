from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True, slots=True)
class StaticConfigProvider:
    get_config: Callable[[], Any]

    @classmethod
    def current(cls) -> "StaticConfigProvider":
        def _get_config():
            from src.utils.config import CONFIG

            return CONFIG

        return cls(get_config=_get_config)

    @property
    def config(self) -> Any:
        return self.get_config()

    @property
    def templates_path(self):
        return self.config.paths.templates

    def max_action_rounds_per_turn(self) -> int:
        return int(self.config.world.max_action_rounds_per_turn)

    def can_interrupt_major_events(self) -> bool:
        return bool(getattr(self.config.world, "can_interrupt_major_events", False))


@dataclass(frozen=True, slots=True)
class RuntimeConfigProvider:
    get_service: Callable[[], Any] | None = None

    def auto_save_enabled(self) -> bool:
        if self.get_service is None:
            from src.config import get_settings_service

            service = get_settings_service()
        else:
            service = self.get_service()
        return bool(service.get_settings().simulation.auto_save_enabled)


@dataclass(frozen=True, slots=True)
class RunConfigProvider:
    world: Any

    def get(self, key: str, default: Any = None) -> Any:
        snapshot = getattr(self.world, "run_config_snapshot", {}) or {}
        return snapshot.get(key, default)
