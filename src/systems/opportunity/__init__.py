from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, TYPE_CHECKING

from src.classes.death import handle_death
from src.classes.death_reason import DeathReason, DeathType
from src.classes.event import Event
from src.classes.items.auxiliary import Auxiliary, get_random_auxiliary_by_realm
from src.classes.items.weapon import Weapon, get_random_weapon_by_realm
from src.classes.observe import get_avatar_observation_radius
from src.classes.story_event_service import StoryEventKind, StoryEventService
from src.i18n import t
from src.systems.cultivation import Realm
from src.systems.single_choice import (
    ItemExchangeKind,
    ItemExchangeRequest,
    RejectMode,
    resolve_item_exchange,
)
from src.utils.config import CONFIG
from src.utils.df import game_configs, get_float, get_int, get_str

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.core.world import World
    from src.classes.environment.region import Region


class OpportunityTargetType(StrEnum):
    REGION = "region"
    AVATAR = "avatar"


class OpportunityOutcome(StrEnum):
    EQUIPMENT = "equipment"
    BOON = "boon"
    EMPTY = "empty"
    INJURY = "injury"


@dataclass
class OpportunityRecord:
    id: str
    avatar_id: str
    target_type: OpportunityTargetType
    target_id: str
    hint_text: str
    created_month: int
    expires_month: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "avatar_id": self.avatar_id,
            "target_type": self.target_type.value,
            "target_id": self.target_id,
            "hint_text": self.hint_text,
            "created_month": int(self.created_month),
            "expires_month": int(self.expires_month),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OpportunityRecord":
        return cls(
            id=str(data.get("id") or uuid.uuid4()),
            avatar_id=str(data.get("avatar_id") or ""),
            target_type=OpportunityTargetType(str(data.get("target_type") or OpportunityTargetType.REGION.value)),
            target_id=str(data.get("target_id") or ""),
            hint_text=str(data.get("hint_text") or ""),
            created_month=int(data.get("created_month", 0) or 0),
            expires_month=int(data.get("expires_month", 0) or 0),
        )


class OpportunityManager:
    def __init__(self) -> None:
        self.active: dict[str, OpportunityRecord] = {}
        self.cooldowns: dict[str, int] = {}

    def get_for_avatar(self, avatar_id: str) -> OpportunityRecord | None:
        return self.active.get(str(avatar_id))

    def has_active(self, avatar_id: str) -> bool:
        return str(avatar_id) in self.active

    def add(self, record: OpportunityRecord) -> None:
        self.active[str(record.avatar_id)] = record

    def clear(self, avatar_id: str, *, cooldown_until: int | None = None) -> None:
        avatar_key = str(avatar_id)
        self.active.pop(avatar_key, None)
        if cooldown_until is not None:
            self.cooldowns[avatar_key] = int(cooldown_until)

    def is_in_cooldown(self, avatar_id: str, current_month: int) -> bool:
        return int(current_month) < int(self.cooldowns.get(str(avatar_id), 0) or 0)

    def to_save_dict(self) -> dict[str, Any]:
        return {
            "active": {
                avatar_id: record.to_dict()
                for avatar_id, record in self.active.items()
            },
            "cooldowns": {avatar_id: int(month) for avatar_id, month in self.cooldowns.items()},
        }

    def load_from_dict(self, data: dict[str, Any] | None) -> None:
        payload = data if isinstance(data, dict) else {}
        self.active = {}
        for avatar_id, raw_record in (payload.get("active") or {}).items():
            if not isinstance(raw_record, dict):
                continue
            record = OpportunityRecord.from_dict(raw_record)
            if not record.avatar_id:
                record.avatar_id = str(avatar_id)
            self.active[str(record.avatar_id)] = record
        self.cooldowns = {
            str(avatar_id): int(month)
            for avatar_id, month in (payload.get("cooldowns") or {}).items()
            if _can_int(month)
        }


def _can_int(value: object) -> bool:
    try:
        int(value)  # noqa: B018
        return True
    except (TypeError, ValueError):
        return False


def _get_cfg_value(name: str, default: Any) -> Any:
    cfg = getattr(getattr(CONFIG.world, "opportunity", None), name, None)
    return default if cfg is None else cfg


def _get_manager(world: "World") -> OpportunityManager:
    manager = getattr(world, "opportunity_manager", None)
    if manager is None:
        manager = OpportunityManager()
        setattr(world, "opportunity_manager", manager)
    return manager


def _cooldown_after_dissipated() -> int:
    return int(_get_cfg_value("cooldown_months_after_dissipated", 12) or 12)


