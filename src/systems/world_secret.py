from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.classes.environment.region import CityRegion
from src.classes.event import Event
from src.classes.world_secret import (
    DISCLOSURE_KEEP_SECRET,
    DISCLOSURE_SHARE_ALL,
    WORLD_SECRET_NONE_ID,
    WORLD_SECRET_RANDOM_ID,
    AvatarWorldSecretKnowledge,
    WorldSecretDefinition,
    WorldSecretFragment,
    WorldSecretRuntime,
    WorldSecretTriggerBinding,
)
from src.i18n import t
from src.systems.single_choice import (
    FallbackMode,
    FallbackPolicy,
    SingleChoiceDecision,
    SingleChoiceOption,
    SingleChoiceOutcome,
    SingleChoiceRequest,
    resolve_single_choice,
)
from src.utils.config import CONFIG
from src.utils.df import game_configs, get_float, get_int, get_str


TRIGGER_KIND_REGION = "region"
TRIGGER_KIND_CITY = "city"
TRIGGER_KIND_INSIGHT = "insight"
VALID_TRIGGER_KINDS = {TRIGGER_KIND_REGION, TRIGGER_KIND_CITY, TRIGGER_KIND_INSIGHT}

REGION_DISCOVERY_PROBABILITY = 0.04
CITY_DISCOVERY_PROBABILITY = 0.05
INSIGHT_DISCOVERY_PROBABILITY = 0.003


def load_world_secret_definitions() -> dict[str, WorldSecretDefinition]:
    secrets: dict[str, WorldSecretDefinition] = {}
    for row in game_configs.get("world_secret", []):
        secret_id = get_str(row, "id")
        if not secret_id:
            continue
        secrets[secret_id] = WorldSecretDefinition(
            id=secret_id,
            title=get_str(row, "title"),
            secret=get_str(row, "secret"),
            weight=get_float(row, "weight", 1.0),
            fragments=[],
        )

    fragments_by_secret: dict[str, list[WorldSecretFragment]] = {}
    for row in game_configs.get("world_secret_fragment", []):
        fragment_id = get_str(row, "id")
        secret_id = get_str(row, "secret_id")
        trigger_kind = get_str(row, "trigger_kind")
        if not fragment_id or not secret_id or trigger_kind not in VALID_TRIGGER_KINDS:
            continue
        fragments_by_secret.setdefault(secret_id, []).append(
            WorldSecretFragment(
                id=fragment_id,
                secret_id=secret_id,
                order=get_int(row, "order", 0),
                angle=get_str(row, "angle"),
                text=get_str(row, "text"),
                trigger_kind=trigger_kind,
            )
        )

    for secret_id, fragments in fragments_by_secret.items():
        if secret_id in secrets:
            secrets[secret_id].fragments = sorted(fragments, key=lambda item: (item.order, item.id))

    if WORLD_SECRET_NONE_ID not in secrets:
        secrets[WORLD_SECRET_NONE_ID] = WorldSecretDefinition(
            id=WORLD_SECRET_NONE_ID,
            title=t("None"),
            secret="",
            weight=0.0,
            fragments=[],
        )
    return secrets


def get_world_secret_options() -> list[dict[str, str]]:
    definitions = load_world_secret_definitions()
    options = [
        {"id": WORLD_SECRET_NONE_ID, "title": definitions[WORLD_SECRET_NONE_ID].title or t("None")},
        {"id": WORLD_SECRET_RANDOM_ID, "title": t("Random")},
    ]
    for secret in sorted(
        [item for item in definitions.values() if item.id != WORLD_SECRET_NONE_ID],
        key=lambda item: item.id,
    ):
        options.append({"id": secret.id, "title": secret.title})
    return options


def get_world_secret_definition(secret_id: str | None) -> WorldSecretDefinition | None:
    definitions = load_world_secret_definitions()
    return definitions.get(str(secret_id or WORLD_SECRET_NONE_ID))


def _choose_random_secret_id(definitions: dict[str, WorldSecretDefinition]) -> str:
    candidates = [
        secret
        for secret in definitions.values()
        if secret.id != WORLD_SECRET_NONE_ID and secret.weight > 0
    ]
    if not candidates:
        return WORLD_SECRET_NONE_ID
    return random.choices(candidates, weights=[secret.weight for secret in candidates], k=1)[0].id


def _region_candidates(world: Any) -> list[Any]:
    regions = list(getattr(getattr(world, "map", None), "regions", {}).values())
    return [
        region
        for region in regions
        if getattr(region, "id", -1) != -1 and not isinstance(region, CityRegion)
    ]


