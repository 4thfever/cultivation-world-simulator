from __future__ import annotations

from typing import Any

from .consts import EXTRA_INCOME_PER_TILE
from .process import merge_sect_effects


class SectEffectsMixin:
    """
    Sect runtime effect helpers.
    """

    def add_temporary_sect_effect(
        self,
        *,
        effects: dict[str, Any],
        start_month: int,
        duration: int,
        source: str = "sect_random_event",
    ) -> None:
        if not effects:
            return
        if duration <= 0:
            return
        self.temporary_sect_effects.append(
            {
                "source": str(source),
                "effects": dict(effects),
                "start_month": int(start_month),
                "duration": int(duration),
            }
        )

    def cleanup_expired_temporary_sect_effects(self, current_month: int) -> None:
        if not getattr(self, "temporary_sect_effects", None):
            return
        now = int(current_month)
        self.temporary_sect_effects = [
            eff
            for eff in self.temporary_sect_effects
            if now < int(eff.get("start_month", 0)) + int(eff.get("duration", 0))
        ]

    def get_active_temporary_sect_effects(self, current_month: int) -> list[dict[str, Any]]:
        now = int(current_month)
        return [
            eff
            for eff in getattr(self, "temporary_sect_effects", [])
            if now < int(eff.get("start_month", 0)) + int(eff.get("duration", 0))
        ]

    def get_sect_effects(self, current_month: int) -> dict[str, Any]:
        self.cleanup_expired_temporary_sect_effects(current_month)

        merged: dict[str, Any] = dict(getattr(self, "sect_effects", {}) or {})
        for temp in self.get_active_temporary_sect_effects(current_month):
            merged = merge_sect_effects(merged, temp.get("effects", {}) or {})
        return merged

    def get_extra_income_per_tile(self, current_month: int) -> float:
        effects = self.get_sect_effects(current_month)
        raw = effects.get(EXTRA_INCOME_PER_TILE, 0.0)
        try:
            return float(raw)
        except (TypeError, ValueError):
            return 0.0
