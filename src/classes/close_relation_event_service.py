from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.i18n import t
from src.classes.event_observation import EventObservation
from src.classes.relation.relation import Relation
from src.classes.relation.relations import add_friendliness

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.event import Event


_CLOSE_RELATION_WEIGHTS: dict[Relation, int] = {
    Relation.IS_PARENT_OF: 90,
    Relation.IS_CHILD_OF: 90,
    Relation.IS_LOVER_OF: 90,
    Relation.IS_SWORN_SIBLING_OF: 70,
    Relation.IS_MASTER_OF: 70,
    Relation.IS_DISCIPLE_OF: 70,
}

_POSITIVE_BOND_LABEL_IDS: dict[str, str] = {
    "bond_lovers_formed": "bond_label_lovers",
    "bond_sworn_sibling_formed": "bond_label_sworn_siblings",
    "bond_master_disciple_formed": "bond_label_master_disciple",
}


@dataclass
class CloseRelationLink:
    observer: "Avatar"
    relation: Relation
    weight: int


def get_close_relation_links(subject: "Avatar") -> list[CloseRelationLink]:
    links: dict[str, CloseRelationLink] = {}
    for other, state in (getattr(subject, "relations", {}) or {}).items():
        if other is None or getattr(other, "is_dead", False):
            continue

        candidates: list[Relation] = []
        if state.blood_relation in _CLOSE_RELATION_WEIGHTS:
            candidates.append(state.blood_relation)
        for rel in sorted(state.identity_relations, key=lambda item: item.value):
            if rel in _CLOSE_RELATION_WEIGHTS:
                candidates.append(rel)

        for rel in candidates:
            weight = _CLOSE_RELATION_WEIGHTS[rel]
            key = str(other.id)
            prev = links.get(key)
            if prev is None or weight > prev.weight:
                links[key] = CloseRelationLink(observer=other, relation=rel, weight=weight)

    return list(links.values())


def append_close_relation_major_observations(
    event: "Event",
    *,
    subject: "Avatar",
    propagation_kind: str,
) -> None:
    existing_keys = {
        (str(getattr(obs, "observer_avatar_id", "")), str(getattr(obs, "propagation_kind", "")))
        for obs in getattr(event, "observations", []) or []
    }
    direct_ids = {str(item) for item in (event.related_avatars or [])}

    for link in get_close_relation_links(subject):
        observer_id = str(link.observer.id)
        if observer_id in direct_ids:
            continue
        key = (observer_id, propagation_kind)
        if key in existing_keys:
            continue
        event.observations.append(
            EventObservation(
                observer_avatar_id=observer_id,
                subject_avatar_id=str(subject.id),
                propagation_kind=propagation_kind,
                relation_type=link.relation.value,
            )
        )
        existing_keys.add(key)


def apply_kill_hatred(*, victim: "Avatar", killer: "Avatar") -> None:
    current_month = int(victim.world.month_stamp)
    for link in get_close_relation_links(victim):
        if str(link.observer.id) == str(killer.id):
            continue
        delta = -90 if link.weight >= 90 else -70
        add_friendliness(link.observer, killer, delta, current_month=current_month)


def apply_positive_bond_warmth(
    *,
    subject: "Avatar",
    other_party: "Avatar",
    event_type: str,
) -> None:
    current_month = int(subject.world.month_stamp)
    if event_type == "bond_lovers_formed":
        delta = 35
    elif event_type == "bond_sworn_sibling_formed":
        delta = 25
    elif event_type == "bond_master_disciple_formed":
        delta = 20
    else:
        return

    for link in get_close_relation_links(subject):
        if str(link.observer.id) == str(other_party.id):
            continue
        add_friendliness(link.observer, other_party, delta, current_month=current_month)


def configure_positive_bond_event(
    event: "Event",
    *,
    avatar_a: "Avatar",
    avatar_b: "Avatar",
) -> None:
    append_close_relation_major_observations(
        event,
        subject=avatar_a,
        propagation_kind="close_relation_positive_bond",
    )
    append_close_relation_major_observations(
        event,
        subject=avatar_b,
        propagation_kind="close_relation_positive_bond",
    )
    params = dict(event.render_params or {})
    params.setdefault("avatar_a_id", str(avatar_a.id))
    params.setdefault("avatar_a_name", avatar_a.name)
    params.setdefault("avatar_b_id", str(avatar_b.id))
    params.setdefault("avatar_b_name", avatar_b.name)
    params.setdefault("bond_label_id", _POSITIVE_BOND_LABEL_IDS.get(event.event_type, "bond_label_major_relationship"))
    event.render_params = params