def _city_candidates(world: Any) -> list[CityRegion]:
    regions = list(getattr(getattr(world, "map", None), "regions", {}).values())
    return [
        region
        for region in regions
        if getattr(region, "id", -1) != -1 and isinstance(region, CityRegion)
    ]


def initialize_world_secret(world: Any, selected_secret_id: str | None) -> WorldSecretRuntime:
    definitions = load_world_secret_definitions()
    requested_id = str(selected_secret_id or WORLD_SECRET_NONE_ID)
    if requested_id == WORLD_SECRET_RANDOM_ID:
        requested_id = _choose_random_secret_id(definitions)
    if requested_id not in definitions:
        requested_id = WORLD_SECRET_NONE_ID

    definition = definitions[requested_id]
    runtime = WorldSecretRuntime(selected_secret_id=definition.id)
    if definition.id == WORLD_SECRET_NONE_ID:
        world.world_secret = runtime
        return runtime

    region_pool = _region_candidates(world)
    city_pool = _city_candidates(world)
    for fragment in definition.fragments:
        binding = WorldSecretTriggerBinding(
            fragment_id=fragment.id,
            trigger_kind=fragment.trigger_kind,
        )
        if fragment.trigger_kind == TRIGGER_KIND_REGION and region_pool:
            binding.region_id = int(getattr(random.choice(region_pool), "id"))
        elif fragment.trigger_kind == TRIGGER_KIND_CITY and city_pool:
            binding.city_region_id = int(getattr(random.choice(city_pool), "id"))
        runtime.trigger_bindings[fragment.id] = binding

    world.world_secret = runtime
    return runtime


def get_avatar_secret_knowledge(avatar: Any, secret_id: str) -> AvatarWorldSecretKnowledge:
    knowledge_map = getattr(avatar, "world_secret_knowledge", None)
    if knowledge_map is None:
        avatar.world_secret_knowledge = {}
        knowledge_map = avatar.world_secret_knowledge
    if secret_id not in knowledge_map:
        knowledge_map[secret_id] = AvatarWorldSecretKnowledge(secret_id=secret_id)
    item = knowledge_map[secret_id]
    if isinstance(item, dict):
        item = AvatarWorldSecretKnowledge.from_dict(secret_id, item)
        knowledge_map[secret_id] = item
    return item


def avatar_knows_full_secret(avatar: Any, secret_id: str) -> bool:
    world_secret = getattr(getattr(avatar, "world", None), "world_secret", None)
    if world_secret is not None and getattr(world_secret, "public_revealed", False):
        return True
    return bool(get_avatar_secret_knowledge(avatar, secret_id).knows_full_secret)


def sync_avatar_public_world_secret_knowledge(world: Any, avatar: Any) -> None:
    runtime = getattr(world, "world_secret", None)
    if runtime is None or not runtime.is_enabled() or not runtime.public_revealed:
        return
    knowledge = get_avatar_secret_knowledge(avatar, runtime.selected_secret_id)
    knowledge.knows_full_secret = True
    if knowledge.full_secret_month is None:
        knowledge.full_secret_month = int(getattr(world, "month_stamp", 0))


def sync_public_world_secret_for_all(world: Any) -> None:
    avatar_manager = getattr(world, "avatar_manager", None)
    if avatar_manager is None:
        return
    avatars = list(getattr(avatar_manager, "avatars", {}).values())
    for avatar in avatars:
        sync_avatar_public_world_secret_knowledge(world, avatar)


def load_world_secret_from_save(world: Any, data: dict[str, Any] | None) -> None:
    world.world_secret = WorldSecretRuntime.from_dict(data)
    if getattr(world.world_secret, "public_revealed", False):
        sync_public_world_secret_for_all(world)


def serialize_world_secret(world: Any) -> dict[str, Any]:
    runtime = getattr(world, "world_secret", None)
    if runtime is None:
        runtime = WorldSecretRuntime()
    return runtime.to_dict()


def _active_definition(world: Any) -> WorldSecretDefinition | None:
    runtime = getattr(world, "world_secret", None)
    if runtime is None or not runtime.is_enabled():
        return get_world_secret_definition(WORLD_SECRET_NONE_ID)
    return get_world_secret_definition(runtime.selected_secret_id)


