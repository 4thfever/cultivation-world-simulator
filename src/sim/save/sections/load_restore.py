from __future__ import annotations

from typing import Any

from .base import LoadContext
from .load_avatars import AvatarsLoadSection
from .load_events import EventsLoadSection
from .load_membership import MembershipLoadSection
from .load_region_runtime import RegionRuntimeLoadSection
from .load_run_config import RunConfigLoadSection
from .load_sect_runtime import SectRuntimeLoadSection
from .load_simulator import SimulatorLoadSection
from .load_world_core import WorldCoreLoadSection


LOAD_SECTIONS = (
    RunConfigLoadSection(),
    WorldCoreLoadSection(),
    SectRuntimeLoadSection(),
    AvatarsLoadSection(),
    RegionRuntimeLoadSection(),
    MembershipLoadSection(),
    EventsLoadSection(),
    SimulatorLoadSection(),
)


def restore_loaded_game(context: LoadContext) -> tuple[Any, Any, list[Any]]:
    for section in LOAD_SECTIONS:
        section.load(context)
    return context.world, context.simulator, context.existed_sects or []
