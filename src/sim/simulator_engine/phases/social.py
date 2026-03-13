from __future__ import annotations

from src.classes.core.avatar import Avatar
from src.classes.event import Event
from src.classes.relation.relation_resolver import RelationResolver
from src.classes.relation.relations import update_second_degree_relations
from src.systems.time import Month
from src.utils.config import CONFIG


def phase_process_interactions(avatar_manager, events: list[Event]) -> None:
    # 只有明确关联 2 个及以上角色的事件，才会被视为“互动事件”。
    for event in events:
        if not event.related_avatars or len(event.related_avatars) < 2:
            continue

        for avatar_id in event.related_avatars:
            avatar = avatar_manager.get_avatar(avatar_id)
            if avatar:
                avatar.process_interaction_from_event(event)


def phase_handle_interactions(
    avatar_manager,
    events: list[Event],
    processed_ids: set[str],
) -> None:
    # 这里做的是“增量分发”：
    # step() 里会调用两次，但每个事件只会处理一次，避免重复累计互动计数。
    new_interactions: list[Event] = []
    for event in events:
        if event.id in processed_ids:
            continue

        if event.related_avatars and len(event.related_avatars) >= 2:
            new_interactions.append(event)
        processed_ids.add(event.id)

    if new_interactions:
        phase_process_interactions(avatar_manager, new_interactions)


async def phase_evolve_relations(avatar_manager, living_avatars: list[Avatar]) -> list[Event]:
    # 关系演化不是对每次互动都立即判定，而是先累计互动计数，
    # 达到阈值后再按角色对批量决议一次。
    pairs_to_resolve: list[tuple[Avatar, Avatar]] = []
    processed_pairs: set[tuple[str, str]] = set()

    for avatar in living_avatars:
        target_ids = list(avatar.relation_interaction_states.keys())

        for target_id in target_ids:
            state = avatar.relation_interaction_states[target_id]
            target = avatar_manager.get_avatar(target_id)

            if target is None or target.is_dead:
                continue

            if state["count"] < CONFIG.social.relation_check_threshold:
                continue

            id1, id2 = sorted([str(avatar.id), str(target.id)])
            pair_key = (id1, id2)
            if pair_key in processed_pairs:
                continue

            processed_pairs.add(pair_key)
            pairs_to_resolve.append((avatar, target))

            # 一旦进入本轮判定，就同时重置双方计数，
            # 避免短时间内因为双向状态重复触发。
            state["count"] = 0
            state["checked_times"] += 1

            target_state = target.relation_interaction_states[str(avatar.id)]
            target_state["count"] = 0
            target_state["checked_times"] += 1

    if not pairs_to_resolve:
        return []

    relation_events = await RelationResolver.run_batch(pairs_to_resolve)
    return relation_events or []


def phase_update_calculated_relations(world, living_avatars: list[Avatar]) -> None:
    # 二阶关系这类“计算型关系”成本较高，只在每年一月集中刷新一次。
    if world.month_stamp.get_month() != Month.JANUARY:
        return

    for avatar in living_avatars:
        update_second_degree_relations(avatar)