def build_avatar_world_secret_ai_context(avatar: Any) -> dict[str, Any] | None:
    world = getattr(avatar, "world", None)
    definition = _active_definition(world) if world is not None else None
    runtime = getattr(world, "world_secret", None) if world is not None else None
    if definition is None or runtime is None or definition.id == WORLD_SECRET_NONE_ID:
        return None
    knowledge = get_avatar_secret_knowledge(avatar, definition.id)
    fragments_by_id = {fragment.id: fragment for fragment in definition.fragments}
    known_fragments = [
        {
            "angle": fragments_by_id[fragment_id].angle,
            "text": fragments_by_id[fragment_id].text,
        }
        for fragment_id in sorted(
            knowledge.known_fragment_ids,
            key=lambda item: (fragments_by_id[item].order, item) if item in fragments_by_id else (9999, item),
        )
        if fragment_id in fragments_by_id
    ]
    knows_full = bool(knowledge.knows_full_secret or runtime.public_revealed)
    payload: dict[str, Any] = {
        "known_fragments": known_fragments,
        "knows_full_secret": knows_full,
        "full_secret": "",
    }
    if knows_full:
        payload["secret_title"] = definition.title
        payload["full_secret"] = definition.secret
    return payload


def _fragment_discovery_probability(trigger_kind: str) -> float:
    if trigger_kind == TRIGGER_KIND_CITY:
        return CITY_DISCOVERY_PROBABILITY
    if trigger_kind == TRIGGER_KIND_INSIGHT:
        return INSIGHT_DISCOVERY_PROBABILITY
    return REGION_DISCOVERY_PROBABILITY


def _can_discover_fragment(world: Any, avatar: Any, binding: WorldSecretTriggerBinding) -> bool:
    if binding.trigger_kind == TRIGGER_KIND_INSIGHT:
        return bool(getattr(avatar, "can_trigger_world_event", True))

    region = getattr(getattr(avatar, "tile", None), "region", None)
    region_id = int(getattr(region, "id", -999999)) if region is not None else -999999
    if binding.trigger_kind == TRIGGER_KIND_REGION:
        return binding.region_id is not None and region_id == int(binding.region_id)
    if binding.trigger_kind == TRIGGER_KIND_CITY:
        return binding.city_region_id is not None and region_id == int(binding.city_region_id)
    return False


def _build_discovery_event(world: Any, avatar: Any, fragment: WorldSecretFragment) -> Event:
    region = getattr(getattr(avatar, "tile", None), "region", None)
    location_name = str(getattr(region, "name", "") or t("unknown location"))
    if fragment.trigger_kind == TRIGGER_KIND_CITY:
        content = t(
            "{avatar} heard a hidden clue in the market rumors of {location}: {fragment}",
            avatar=avatar.name,
            location=location_name,
            fragment=fragment.text,
        )
    elif fragment.trigger_kind == TRIGGER_KIND_INSIGHT:
        content = t(
            "{avatar} glimpsed a corner of the truth through a mysterious insight: {fragment}",
            avatar=avatar.name,
            fragment=fragment.text,
        )
    else:
        content = t(
            "{avatar} noticed an unusual clue at {location}: {fragment}",
            avatar=avatar.name,
            location=location_name,
            fragment=fragment.text,
        )
    return Event(
        world.month_stamp,
        content,
        related_avatars=[avatar.id],
        is_major=False,
        is_story=False,
        event_type="world_secret_fragment_discovered",
    )


def _build_full_secret_event(world: Any, avatar: Any) -> Event:
    return Event(
        world.month_stamp,
        t(
            "{avatar} connected scattered clues and finally learned a world secret capable of shaking this realm's foundations.",
            avatar=avatar.name,
        ),
        related_avatars=[avatar.id],
        is_major=True,
        is_story=False,
        event_type="world_secret_resolved",
    )


@dataclass(slots=True)
class WorldSecretDisclosureOutcome(SingleChoiceOutcome):
    events: list[Event]