def _cooldown_after_resolved() -> int:
    return int(_get_cfg_value("cooldown_months_after_resolved", 60) or 60)


def _duration_months() -> int:
    return int(_get_cfg_value("duration_months", 60) or 60)


def _opportunity_probability(avatar: "Avatar") -> float:
    base = float(_get_cfg_value("probability", 0.0) or 0.0)
    extra = float(getattr(avatar, "effects", {}).get("extra_opportunity_probability", 0.0) or 0.0)
    return max(0.0, min(1.0, base + extra))


def _weighted_choice_from_mapping(mapping: Any, defaults: dict[str, float]) -> str:
    weights: dict[str, float] = dict(defaults)
    if isinstance(mapping, dict):
        for key, value in mapping.items():
            try:
                weights[str(key)] = max(0.0, float(value))
            except (TypeError, ValueError):
                continue
    choices = [(key, weight) for key, weight in weights.items() if weight > 0]
    if not choices:
        return next(iter(defaults))
    keys, values = zip(*choices)
    return str(random.choices(keys, weights=values, k=1)[0])


def _relative_direction(from_x: int, from_y: int, to_x: int, to_y: int) -> str:
    dx = to_x - from_x
    dy = to_y - from_y
    horizontal = "east" if dx > 0 else "west"
    vertical = "south" if dy > 0 else "north"
    if abs(dx) >= abs(dy) * 2:
        return horizontal
    if abs(dy) >= abs(dx) * 2:
        return vertical
    if dx == 0 and dy == 0:
        return "nearby"
    return f"{vertical}_{horizontal}"


def _direction_label(direction: str) -> str:
    labels = {
        "north": t("north"),
        "south": t("south"),
        "east": t("east"),
        "west": t("west"),
        "nearby": t("nearby"),
        "north_east": t("northeast"),
        "north_west": t("northwest"),
        "south_east": t("southeast"),
        "south_west": t("southwest"),
    }
    return labels.get(direction, direction)


def _region_kind_label(region: "Region") -> str:
    from src.classes.environment.region import CityRegion, CultivateRegion, NormalRegion
    from src.classes.environment.sect_region import SectRegion

    if isinstance(region, CityRegion):
        return t("old city")
    if isinstance(region, SectRegion):
        return t("sect territory")
    if isinstance(region, CultivateRegion):
        return t("cave dwelling")
    if isinstance(region, NormalRegion):
        return t("wilderness place")
    return t("unknown place")


def _realm_hint(avatar: "Avatar") -> str:
    return str(getattr(getattr(avatar, "cultivation_progress", None), "realm", t("unknown realm")))


def _avatar_feature_hint(avatar: "Avatar") -> str:
    weapon = getattr(avatar, "weapon", None)
    if weapon is not None:
        weapon_type = getattr(weapon, "weapon_type", None)
        if weapon_type is not None:
            return t("{realm} {weapon_type} cultivator", realm=_realm_hint(avatar), weapon_type=str(weapon_type))
    sect = getattr(avatar, "sect", None)
    if sect is not None:
        return t("{realm} sect cultivator", realm=_realm_hint(avatar))
    return t("{realm} cultivator", realm=_realm_hint(avatar))


def _build_region_hint(avatar: "Avatar", region: "Region") -> str:
    center_x, center_y = getattr(region, "center_loc", (avatar.pos_x, avatar.pos_y))
    direction = _direction_label(_relative_direction(avatar.pos_x, avatar.pos_y, center_x, center_y))
    return t(
        "{avatar_name} felt a stir of fate, sensing a thread of opportunity tied to a {region_hint} in the {direction}.",
        avatar_name=avatar.name,
        region_hint=_region_kind_label(region),
        direction=direction,
    )


def _build_avatar_hint(avatar: "Avatar", target: "Avatar") -> str:
    direction = _direction_label(_relative_direction(avatar.pos_x, avatar.pos_y, target.pos_x, target.pos_y))
    return t(
        "{avatar_name} felt a stir of fate, sensing a thread of opportunity tied to a {target_hint} in the {direction}.",
        avatar_name=avatar.name,
        target_hint=_avatar_feature_hint(target),
        direction=direction,
    )


def _pick_region_target(avatar: "Avatar", world: "World") -> "Region | None":
    current_region_id = getattr(getattr(getattr(avatar, "tile", None), "region", None), "id", None)
    candidates = [
        region
        for region in getattr(getattr(world, "map", None), "regions", {}).values()
        if getattr(region, "id", None) is not None and getattr(region, "id", None) != current_region_id
    ]
    if not candidates:
        return None
    return random.choice(candidates)


