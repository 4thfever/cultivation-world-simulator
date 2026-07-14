from __future__ import annotations

import random
import re
from collections import Counter
from typing import Any

from src.classes.event import Event
from src.i18n import t
from src.utils.config import CONFIG

from .loader import (
    load_background_npc_event_types,
    load_background_npc_profiles,
    load_background_npc_region_bindings,
)
from .models import (
    BACKGROUND_NPC_EVENT_TYPE,
    BackgroundNpcContext,
    BackgroundNpcEventType,
    BackgroundNpcProfile,
    BackgroundNpcRegionBinding,
    BackgroundNpcTriggerKind,
)


_FORMAT_FIELD_RE = re.compile(r"{([a-zA-Z_][a-zA-Z0-9_]*)}")


class BackgroundNpcService:
    """Create prewritten mortal-scene events without mutating world state."""

    _last_triggered_month_by_key: dict[tuple[int, str, str], int] = {}
    _monthly_counts: Counter[tuple[int, int, str]] = Counter()

    @classmethod
    def reset_runtime_state(cls) -> None:
        cls._last_triggered_month_by_key.clear()
        cls._monthly_counts.clear()

    @classmethod
    def create_action_echo_events(
        cls,
        world: Any,
        avatar: Any,
        action_key: str,
        *,
        max_events: int | None = None,
    ) -> list[Event]:
        config = cls._get_config()
        if not bool(getattr(config, "enabled", True)):
            return []
        prob = float(getattr(config, "action_echo_prob", 0.15))
        if prob <= 0 or random.random() >= prob:
            return []

        if max_events is None:
            max_events = int(getattr(config, "max_action_echo_per_month", 2) or 2)
        return cls._create_events_for_trigger(
            world,
            BackgroundNpcTriggerKind.ACTION_ECHO,
            avatars=[avatar],
            action_key=action_key,
            max_events=max_events,
        )

    @classmethod
    def create_monthly_events(cls, world: Any, living_avatars: list[Any]) -> list[Event]:
        config = cls._get_config()
        if not bool(getattr(config, "enabled", True)):
            return []

        events: list[Event] = []
        region_prob = float(getattr(config, "region_tick_prob", 0.25))
        if region_prob > 0 and random.random() < region_prob:
            events.extend(
                cls._create_events_for_trigger(
                    world,
                    BackgroundNpcTriggerKind.REGION_TICK,
                    max_events=int(getattr(config, "max_region_tick_per_month", 1) or 1),
                )
            )

        witness_prob = float(getattr(config, "avatar_witness_prob", 0.03))
        if witness_prob > 0:
            witness_avatars = [
                avatar
                for avatar in living_avatars
                if getattr(avatar, "can_trigger_world_event", False) and random.random() < witness_prob
            ]
            events.extend(
                cls._create_events_for_trigger(
                    world,
                    BackgroundNpcTriggerKind.AVATAR_WITNESS,
                    avatars=witness_avatars,
                    max_events=int(getattr(config, "max_avatar_witness_per_month", 2) or 2),
                )
            )
        return events

    @classmethod
    def _create_events_for_trigger(
        cls,
        world: Any,
        trigger_kind: BackgroundNpcTriggerKind,
        *,
        avatars: list[Any] | None = None,
        action_key: str | None = None,
        max_events: int,
    ) -> list[Event]:
        if max_events <= 0:
            return []

        profiles = {profile.profile_key: profile for profile in load_background_npc_profiles()}
        event_types = load_background_npc_event_types()
        bindings = load_background_npc_region_bindings()
        if not profiles or not event_types:
            return []

        events: list[Event] = []
        if trigger_kind == BackgroundNpcTriggerKind.REGION_TICK:
            candidates = cls._build_region_tick_contexts(world, profiles, event_types, bindings)
            events.extend(cls._pick_and_build_events(world, candidates, max_events=max_events))
        else:
            for avatar in avatars or []:
                if len(events) >= max_events:
                    break
                candidates = cls._build_avatar_contexts(
                    world,
                    avatar,
                    profiles,
                    event_types,
                    bindings,
                    trigger_kind=trigger_kind,
                    action_key=action_key,
                )
                events.extend(cls._pick_and_build_events(world, candidates, max_events=max_events - len(events)))
        return events

    @classmethod
    def _build_region_tick_contexts(
        cls,
        world: Any,
        profiles: dict[str, BackgroundNpcProfile],
        event_types: list[BackgroundNpcEventType],
        bindings: list[BackgroundNpcRegionBinding],
    ) -> list[BackgroundNpcContext]:
        contexts: list[BackgroundNpcContext] = []
        for region in cls._iter_regions(world):
            for event_type in event_types:
                if event_type.trigger_kind != BackgroundNpcTriggerKind.REGION_TICK:
                    continue
                profile = profiles.get(event_type.profile_key)
                if profile is None:
                    continue
                if cls._matches_region(world, region, event_type, profile, bindings):
                    contexts.append(cls._build_context(world, region, profile, event_type))
        return contexts

    @classmethod
    def _build_avatar_contexts(
        cls,
        world: Any,
        avatar: Any,
        profiles: dict[str, BackgroundNpcProfile],
        event_types: list[BackgroundNpcEventType],
        bindings: list[BackgroundNpcRegionBinding],
        *,
        trigger_kind: BackgroundNpcTriggerKind,
        action_key: str | None,
    ) -> list[BackgroundNpcContext]:
        region = getattr(getattr(avatar, "tile", None), "region", None)
        if region is None:
            return []
        contexts: list[BackgroundNpcContext] = []
        for event_type in event_types:
            if event_type.trigger_kind != trigger_kind:
                continue
            if trigger_kind == BackgroundNpcTriggerKind.ACTION_ECHO and not cls._matches_action(action_key, event_type):
                continue
            profile = profiles.get(event_type.profile_key)
            if profile is None:
                continue
            if not cls._matches_region(world, region, event_type, profile, bindings):
                continue
            if not cls._matches_avatar(avatar, event_type.avatar_filters):
                continue
            contexts.append(cls._build_context(world, region, profile, event_type, avatar=avatar, action_key=action_key))
        return contexts

    @classmethod
    def _pick_and_build_events(
        cls,
        world: Any,
        contexts: list[BackgroundNpcContext],
        *,
        max_events: int,
    ) -> list[Event]:
        events: list[Event] = []
        remaining = [
            context
            for context in contexts
            if cls._passes_cooldown(world, context) and cls._has_required_template_values(context)
        ]
        while remaining and len(events) < max_events:
            chosen = random.choices(remaining, weights=[context.event_type.weight for context in remaining], k=1)[0]
            event = cls._build_event(world, chosen)
            if event is not None:
                events.append(event)
                cls._record_trigger(world, chosen)
            remaining = [context for context in remaining if context.event_type.event_key != chosen.event_type.event_key]
        return events

    @staticmethod
    def _iter_regions(world: Any) -> list[Any]:
        game_map = getattr(world, "map", None)
        regions = getattr(game_map, "regions", {}) if game_map is not None else {}
        return list((regions or {}).values())

    @classmethod
    def _matches_region(
        cls,
        world: Any,
        region: Any,
        event_type: BackgroundNpcEventType,
        profile: BackgroundNpcProfile,
        bindings: list[BackgroundNpcRegionBinding],
    ) -> bool:
        map_id = str(getattr(getattr(world, "map", None), "map_id", "") or "")
        if event_type.map_ids and map_id not in event_type.map_ids:
            return False

        region_type = cls._region_type(region)
        if event_type.region_types and region_type not in event_type.region_types:
            return False

        tags = cls._region_scene_tags(world, region, bindings) | set(profile.default_scene_tags)
        required = set(event_type.required_tags)
        if required and not required.issubset(tags):
            return False
        if set(event_type.excluded_tags) & tags:
            return False
        return True

    @staticmethod
    def _region_type(region: Any) -> str:
        if region is None:
            return ""
        if hasattr(region, "get_region_type"):
            return str(region.get_region_type())
        return str(getattr(region, "type", "") or "")

    @classmethod
    def _region_scene_tags(
        cls,
        world: Any,
        region: Any,
        bindings: list[BackgroundNpcRegionBinding],
    ) -> set[str]:
        region_id = int(getattr(region, "id", -1))
        map_id = str(getattr(getattr(world, "map", None), "map_id", "") or "")
        tags: set[str] = set()
        for binding in bindings:
            if binding.map_id == map_id and binding.region_id == region_id:
                tags.update(binding.scene_tags)
        region_type = cls._region_type(region)
        if region_type == "city":
            tags.add("city")
        elif region_type == "sect":
            tags.update({"sect", "sect_edge"})
        elif region_type == "normal":
            tags.add("wild")
        elif region_type == "cultivate":
            tags.add("cultivate")
        return tags

    @staticmethod
    def _matches_action(action_key: str | None, event_type: BackgroundNpcEventType) -> bool:
        if not event_type.action_keys:
            return True
        return bool(action_key and action_key in event_type.action_keys)

    @classmethod
    def _matches_avatar(cls, avatar: Any, filters: dict[str, str]) -> bool:
        for key, expected in filters.items():
            if key == "race":
                race_id = cls._avatar_race_id(avatar)
                if expected == "yao":
                    if race_id == "human":
                        return False
                elif race_id != expected:
                    return False
            elif key == "alignment":
                alignment = getattr(avatar, "alignment", None)
                value = str(getattr(alignment, "value", alignment or "")).upper()
                if value != expected.upper():
                    return False
            elif key == "sect":
                has_sect = getattr(avatar, "sect", None) is not None
                if expected == "any" and not has_sect:
                    return False
                if expected == "none" and has_sect:
                    return False
            elif key == "official":
                rank = str(getattr(avatar, "official_rank", "none") or "none")
                has_official = rank not in {"none", "OFFICIAL_NONE"}
                if expected == "any" and not has_official:
                    return False
                if expected == "none" and has_official:
                    return False
            elif key in {"realm_min", "realm_max"}:
                if not cls._matches_realm_filter(avatar, key, expected):
                    return False
            else:
                return False
        return True

    @staticmethod
    def _avatar_race_id(avatar: Any) -> str:
        race = getattr(avatar, "race", None)
        return str(getattr(race, "id", race or "human"))

    @staticmethod
    def _matches_realm_filter(avatar: Any, key: str, expected: str) -> bool:
        try:
            from src.systems.cultivation import Realm, REALM_ORDER

            current = getattr(getattr(avatar, "cultivation_progress", None), "realm", None)
            current_realm = current if isinstance(current, Realm) else Realm.from_str(str(current))
            expected_realm = Realm.from_str(expected)
            current_idx = REALM_ORDER.index(current_realm)
            expected_idx = REALM_ORDER.index(expected_realm)
        except Exception:
            return False
        if key == "realm_min":
            return current_idx >= expected_idx
        return current_idx <= expected_idx

    @classmethod
    def _build_context(
        cls,
        world: Any,
        region: Any,
        profile: BackgroundNpcProfile,
        event_type: BackgroundNpcEventType,
        *,
        avatar: Any | None = None,
        action_key: str | None = None,
    ) -> BackgroundNpcContext:
        sect_name = cls._resolve_sect_name(region, avatar)
        dynasty = getattr(world, "dynasty", None)
        dynasty_title = str(getattr(dynasty, "title", "") or "") if dynasty is not None else None
        return BackgroundNpcContext(
            event_type=event_type,
            profile=profile,
            region=region,
            avatar=avatar,
            action_key=action_key,
            sect_name=sect_name,
            dynasty_title=dynasty_title,
        )

    @staticmethod
    def _resolve_sect_name(region: Any, avatar: Any | None) -> str | None:
        if region is not None and BackgroundNpcService._region_type(region) == "sect":
            name = getattr(region, "sect_name", None) or getattr(region, "name", None)
            if name:
                return str(name)
        sect = getattr(avatar, "sect", None)
        if sect is not None:
            name = getattr(sect, "name", None)
            if name:
                return str(name)
        return None

    @classmethod
    def _has_required_template_values(cls, context: BackgroundNpcContext) -> bool:
        text_template = t(context.event_type.text_id)
        fields = set(_FORMAT_FIELD_RE.findall(text_template))
        if "avatar_name" in fields and context.avatar is None:
            return False
        if "region_name" in fields and context.region is None:
            return False
        if "sect_name" in fields and not context.sect_name:
            return False
        if "dynasty_title" in fields and not context.dynasty_title:
            return False
        return True

    @classmethod
    def _build_event(cls, world: Any, context: BackgroundNpcContext) -> Event | None:
        content = cls._render_text(context)
        if not content or content == context.event_type.text_id:
            return None
        avatar = context.avatar
        related_avatars = None
        if context.event_type.trigger_kind in {
            BackgroundNpcTriggerKind.AVATAR_WITNESS,
            BackgroundNpcTriggerKind.ACTION_ECHO,
        } and avatar is not None:
            related_avatars = [avatar.id]

        related_sects = None
        sect_id = getattr(context.region, "sect_id", None)
        if sect_id is not None:
            try:
                related_sects = [int(sect_id)]
            except (TypeError, ValueError):
                related_sects = None

        return Event(
            world.month_stamp,
            content,
            related_avatars=related_avatars,
            related_sects=related_sects,
            is_major=False,
            is_story=False,
            event_type=BACKGROUND_NPC_EVENT_TYPE,
            render_params=cls._build_render_params(context),
        )

    @staticmethod
    def _build_render_params(context: BackgroundNpcContext) -> dict[str, Any]:
        region = context.region
        avatar = context.avatar
        params: dict[str, Any] = {
            "background_npc": True,
            "trigger_kind": context.event_type.trigger_kind.value,
            "event_key": context.event_type.event_key,
            "profile_key": context.profile.profile_key,
            "npc_role": t(context.profile.role_label_id),
        }
        if region is not None:
            params["region_id"] = int(getattr(region, "id", -1))
            params["region_name"] = str(getattr(region, "name", ""))
            params["region_type"] = BackgroundNpcService._region_type(region)
        if avatar is not None:
            params["avatar_id"] = str(getattr(avatar, "id", ""))
            params["avatar_name"] = str(getattr(avatar, "name", ""))
        if context.sect_name:
            params["sect_name"] = context.sect_name
        if context.action_key:
            params["action_key"] = context.action_key
        return params

    @staticmethod
    def _render_text(context: BackgroundNpcContext) -> str:
        avatar = context.avatar
        region = context.region
        return t(
            context.event_type.text_id,
            avatar_name=str(getattr(avatar, "name", "")),
            region_name=str(getattr(region, "name", "")),
            sect_name=context.sect_name or "",
            dynasty_title=context.dynasty_title or "",
            npc_role=t(context.profile.role_label_id),
        ).strip()

    @classmethod
    def _passes_cooldown(cls, world: Any, context: BackgroundNpcContext) -> bool:
        month = int(world.month_stamp)
        world_key = id(world)
        monthly_key = (world_key, month, context.event_type.event_key)
        if cls._monthly_counts[monthly_key] >= context.event_type.max_per_month:
            return False

        scope = cls._cooldown_scope(context)
        last_month = cls._last_triggered_month_by_key.get((world_key, scope, context.event_type.event_key))
        if last_month is None:
            return True
        return month - last_month >= context.event_type.cooldown_months

    @classmethod
    def _record_trigger(cls, world: Any, context: BackgroundNpcContext) -> None:
        month = int(world.month_stamp)
        world_key = id(world)
        cls._monthly_counts[(world_key, month, context.event_type.event_key)] += 1
        cls._last_triggered_month_by_key[(world_key, cls._cooldown_scope(context), context.event_type.event_key)] = month

    @staticmethod
    def _cooldown_scope(context: BackgroundNpcContext) -> str:
        if context.avatar is not None:
            return f"avatar:{context.avatar.id}"
        region_id = getattr(context.region, "id", "world")
        return f"region:{region_id}"

    @staticmethod
    def _get_config() -> Any:
        return getattr(getattr(CONFIG, "world", object()), "background_npc", object())


__all__ = ["BackgroundNpcService"]
