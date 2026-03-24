from __future__ import annotations

from src.classes.core.avatar import Avatar
from src.classes.event import Event
from src.classes.relation.relations import ensure_numeric_relation_state, regress_yearly_friendliness, update_second_degree_relations
from src.systems.time import Month


def phase_process_interactions(avatar_manager, events: list[Event]) -> None:
    # 旧版关系系统使用“按事件累计互动次数”，新版已废弃。
    return


def phase_handle_interactions(
    avatar_manager,
    events: list[Event],
    processed_ids: set[str],
) -> None:
    for event in events:
        processed_ids.add(event.id)
    return


async def phase_evolve_relations(avatar_manager, living_avatars: list[Avatar]) -> list[Event]:
    current_month = int(living_avatars[0].world.month_stamp) if living_avatars else None
    for avatar in living_avatars:
        ensure_numeric_relation_state(avatar, current_month=current_month)
    return []


def phase_update_calculated_relations(world, living_avatars: list[Avatar]) -> None:
    if world.month_stamp.get_month() != Month.JANUARY:
        return

    for avatar in living_avatars:
        regress_yearly_friendliness(avatar, current_month=int(world.month_stamp))
        update_second_degree_relations(avatar)
        ensure_numeric_relation_state(avatar, current_month=int(world.month_stamp))