def _pick_avatar_target(avatar: "Avatar", world: "World") -> "Avatar | None":
    candidates = [
        other
        for other in world.avatar_manager.get_living_avatars()
        if other.id != avatar.id and not getattr(other, "is_dead", False)
    ]
    if not candidates:
        return None
    return random.choice(candidates)


def _build_record(avatar: "Avatar", world: "World") -> OpportunityRecord | None:
    target_kind = _weighted_choice_from_mapping(
        _get_cfg_value("target_weights", None),
        {OpportunityTargetType.REGION.value: 70, OpportunityTargetType.AVATAR.value: 30},
    )
    if target_kind == OpportunityTargetType.AVATAR.value:
        target_avatar = _pick_avatar_target(avatar, world)
        if target_avatar is not None:
            current_month = int(world.month_stamp)
            return OpportunityRecord(
                id=str(uuid.uuid4()),
                avatar_id=str(avatar.id),
                target_type=OpportunityTargetType.AVATAR,
                target_id=str(target_avatar.id),
                hint_text=_build_avatar_hint(avatar, target_avatar),
                created_month=current_month,
                expires_month=current_month + _duration_months(),
            )

    target_region = _pick_region_target(avatar, world)
    if target_region is None:
        return None
    current_month = int(world.month_stamp)
    return OpportunityRecord(
        id=str(uuid.uuid4()),
        avatar_id=str(avatar.id),
        target_type=OpportunityTargetType.REGION,
        target_id=str(target_region.id),
        hint_text=_build_region_hint(avatar, target_region),
        created_month=current_month,
        expires_month=current_month + _duration_months(),
    )


def _event(owner: "Avatar", content: str, *, related_avatars: list[str] | None = None, is_major: bool = False) -> Event:
    return Event(
        owner.world.month_stamp,
        content,
        related_avatars=related_avatars or [owner.id],
        is_major=is_major,
        event_type="opportunity",
    )


async def try_generate_opportunity(avatar: "Avatar", world: "World") -> list[Event]:
    manager = _get_manager(world)
    current_month = int(world.month_stamp)
    if manager.has_active(avatar.id):
        return []
    if manager.is_in_cooldown(avatar.id, current_month):
        return []
    if not getattr(avatar, "can_trigger_world_event", True):
        return []
    prob = _opportunity_probability(avatar)
    if prob <= 0.0 or random.random() >= prob:
        return []

    record = _build_record(avatar, world)
    if record is None:
        return []
    manager.add(record)
    return [_event(avatar, record.hint_text)]


def _resolve_target_avatar(world: "World", target_id: str) -> "Avatar | None":
    manager = getattr(world, "avatar_manager", None)
    if manager is None:
        return None
    if hasattr(manager, "get_avatar"):
        return manager.get_avatar(str(target_id))
    return getattr(manager, "avatars", {}).get(str(target_id))


def _is_avatar_observable(owner: "Avatar", target: "Avatar") -> bool:
    radius = get_avatar_observation_radius(owner)
    distance = abs(int(target.pos_x) - int(owner.pos_x)) + abs(int(target.pos_y) - int(owner.pos_y))
    return distance <= radius


def _target_is_reached(owner: "Avatar", record: OpportunityRecord) -> tuple[bool, list[str]]:
    world = owner.world
    if record.target_type == OpportunityTargetType.REGION:
        region = getattr(getattr(owner, "tile", None), "region", None)
        return bool(region is not None and str(getattr(region, "id", "")) == str(record.target_id)), [owner.id]

    target = _resolve_target_avatar(world, record.target_id)
    if target is None or getattr(target, "is_dead", False):
        return False, [owner.id]
    return _is_avatar_observable(owner, target), [owner.id, target.id]


def _target_is_invalid(world: "World", record: OpportunityRecord) -> bool:
    if record.target_type == OpportunityTargetType.REGION:
        regions = getattr(getattr(world, "map", None), "regions", {})
        return not (int(record.target_id) in regions if _can_int(record.target_id) else record.target_id in regions)
    target = _resolve_target_avatar(world, record.target_id)
    return target is None or getattr(target, "is_dead", False)


def _pick_outcome() -> OpportunityOutcome:
    value = _weighted_choice_from_mapping(
        _get_cfg_value("outcome_weights", None),
        {
            OpportunityOutcome.EQUIPMENT.value: 35,
            OpportunityOutcome.BOON.value: 35,
            OpportunityOutcome.EMPTY.value: 20,
            OpportunityOutcome.INJURY.value: 10,
        },
    )
    try:
        return OpportunityOutcome(value)
    except ValueError:
        return OpportunityOutcome.EMPTY


