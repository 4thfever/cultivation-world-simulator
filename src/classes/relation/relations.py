"""
两个角色之间的关系操作函数
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List

from src.classes.relation.relation import (
    BLOOD_RELATIONS,
    IDENTITY_RELATIONS,
    NumericRelation,
    Relation,
    RelationState,
    get_reciprocal,
    is_innate,
)
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


def _ensure_relations_dict(avatar: "Avatar") -> dict:
    relations = getattr(avatar, "relations", None)
    if isinstance(relations, dict):
        return relations
    relations = {}
    setattr(avatar, "relations", relations)
    return relations


def _ensure_archived_relations_dict(avatar: "Avatar") -> dict:
    relations = getattr(avatar, "archived_relations", None)
    if isinstance(relations, dict):
        return relations
    relations = {}
    setattr(avatar, "archived_relations", relations)
    return relations


def _normalize_numeric_relation(value: NumericRelation | object) -> NumericRelation:
    return value if isinstance(value, NumericRelation) else NumericRelation.STRANGER


def _normalize_month(value: int | object | None) -> int | None:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return None


def _get_or_create_state(from_avatar: "Avatar", to_avatar: "Avatar") -> RelationState:
    relations = _ensure_relations_dict(from_avatar)
    state = relations.get(to_avatar)
    if not isinstance(state, RelationState):
        state = RelationState()
        relations[to_avatar] = state
    return state


def _copy_state_to_archive(from_avatar: "Avatar", to_avatar: "Avatar", state: RelationState | None) -> None:
    if state is None:
        return
    archived_relations = _ensure_archived_relations_dict(from_avatar)
    archived_relations[to_avatar] = state.copy()


def clamp_friendliness(value: int) -> int:
    min_value = int(getattr(CONFIG.social.relation, "min_friendliness", -100))
    max_value = int(getattr(CONFIG.social.relation, "max_friendliness", 100))
    return max(min_value, min(max_value, int(value)))


def get_numeric_relation_thresholds() -> dict[NumericRelation, int]:
    thresholds = getattr(CONFIG.social.relation, "thresholds", None)
    return {
        NumericRelation.ARCHENEMY: int(getattr(thresholds, "archenemy", -60)),
        NumericRelation.DISLIKED: int(getattr(thresholds, "disliked", -25)),
        NumericRelation.FRIEND: int(getattr(thresholds, "friend", 25)),
        NumericRelation.BEST_FRIEND: int(getattr(thresholds, "best_friend", 60)),
    }


def infer_numeric_relation_from_friendliness(friendliness: int) -> NumericRelation:
    thresholds = get_numeric_relation_thresholds()
    if friendliness <= thresholds[NumericRelation.ARCHENEMY]:
        return NumericRelation.ARCHENEMY
    if friendliness <= thresholds[NumericRelation.DISLIKED]:
        return NumericRelation.DISLIKED
    if friendliness >= thresholds[NumericRelation.BEST_FRIEND]:
        return NumericRelation.BEST_FRIEND
    if friendliness >= thresholds[NumericRelation.FRIEND]:
        return NumericRelation.FRIEND
    return NumericRelation.STRANGER


def _numeric_relation_bounds() -> dict[NumericRelation, tuple[int | None, int | None]]:
    thresholds = get_numeric_relation_thresholds()
    return {
        NumericRelation.ARCHENEMY: (None, thresholds[NumericRelation.ARCHENEMY]),
        NumericRelation.DISLIKED: (thresholds[NumericRelation.ARCHENEMY] + 1, thresholds[NumericRelation.DISLIKED]),
        NumericRelation.STRANGER: (thresholds[NumericRelation.DISLIKED] + 1, thresholds[NumericRelation.FRIEND] - 1),
        NumericRelation.FRIEND: (thresholds[NumericRelation.FRIEND], thresholds[NumericRelation.BEST_FRIEND] - 1),
        NumericRelation.BEST_FRIEND: (thresholds[NumericRelation.BEST_FRIEND], None),
    }


def update_numeric_relation(state: RelationState, current_month: int | None = None) -> NumericRelation:
    state.last_numeric_relation = _normalize_numeric_relation(state.last_numeric_relation)
    state.last_numeric_relation_change_month = _normalize_month(state.last_numeric_relation_change_month)
    current_month = _normalize_month(current_month)
    target_relation = infer_numeric_relation_from_friendliness(state.friendliness)
    prev_relation = state.last_numeric_relation
    if target_relation == prev_relation:
        return prev_relation

    hysteresis = int(getattr(CONFIG.social.relation, "transition_hysteresis", 10))
    cooldown_months = int(getattr(CONFIG.social.relation, "transition_cooldown_months", 12))

    if current_month is not None and state.last_numeric_relation_change_month is not None:
        if current_month - state.last_numeric_relation_change_month < cooldown_months:
            return prev_relation

    bounds = _numeric_relation_bounds()[prev_relation]
    lower_bound, upper_bound = bounds
    order = {
        NumericRelation.ARCHENEMY: 0,
        NumericRelation.DISLIKED: 1,
        NumericRelation.STRANGER: 2,
        NumericRelation.FRIEND: 3,
        NumericRelation.BEST_FRIEND: 4,
    }
    if lower_bound is not None and state.friendliness >= lower_bound - hysteresis and order[target_relation] < order[prev_relation]:
        return prev_relation
    if upper_bound is not None and state.friendliness <= upper_bound + hysteresis and order[target_relation] > order[prev_relation]:
        return prev_relation

    state.last_numeric_relation = target_relation
    state.last_numeric_relation_change_month = current_month
    return target_relation


def ensure_numeric_relation_state(avatar: "Avatar", current_month: int | None = None) -> None:
    for state in _ensure_relations_dict(avatar).values():
        if not isinstance(state, RelationState):
            continue
        update_numeric_relation(state, current_month=current_month)


def update_second_degree_relations(avatar: "Avatar") -> None:
    computed = {}
    relations = getattr(avatar, "relations", {})

    parents = [t for t, s in relations.items() if s.blood_relation == Relation.IS_PARENT_OF]
    children = [t for t, s in relations.items() if s.blood_relation == Relation.IS_CHILD_OF]
    masters = [t for t, s in relations.items() if Relation.IS_MASTER_OF in s.identity_relations]
    apprentices = [t for t, s in relations.items() if Relation.IS_DISCIPLE_OF in s.identity_relations]

    for p in parents:
        p_relations = getattr(p, "relations", {})
        for sib, state in p_relations.items():
            if state.blood_relation == Relation.IS_CHILD_OF and sib.id != avatar.id:
                computed[sib] = Relation.IS_SIBLING_OF

    for p in parents:
        p_relations = getattr(p, "relations", {})
        for gp, state in p_relations.items():
            if state.blood_relation == Relation.IS_PARENT_OF:
                computed[gp] = Relation.IS_GRAND_PARENT_OF

    for c in children:
        c_relations = getattr(c, "relations", {})
        for gc, state in c_relations.items():
            if state.blood_relation == Relation.IS_CHILD_OF:
                computed[gc] = Relation.IS_GRAND_CHILD_OF

    for m in masters:
        m_relations = getattr(m, "relations", {})
        for fellow, state in m_relations.items():
            if Relation.IS_DISCIPLE_OF in state.identity_relations and fellow.id != avatar.id:
                computed[fellow] = Relation.IS_MARTIAL_SIBLING_OF

    for m in masters:
        m_relations = getattr(m, "relations", {})
        for mgm, state in m_relations.items():
            if Relation.IS_MASTER_OF in state.identity_relations:
                computed[mgm] = Relation.IS_MARTIAL_GRANDMASTER_OF

    for app in apprentices:
        app_relations = getattr(app, "relations", {})
        for mgc, state in app_relations.items():
            if Relation.IS_DISCIPLE_OF in state.identity_relations:
                computed[mgc] = Relation.IS_MARTIAL_GRANDCHILD_OF

    avatar.computed_relations = computed


def get_possible_new_relations(from_avatar: "Avatar", to_avatar: "Avatar") -> List[Relation]:
    existing_relation = get_relation(to_avatar, from_avatar)
    candidates: list[Relation] = []
    level_from = from_avatar.cultivation_progress.level
    level_to = to_avatar.cultivation_progress.level

    if existing_relation != Relation.IS_FRIEND_OF:
        candidates.append(Relation.IS_FRIEND_OF)
    if existing_relation != Relation.IS_ENEMY_OF:
        candidates.append(Relation.IS_ENEMY_OF)
    if from_avatar.gender != to_avatar.gender and not has_identity_relation(to_avatar, from_avatar, Relation.IS_LOVER_OF):
        candidates.append(Relation.IS_LOVER_OF)
    if not has_identity_relation(to_avatar, from_avatar, Relation.IS_SWORN_SIBLING_OF):
        candidates.append(Relation.IS_SWORN_SIBLING_OF)
    if level_to >= level_from + 20 and not has_identity_relation(to_avatar, from_avatar, Relation.IS_MASTER_OF):
        candidates.append(Relation.IS_MASTER_OF)
    if level_to <= level_from - 20 and not has_identity_relation(to_avatar, from_avatar, Relation.IS_DISCIPLE_OF):
        candidates.append(Relation.IS_DISCIPLE_OF)
    return candidates


def set_relation(from_avatar: "Avatar", to_avatar: "Avatar", relation: Relation) -> None:
    if to_avatar is from_avatar:
        return

    if relation == Relation.IS_FRIEND_OF:
        set_friendliness(from_avatar, to_avatar, 35, current_month=int(from_avatar.world.month_stamp))
        set_friendliness(to_avatar, from_avatar, 35, current_month=int(from_avatar.world.month_stamp))
        return
    if relation == Relation.IS_ENEMY_OF:
        set_friendliness(from_avatar, to_avatar, -70, current_month=int(from_avatar.world.month_stamp))
        set_friendliness(to_avatar, from_avatar, -70, current_month=int(from_avatar.world.month_stamp))
        return

    from_state = _get_or_create_state(from_avatar, to_avatar)
    to_state = _get_or_create_state(to_avatar, from_avatar)

    if relation in BLOOD_RELATIONS:
        from_state.blood_relation = relation
        to_state.blood_relation = get_reciprocal(relation)
    elif relation in IDENTITY_RELATIONS:
        from_state.set_identity(relation)
        to_state.set_identity(get_reciprocal(relation))
    else:
        from_state.set_identity(relation)
        to_state.set_identity(get_reciprocal(relation))

    if relation == Relation.IS_LOVER_OF:
        current_time = int(from_avatar.world.month_stamp)
        from_avatar.relation_start_dates[to_avatar.id] = current_time
        to_avatar.relation_start_dates[from_avatar.id] = current_time

    if relation == Relation.IS_MASTER_OF:
        if to_avatar.sect is not None and from_avatar.sect != to_avatar.sect:
            from src.classes.sect_ranks import get_rank_from_realm

            from_avatar.join_sect(to_avatar.sect, get_rank_from_realm(from_avatar.cultivation_progress.realm))
    elif relation == Relation.IS_DISCIPLE_OF:
        if from_avatar.sect is not None and to_avatar.sect != from_avatar.sect:
            from src.classes.sect_ranks import get_rank_from_realm

            to_avatar.join_sect(from_avatar.sect, get_rank_from_realm(to_avatar.cultivation_progress.realm))


def get_state(from_avatar: "Avatar", to_avatar: "Avatar") -> RelationState | None:
    state = _ensure_relations_dict(from_avatar).get(to_avatar)
    return state if isinstance(state, RelationState) else None


def get_relation(from_avatar: "Avatar", to_avatar: "Avatar") -> Relation | None:
    state = get_state(from_avatar, to_avatar)
    if state is None:
        return None
    if state.blood_relation is not None:
        return state.blood_relation
    if state.identity_relations:
        return sorted(state.identity_relations, key=lambda item: item.value)[0]
    numeric_relation = update_numeric_relation(state)
    if numeric_relation == NumericRelation.FRIEND:
        return Relation.IS_FRIEND_OF
    if numeric_relation == NumericRelation.ARCHENEMY:
        return Relation.IS_ENEMY_OF
    return None


def has_identity_relation(from_avatar: "Avatar", to_avatar: "Avatar", relation: Relation) -> bool:
    state = get_state(from_avatar, to_avatar)
    return state is not None and relation in state.identity_relations


def get_friendliness(from_avatar: "Avatar", to_avatar: "Avatar") -> int:
    state = get_state(from_avatar, to_avatar)
    return 0 if state is None else int(state.friendliness)


def get_numeric_relation(from_avatar: "Avatar", to_avatar: "Avatar") -> NumericRelation:
    state = get_state(from_avatar, to_avatar)
    if state is None:
        return NumericRelation.STRANGER
    return update_numeric_relation(state)


def set_friendliness(from_avatar: "Avatar", to_avatar: "Avatar", value: int, *, current_month: int | None = None) -> int:
    state = _get_or_create_state(from_avatar, to_avatar)
    state.friendliness = clamp_friendliness(value)
    _apply_identity_friendliness_floor(state)
    update_numeric_relation(state, current_month=current_month)
    return state.friendliness


def add_friendliness(from_avatar: "Avatar", to_avatar: "Avatar", delta: int, *, current_month: int | None = None) -> int:
    state = _get_or_create_state(from_avatar, to_avatar)
    state.friendliness = clamp_friendliness(state.friendliness + int(delta))
    _apply_identity_friendliness_floor(state)
    update_numeric_relation(state, current_month=current_month)
    return state.friendliness


def _apply_identity_friendliness_floor(state: RelationState) -> None:
    if Relation.IS_LOVER_OF in state.identity_relations:
        state.friendliness = max(state.friendliness, int(getattr(CONFIG.social.relation.identity_friendliness_floor, "lovers", 30)))
    if Relation.IS_SWORN_SIBLING_OF in state.identity_relations:
        state.friendliness = max(state.friendliness, int(getattr(CONFIG.social.relation.identity_friendliness_floor, "sworn_sibling", 20)))
    if Relation.IS_MASTER_OF in state.identity_relations or Relation.IS_DISCIPLE_OF in state.identity_relations:
        state.friendliness = max(state.friendliness, int(getattr(CONFIG.social.relation.identity_friendliness_floor, "master_apprentice", 10)))


def clear_relation(from_avatar: "Avatar", to_avatar: "Avatar") -> None:
    from_avatar.relations.pop(to_avatar, None)
    to_avatar.relations.pop(from_avatar, None)
    getattr(from_avatar, "archived_relations", {}).pop(to_avatar, None)
    getattr(to_avatar, "archived_relations", {}).pop(from_avatar, None)
    from_avatar.relation_start_dates.pop(to_avatar.id, None)
    to_avatar.relation_start_dates.pop(from_avatar.id, None)


def clear_friendliness(from_avatar: "Avatar", to_avatar: "Avatar", *, keep_structural_relations: bool = True) -> None:
    state = _ensure_relations_dict(from_avatar).get(to_avatar)
    if state is None:
        return
    state.friendliness = 0
    state.last_numeric_relation = NumericRelation.STRANGER
    state.last_numeric_relation_change_month = None
    if not keep_structural_relations and state.blood_relation is None and not state.identity_relations:
        from_avatar.relations.pop(to_avatar, None)


def iter_live_relation_items(avatar: "Avatar") -> list[tuple["Avatar", RelationState]]:
    return list((_ensure_relations_dict(avatar) or {}).items())


def iter_archived_relation_items(avatar: "Avatar") -> list[tuple["Avatar", RelationState]]:
    return list((_ensure_archived_relations_dict(avatar) or {}).items())


def iter_display_relation_items(avatar: "Avatar") -> list[tuple["Avatar", RelationState]]:
    merged: dict["Avatar", RelationState] = {}
    for other, state in iter_archived_relation_items(avatar):
        merged[other] = state
    for other, state in iter_live_relation_items(avatar):
        merged[other] = state
    return list(merged.items())


def iter_display_relation_entries(avatar: "Avatar") -> list[tuple["Avatar", RelationState, str]]:
    entries: list[tuple["Avatar", RelationState, str]] = []
    live_targets = {other for other, _ in iter_live_relation_items(avatar)}
    for other, state in iter_archived_relation_items(avatar):
        if other in live_targets:
            continue
        entries.append((other, state, "archived"))
    for other, state in iter_live_relation_items(avatar):
        entries.append((other, state, "active"))
    return entries


def get_live_related_avatars(
    avatar: "Avatar",
    *,
    identity_relation: Relation | None = None,
    numeric_relation: NumericRelation | None = None,
) -> list["Avatar"]:
    candidates: list["Avatar"] = []
    for other, state in iter_live_relation_items(avatar):
        if identity_relation is not None and identity_relation not in state.identity_relations:
            continue
        if numeric_relation is not None and state.last_numeric_relation != numeric_relation:
            continue
        candidates.append(other)
    return candidates


def archive_relation_pair(from_avatar: "Avatar", to_avatar: "Avatar") -> None:
    from_state = get_state(from_avatar, to_avatar)
    to_state = get_state(to_avatar, from_avatar)
    _copy_state_to_archive(from_avatar, to_avatar, from_state)
    _copy_state_to_archive(to_avatar, from_avatar, to_state)
    from_avatar.relations.pop(to_avatar, None)
    to_avatar.relations.pop(from_avatar, None)
    from_avatar.relation_start_dates.pop(to_avatar.id, None)
    to_avatar.relation_start_dates.pop(from_avatar.id, None)


def archive_all_relations_for_death(avatar: "Avatar") -> None:
    related = list(_ensure_relations_dict(avatar).keys())
    for other in related:
        archive_relation_pair(avatar, other)


def cancel_relation(from_avatar: "Avatar", to_avatar: "Avatar", relation: Relation) -> bool:
    if relation == Relation.IS_FRIEND_OF or relation == Relation.IS_ENEMY_OF:
        clear_friendliness(from_avatar, to_avatar, keep_structural_relations=True)
        clear_friendliness(to_avatar, from_avatar, keep_structural_relations=True)
        return True
    if is_innate(relation):
        return False

    from_state = get_state(from_avatar, to_avatar)
    to_state = get_state(to_avatar, from_avatar)
    if from_state is None or to_state is None:
        return False
    if relation not in from_state.identity_relations:
        return False

    from_state.remove_identity(relation)
    to_state.remove_identity(get_reciprocal(relation))

    if not from_state.identity_relations and from_state.blood_relation is None and from_state.friendliness == 0:
        from_avatar.relations.pop(to_avatar, None)
    if not to_state.identity_relations and to_state.blood_relation is None and to_state.friendliness == 0:
        to_avatar.relations.pop(from_avatar, None)
    return True


def get_possible_cancel_relations(from_avatar: "Avatar", to_avatar: "Avatar") -> List[Relation]:
    state = get_state(from_avatar, to_avatar)
    if state is None:
        return []
    return sorted(state.identity_relations, key=lambda item: item.value)


def regress_yearly_friendliness(avatar: "Avatar", current_month: int | None = None) -> None:
    base_amount = int(getattr(CONFIG.social.relation, "yearly_regression", 2))
    reduced_amount = int(getattr(CONFIG.social.relation, "yearly_regression_with_identity", 1))
    for state in _ensure_relations_dict(avatar).values():
        if not isinstance(state, RelationState):
            continue
        if state.friendliness == 0:
            update_numeric_relation(state, current_month=current_month)
            continue
        amount = reduced_amount if state.identity_relations else base_amount
        if abs(state.friendliness) <= amount:
            state.friendliness = 0
        elif state.friendliness > 0:
            state.friendliness -= amount
        else:
            state.friendliness += amount
        _apply_identity_friendliness_floor(state)
        update_numeric_relation(state, current_month=current_month)