@dataclass(slots=True)
class WorldSecretDisclosureScenario:
    world: Any
    avatar: Any
    definition: WorldSecretDefinition

    def build_request(self) -> SingleChoiceRequest:
        return SingleChoiceRequest(
            task_name="single_choice",
            template_path=Path(CONFIG.paths.templates) / "single_choice.txt",
            avatar=self.avatar,
            situation=t(
                (
                    "{avatar} has pieced together scattered clues and learned a world secret capable of shaking this realm's foundations. "
                    "If revealed, the secret will become known to all under heaven; if kept silent, only {avatar} will bear it. "
                    "Complete secret: {secret}"
                ),
                avatar=self.avatar.name,
                secret=self.definition.secret,
            ),
            title=t("Reveal the world secret?"),
            description=t(
                "You have learned a secret capable of shaking the world's foundations. Will you tell all under heaven, or remain silent alone?"
            ),
            options=[
                SingleChoiceOption(
                    key=DISCLOSURE_SHARE_ALL,
                    title=t("Tell everyone"),
                    description=t("Reveal the complete secret so all cultivators under heaven know this realm's truth."),
                ),
                SingleChoiceOption(
                    key=DISCLOSURE_KEEP_SECRET,
                    title=t("Bear it silently"),
                    description=t("Do not spread it; bear this truth alone."),
                ),
            ],
            fallback_policy=FallbackPolicy(
                mode=FallbackMode.PREFERRED_KEY,
                preferred_key=DISCLOSURE_KEEP_SECRET,
            ),
        )

    async def apply_decision(self, decision: SingleChoiceDecision) -> WorldSecretDisclosureOutcome:
        runtime = self.world.world_secret
        selected = decision.selected_key
        if selected not in {DISCLOSURE_SHARE_ALL, DISCLOSURE_KEEP_SECRET}:
            selected = DISCLOSURE_KEEP_SECRET
        runtime.disclosure_decisions[str(self.avatar.id)] = selected
        if selected == DISCLOSURE_SHARE_ALL:
            runtime.public_revealed = True
            runtime.public_revealed_month = int(self.world.month_stamp)
            runtime.public_revealed_by_avatar_id = str(self.avatar.id)
            sync_public_world_secret_for_all(self.world)
            event = Event(
                self.world.month_stamp,
                t(
                    "{avatar} revealed a world secret to all: '{title}'. From now on, cultivators under heaven know this realm's truth.",
                    avatar=self.avatar.name,
                    title=self.definition.title,
                ),
                related_avatars=[self.avatar.id],
                is_major=True,
                is_story=False,
                event_type="world_secret_public_revealed",
            )
            return WorldSecretDisclosureOutcome(decision=decision, result_text=event.content, events=[event])

        event = Event(
            self.world.month_stamp,
            t(
                "{avatar} chose silence after learning the truth, pressing this secret deep into the heart.",
                avatar=self.avatar.name,
            ),
            related_avatars=[self.avatar.id],
            is_major=False,
            is_story=False,
            event_type="world_secret_kept",
        )
        return WorldSecretDisclosureOutcome(decision=decision, result_text=event.content, events=[event])


async def _resolve_full_secret_if_complete(world: Any, avatar: Any, definition: WorldSecretDefinition) -> list[Event]:
    runtime = world.world_secret
    knowledge = get_avatar_secret_knowledge(avatar, definition.id)
    if knowledge.knows_full_secret:
        return []
    all_fragment_ids = {fragment.id for fragment in definition.fragments}
    if not all_fragment_ids or not all_fragment_ids.issubset(knowledge.known_fragment_ids):
        return []

    knowledge.knows_full_secret = True
    knowledge.full_secret_month = int(world.month_stamp)
    runtime.resolved_by_avatar_ids.add(str(avatar.id))
    events = [_build_full_secret_event(world, avatar)]
    if str(avatar.id) not in runtime.disclosure_decisions:
        outcome = await resolve_single_choice(WorldSecretDisclosureScenario(world, avatar, definition))
        events.extend(outcome.events)
    return events


async def try_discover_world_secret_fragments(world: Any, avatar: Any) -> list[Event]:
    runtime = getattr(world, "world_secret", None)
    if runtime is None or not runtime.is_enabled() or runtime.public_revealed:
        return []
    definition = get_world_secret_definition(runtime.selected_secret_id)
    if definition is None or not definition.fragments:
        return []

    knowledge = get_avatar_secret_knowledge(avatar, definition.id)
    fragments_by_id = {fragment.id: fragment for fragment in definition.fragments}
    events: list[Event] = []
    for fragment in definition.fragments:
        if fragment.id in knowledge.known_fragment_ids:
            continue
        binding = runtime.trigger_bindings.get(fragment.id)
        if binding is None:
            continue
        if not _can_discover_fragment(world, avatar, binding):
            continue
        if random.random() >= _fragment_discovery_probability(binding.trigger_kind):
            continue
        knowledge.known_fragment_ids.add(fragment.id)
        events.append(_build_discovery_event(world, avatar, fragments_by_id[fragment.id]))

    events.extend(await _resolve_full_secret_if_complete(world, avatar, definition))
    return events