def _next_realm(realm: Realm) -> Realm:
    realms = list(Realm)
    idx = realms.index(realm)
    return realms[min(idx + 1, len(realms) - 1)]


def _equipment_realm(avatar: "Avatar") -> Realm:
    return _next_realm(avatar.cultivation_progress.realm)


def _item_is_below_current_realm(item: object | None, avatar: "Avatar") -> bool:
    if item is None:
        return True
    realm = getattr(item, "realm", None)
    return bool(realm is not None and realm < avatar.cultivation_progress.realm)


def _pick_equipment(avatar: "Avatar") -> tuple[Weapon | Auxiliary | None, ItemExchangeKind | None]:
    target_realm = _equipment_realm(avatar)
    weapon_weight = 1.0
    auxiliary_weight = 1.0
    if _item_is_below_current_realm(getattr(avatar, "weapon", None), avatar):
        weapon_weight += 2.0
    if _item_is_below_current_realm(getattr(avatar, "auxiliary", None), avatar):
        auxiliary_weight += 2.0
    kind = random.choices(
        [ItemExchangeKind.WEAPON, ItemExchangeKind.AUXILIARY],
        weights=[weapon_weight, auxiliary_weight],
        k=1,
    )[0]
    if kind == ItemExchangeKind.WEAPON:
        return get_random_weapon_by_realm(target_realm), kind
    return get_random_auxiliary_by_realm(target_realm), kind


async def _apply_equipment(owner: "Avatar") -> tuple[str, bool]:
    item, kind = _pick_equipment(owner)
    if item is None or kind is None:
        return await _apply_boon(owner)
    intro = t(
        "{avatar_name} followed the opportunity and found an ancient treasure: {item_name}.",
        avatar_name=owner.name,
        item_name=item.name,
    )
    outcome = await resolve_item_exchange(
        ItemExchangeRequest(
            avatar=owner,
            new_item=item,
            kind=kind,
            scene_intro=intro,
            reject_mode=RejectMode.ABANDON_NEW,
            auto_accept_when_empty=True,
        )
    )
    return t(
        "{avatar_name} followed the opportunity and obtained {item_name}. {exchange_text}",
        avatar_name=owner.name,
        item_name=item.name,
        exchange_text=outcome.result_text,
    ), True


def _load_boon_records(owner: "Avatar") -> list[dict[str, Any]]:
    records = []
    for row in game_configs.get("opportunity_boon", []):
        min_realm = Realm.from_str(get_str(row, "min_realm", "QI_REFINEMENT"))
        max_realm = Realm.from_str(get_str(row, "max_realm", "NASCENT_SOUL"))
        if min_realm <= owner.cultivation_progress.realm <= max_realm:
            records.append(row)
    return records


async def _apply_boon(owner: "Avatar") -> tuple[str, bool]:
    from src.classes.effect import load_effect_from_str

    records = _load_boon_records(owner)
    if not records:
        return t("{avatar_name} followed the opportunity, but the spiritual trace faded away.", avatar_name=owner.name), False
    record = random.choices(records, weights=[max(0.0, get_float(row, "weight", 10.0)) for row in records], k=1)[0]
    effects = load_effect_from_str(get_str(record, "effects"))
    duration = get_int(record, "duration_months", 0)
    source = get_str(record, "source", "effect_source_opportunity")
    if duration > 0:
        owner.temporary_effects.append(
            {
                "source": source,
                "effects": effects,
                "start_month": int(owner.world.month_stamp),
                "duration": duration,
            }
        )
    else:
        owner.add_persistent_effect(source, effects)
    owner.recalc_effects()
    title = get_str(record, "title") or t("opportunity_boon")
    return t(
        "{avatar_name} followed the opportunity and gained a boon: {boon_title}.",
        avatar_name=owner.name,
        boon_title=title,
    ), True


def _apply_empty(owner: "Avatar") -> tuple[str, bool]:
    return t(
        "{avatar_name} followed the feeling, but only found the spiritual trace already gone.",
        avatar_name=owner.name,
    ), False


def _apply_injury(owner: "Avatar") -> tuple[str, bool]:
    min_ratio = float(_get_cfg_value("injury_min_hp_ratio", 0.2) or 0.2)
    max_ratio = float(_get_cfg_value("injury_max_hp_ratio", 0.8) or 0.8)
    if max_ratio < min_ratio:
        min_ratio, max_ratio = max_ratio, min_ratio
    damage = max(1, int(owner.hp.max * random.uniform(min_ratio, max_ratio)))
    owner.hp.cur -= damage
    if owner.hp.cur <= 0:
        handle_death(owner.world, owner, DeathReason(DeathType.SERIOUS_INJURY))
        return t(
            "{avatar_name} followed the opportunity, but suffered backlash and perished.",
            avatar_name=owner.name,
        ), True
    return t(
        "{avatar_name} followed the opportunity, but suffered backlash and was injured for {damage} HP.",
        avatar_name=owner.name,
        damage=damage,
    ), False


