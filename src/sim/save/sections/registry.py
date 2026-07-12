from __future__ import annotations

from typing import Any

from .base import SaveContext
from .load_restore import restore_loaded_game
from .save_sections import (
    AvatarsSection,
    CustomContentSection,
    EventsSection,
    MetaSection,
    RunConfigSection,
    SimulatorSection,
    WorldSection,
)


SAVE_SECTIONS = (
    MetaSection(),
    RunConfigSection(),
    CustomContentSection(),
    WorldSection(),
    AvatarsSection(),
    EventsSection(),
    SimulatorSection(),
)


def dump_save_data(context: SaveContext) -> dict[str, Any]:
    return {section.key: section.dump(context) for section in SAVE_SECTIONS}
