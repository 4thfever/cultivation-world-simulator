from __future__ import annotations

from typing import TYPE_CHECKING

from src.classes.alignment import Alignment
from src.classes.emotions import EmotionType
from src.classes.environment.region import CityRegion
from src.classes.event_observation import EventObservation
from src.classes.observe import is_within_observation
from src.systems.battle import get_base_strength

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.core.world import World
    from src.classes.event import Event


PUBLIC_PREDATION_EVENT_TYPE = "public_predation"
LOCAL_WITNESS_PUBLIC_PREDATION = "local_witness_public_predation"
PUBLIC_PREDATION_MAX_RESPONDERS = 1


def apply_public_event_reactions(event: "Event", world: "World") -> None:
    if event.event_type != PUBLIC_PREDATION_EVENT_TYPE or event.is_story:
        return

    predator = _resolve_predator(event, world)
    if predator is None or getattr(predator, "is_dead", False):
        return

    params = dict(event.render_params or {})
    params.setdefault("predator_id", str(predator.id))
    params.setdefault("predator_name", predator.name)
    params.setdefault("subject_name", predator.name)
    region = getattr(getattr(predator, "tile", None), "region", None)
    if region is not None:
        params.setdefault("city_name", str(getattr(region, "name", "")))
    event.render_params = params

    response_candidates: list["Avatar"] = []
    for observer in world.avatar_manager.get_living_avatars():
        if observer is predator or getattr(observer, "is_dead", False):
            continue
        if not _can_observe_public_predation(observer, predator):
            continue

        _append_witness_observation(event, observer, predator)
        if _apply_witness_emotion(observer, predator):
            response_candidates.append(observer)

    for responder in _select_response_candidates(response_candidates)[:PUBLIC_PREDATION_MAX_RESPONDERS]:
        _queue_public_predation_response(responder, predator)


def _resolve_predator(event: "Event", world: "World") -> "Avatar | None":
    predator_id = str((event.render_params or {}).get("predator_id") or "")
    if not predator_id and event.related_avatars:
        predator_id = str(event.related_avatars[0])
    if not predator_id:
        return None
    return world.avatar_manager.get_avatar(predator_id)


def _can_observe_public_predation(observer: "Avatar", predator: "Avatar") -> bool:
    observer_region = getattr(getattr(observer, "tile", None), "region", None)
    predator_region = getattr(getattr(predator, "tile", None), "region", None)
    if isinstance(predator_region, CityRegion) and observer_region == predator_region:
        return True
    return is_within_observation(observer, predator)


def _append_witness_observation(event: "Event", observer: "Avatar", predator: "Avatar") -> None:
    observer_id = str(observer.id)
    if observer_id in {str(item) for item in (event.related_avatars or [])}:
        return

    existing_keys = {
        (str(getattr(obs, "observer_avatar_id", "")), str(getattr(obs, "propagation_kind", "")))
        for obs in getattr(event, "observations", []) or []
    }
    key = (observer_id, LOCAL_WITNESS_PUBLIC_PREDATION)
    if key in existing_keys:
        return

    event.observations.append(
        EventObservation(
            observer_avatar_id=observer_id,
            subject_avatar_id=str(predator.id),
            propagation_kind=LOCAL_WITNESS_PUBLIC_PREDATION,
        )
    )


def _apply_witness_emotion(observer: "Avatar", predator: "Avatar") -> bool:
    alignment = getattr(observer, "alignment", None)
    if alignment == Alignment.EVIL:
        return False

    observer_strength = get_base_strength(observer)
    predator_strength = get_base_strength(predator)
    can_confront = alignment == Alignment.RIGHTEOUS and observer_strength >= predator_strength

    observer.emotion = EmotionType.ANGRY if can_confront else EmotionType.FEARFUL
    if not can_confront:
        return False
    return observer.current_action is None and not observer.has_plans()


def _select_response_candidates(candidates: list["Avatar"]) -> list["Avatar"]:
    return sorted(
        candidates,
        key=lambda avatar: (
            -get_base_strength(avatar),
            str(getattr(avatar, "name", "")),
            str(getattr(avatar, "id", "")),
        ),
    )


def _queue_public_predation_response(observer: "Avatar", predator: "Avatar") -> None:
    observer.load_decide_result_chain(
        [
            ("MoveToAvatar", {"avatar_name": predator.name}),
            ("Attack", {"avatar_name": predator.name}),
        ],
        observer.thinking,
        f"Stop {predator.name} after witnessing public predation.",
    )