async def _resolve_opportunity(owner: "Avatar", record: OpportunityRecord, related_avatars: list[str]) -> list[Event]:
    outcome = _pick_outcome()
    if outcome == OpportunityOutcome.EQUIPMENT:
        result_text, is_major = await _apply_equipment(owner)
    elif outcome == OpportunityOutcome.BOON:
        result_text, is_major = await _apply_boon(owner)
    elif outcome == OpportunityOutcome.INJURY:
        result_text, is_major = _apply_injury(owner)
    else:
        result_text, is_major = _apply_empty(owner)

    base_event = _event(owner, result_text, related_avatars=related_avatars, is_major=is_major)
    story_event = await StoryEventService.maybe_create_story(
        kind=StoryEventKind.OPPORTUNITY,
        month_stamp=owner.world.month_stamp,
        start_text=record.hint_text,
        result_text=result_text,
        actors=[owner, _resolve_target_avatar(owner.world, record.target_id) if record.target_type == OpportunityTargetType.AVATAR else None],
        related_avatar_ids=related_avatars,
        prompt=t("opportunity_story_prompt"),
        allow_relation_changes=False,
    )
    events = [base_event]
    if story_event is not None:
        events.append(story_event)
    return events


async def phase_generate_opportunities(world: "World", living_avatars: list["Avatar"]) -> list[Event]:
    events: list[Event] = []
    for avatar in living_avatars:
        events.extend(await try_generate_opportunity(avatar, world))
    return events


async def phase_check_opportunities(world: "World", living_avatars: list["Avatar"]) -> list[Event]:
    manager = _get_manager(world)
    current_month = int(world.month_stamp)
    living_by_id = {str(avatar.id): avatar for avatar in living_avatars if not getattr(avatar, "is_dead", False)}
    events: list[Event] = []

    for avatar_id, record in list(manager.active.items()):
        owner = living_by_id.get(str(avatar_id))
        if owner is None:
            manager.clear(avatar_id)
            continue

        if current_month >= record.expires_month:
            manager.clear(avatar_id, cooldown_until=current_month + _cooldown_after_dissipated())
            events.append(
                _event(
                    owner,
                    t("{avatar_name}'s opportunity sense gradually faded away.", avatar_name=owner.name),
                )
            )
            continue

        if _target_is_invalid(world, record):
            manager.clear(avatar_id, cooldown_until=current_month + _cooldown_after_dissipated())
            events.append(
                _event(
                    owner,
                    t("{avatar_name}'s opportunity sense suddenly broke, leaving nowhere to seek.", avatar_name=owner.name),
                )
            )
            continue

        if current_month <= record.created_month:
            continue

        reached, related_avatars = _target_is_reached(owner, record)
        if not reached:
            continue

        manager.clear(avatar_id, cooldown_until=current_month + _cooldown_after_resolved())
        events.extend(await _resolve_opportunity(owner, record, related_avatars))

    return events


def get_opportunity_context_text(avatar: "Avatar") -> str:
    manager = _get_manager(avatar.world)
    record = manager.get_for_avatar(avatar.id)
    if record is None:
        return ""
    remaining = max(0, int(record.expires_month) - int(avatar.world.month_stamp))
    years = remaining // 12
    months = remaining % 12
    if years > 0 and months > 0:
        remaining_text = t("{years} years and {months} months", years=years, months=months)
    elif years > 0:
        remaining_text = t("{years} years", years=years)
    else:
        remaining_text = t("{months} months", months=months)
    return t("Opportunity sense: {hint} This sense may last about {remaining}.", hint=record.hint_text, remaining=remaining_text)


def serialize_opportunities(world: "World") -> dict[str, Any]:
    return _get_manager(world).to_save_dict()


def load_opportunities(world: "World", data: dict[str, Any] | None) -> None:
    manager = _get_manager(world)
    manager.load_from_dict(data)


__all__ = [
    "OpportunityManager",
    "OpportunityOutcome",
    "OpportunityRecord",
    "OpportunityTargetType",
    "phase_generate_opportunities",
    "phase_check_opportunities",
    "get_opportunity_context_text",
    "serialize_opportunities",
    "load_opportunities",
]
