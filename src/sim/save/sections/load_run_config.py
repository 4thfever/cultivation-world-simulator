from __future__ import annotations

from src.config import get_settings_service

from .base import LoadContext
from .save_sections import _model_to_dict


class RunConfigLoadSection:
    key = "run_config"

    def load(self, context: LoadContext) -> None:
        context.run_config_snapshot = context.save_data.get(
            "run_config",
            _model_to_dict(get_settings_service().get_default_run_config()),
        )
        context.world_data = context.save_data.get("world", {})