async def phase_world_secret_discovery(world: Any, living_avatars: list[Any]) -> list[Event]:
    events: list[Event] = []
    for avatar in living_avatars:
        if getattr(avatar, "is_dead", False):
            continue
        sync_avatar_public_world_secret_knowledge(world, avatar)
        events.extend(await try_discover_world_secret_fragments(world, avatar))
    return events


def build_world_secret_overview(world: Any) -> dict[str, Any]:
    runtime = getattr(world, "world_secret", None) or WorldSecretRuntime()
    definition = get_world_secret_definition(runtime.selected_secret_id) or get_world_secret_definition(WORLD_SECRET_NONE_ID)
    if definition is None:
        definition = WorldSecretDefinition(WORLD_SECRET_NONE_ID, t("None"), "", 0.0, [])

    avatar_manager = getattr(world, "avatar_manager", None)
    all_avatars = []
    if avatar_manager is not None:
        living = list(getattr(avatar_manager, "avatars", {}).values())
        dead = list(getattr(avatar_manager, "dead_avatars", {}).values())
        all_avatars = living + dead

    fragments_payload: list[dict[str, Any]] = []
    for fragment in definition.fragments:
        known_by = []
        for avatar in all_avatars:
            knowledge = get_avatar_secret_knowledge(avatar, definition.id)
            if fragment.id not in knowledge.known_fragment_ids:
                continue
            known_by.append(
                {
                    "id": str(getattr(avatar, "id", "")),
                    "name": str(getattr(avatar, "name", "")),
                    "is_dead": bool(getattr(avatar, "is_dead", False)),
                }
            )
        fragments_payload.append(
            {
                "id": fragment.id,
                "order": fragment.order,
                "angle": fragment.angle,
                "text": fragment.text,
                "known_by": known_by,
            }
        )

    avatars_payload: list[dict[str, Any]] = []
    fragment_count = len(definition.fragments)
    for avatar in all_avatars:
        knowledge = get_avatar_secret_knowledge(avatar, definition.id)
        knows_full = bool(knowledge.knows_full_secret or runtime.public_revealed)
        known_count = len([fid for fid in knowledge.known_fragment_ids if fid in {f.id for f in definition.fragments}])
        if known_count <= 0 and not knows_full:
            continue
        avatars_payload.append(
            {
                "id": str(getattr(avatar, "id", "")),
                "name": str(getattr(avatar, "name", "")),
                "known_fragment_count": known_count,
                "fragment_count": fragment_count,
                "knows_full_secret": knows_full,
                "decision": runtime.disclosure_decisions.get(str(getattr(avatar, "id", ""))),
                "is_dead": bool(getattr(avatar, "is_dead", False)),
            }
        )

    public_avatar = None
    if runtime.public_revealed_by_avatar_id:
        for avatar in all_avatars:
            if str(getattr(avatar, "id", "")) == str(runtime.public_revealed_by_avatar_id):
                public_avatar = {
                    "id": str(getattr(avatar, "id", "")),
                    "name": str(getattr(avatar, "name", "")),
                    "is_dead": bool(getattr(avatar, "is_dead", False)),
                }
                break

    return {
        "active_secret": {
            "id": definition.id,
            "title": definition.title,
            "secret": definition.secret,
            "fragment_count": fragment_count,
        },
        "public_revealed": bool(runtime.public_revealed),
        "public_revealed_month": runtime.public_revealed_month,
        "public_revealed_by": public_avatar,
        "fragments": fragments_payload,
        "avatars": avatars_payload,
    }


__all__ = [
    "CITY_DISCOVERY_PROBABILITY",
    "INSIGHT_DISCOVERY_PROBABILITY",
    "REGION_DISCOVERY_PROBABILITY",
    "TRIGGER_KIND_CITY",
    "TRIGGER_KIND_INSIGHT",
    "TRIGGER_KIND_REGION",
    "VALID_TRIGGER_KINDS",
    "avatar_knows_full_secret",
    "build_avatar_world_secret_ai_context",
    "build_world_secret_overview",
    "get_avatar_secret_knowledge",
    "get_world_secret_definition",
    "get_world_secret_options",
    "initialize_world_secret",
    "load_world_secret_definitions",
    "load_world_secret_from_save",
    "phase_world_secret_discovery",
    "serialize_world_secret",
    "sync_avatar_public_world_secret_knowledge",
    "sync_public_world_secret_for_all",
    "try_discover_world_secret_fragments",
]
