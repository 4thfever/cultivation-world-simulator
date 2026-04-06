from __future__ import annotations

import json
import random

from src.classes.core.avatar import Avatar
from src.classes.core.world import World
from src.classes.event import Event
from src.classes.goldfinger import build_goldfinger_story_hint
from src.classes.observe import get_avatar_observation_radius
from src.classes.relation.relations import ensure_numeric_relation_state
from src.classes.relation.relation_delta_service import RelationDeltaService
from src.i18n import t
from src.run.log import get_logger
from src.utils.config import CONFIG
from src.utils.llm.client import call_llm_with_task_name

from .random_minor_event_loader import load_minor_event_types
from .random_minor_event_types import (
    MinorEventContext,
    MinorEventParticipants,
    MinorEventRelationHint,
    MinorEventTone,
    MinorEventType,
)


class RandomMinorEventService:
    SOLO_TEMPLATE_NAME = "random_minor_event_solo.txt"
    PAIR_TEMPLATE_NAME = "random_minor_event_pair.txt"

    @classmethod
    def should_trigger(cls, avatar: Avatar) -> bool:
        base_prob = float(getattr(CONFIG.world, "random_minor_event_prob", 0.05))
        if base_prob <= 0.0:
            return False
        if not avatar.can_trigger_world_event:
            return False
        return random.random() < base_prob

    @classmethod
    async def try_create_events(cls, avatar: Avatar, world: World) -> list[Event]:
        event_types = load_minor_event_types()
        if not event_types:
            return []

        event_type = cls._pick_event_type(event_types)
        if event_type is None:
            return []

        context = cls._build_context(avatar, world, event_type, event_types)
        if context is None:
            return []

        event_text = await cls._generate_event_text(context)
        if not event_text:
            return []

        event = cls._build_event(context, event_text)
        if context.target_avatar is not None:
            await cls._apply_pair_friendliness_delta(context, event_text)
        return [event]

    @staticmethod
    def _pick_event_type(event_types: list[MinorEventType]) -> MinorEventType | None:
        if not event_types:
            return None
        return random.choices(event_types, weights=[event_type.weight for event_type in event_types], k=1)[0]

    @classmethod
    def _build_context(
        cls,
        avatar: Avatar,
        world: World,
        event_type: MinorEventType,
        event_types: list[MinorEventType],
    ) -> MinorEventContext | None:
        target_avatar = None
        if event_type.participants == MinorEventParticipants.PAIR:
            target_avatar = cls._pick_target_avatar(avatar, world)
            if target_avatar is None:
                solo_types = [item for item in event_types if item.participants == MinorEventParticipants.SOLO]
                fallback_type = cls._pick_event_type(solo_types)
                if fallback_type is None:
                    return None
                event_type = fallback_type

        location_name = avatar.tile.region.name if avatar.tile and avatar.tile.region else t("unknown location")
        world_info = ""
        if world.current_phenomenon:
            world_info = t("Current world celestial phenomenon: {name}", name=world.current_phenomenon.name)

        return MinorEventContext(
            source_avatar=avatar,
            target_avatar=target_avatar,
            event_type=event_type,
            location_name=location_name,
            world_info=world_info,
        )

    @staticmethod
    def _pick_target_avatar(avatar: Avatar, world: World) -> Avatar | None:
        radius = get_avatar_observation_radius(avatar)
        candidates: list[Avatar] = []
        for other in world.avatar_manager.get_living_avatars():
            if other.id == avatar.id or other.is_dead:
                continue
            dist = abs(other.pos_x - avatar.pos_x) + abs(other.pos_y - avatar.pos_y)
            if dist <= radius:
                candidates.append(other)
        if not candidates:
            return None
        return random.choice(candidates)

    @classmethod
    async def _generate_event_text(cls, context: MinorEventContext) -> str:
        template_name = cls.PAIR_TEMPLATE_NAME if context.target_avatar is not None else cls.SOLO_TEMPLATE_NAME
        infos = cls._build_prompt_infos(context)
        try:
            result = await call_llm_with_task_name(
                task_name="random_minor_event",
                template_path=CONFIG.paths.templates / template_name,
                infos=infos,
            )
        except Exception as exc:
            get_logger().logger.error(
                "Failed to generate random minor event for %s: %s",
                context.source_avatar.name,
                exc,
            )
            return ""
        return str(result.get("event_text", "")).strip()

    @classmethod
    def _build_prompt_infos(cls, context: MinorEventContext) -> dict:
        source_avatar = context.source_avatar
        target_avatar = context.target_avatar
        event_type = context.event_type
        goldfinger_hint = build_goldfinger_story_hint(source_avatar, target_avatar)
        world_info = context.world_info
        if goldfinger_hint:
            world_info = f"{world_info}\n外挂叙事提示：{goldfinger_hint}".strip()

        if target_avatar is None:
            avatar_info = json.dumps(source_avatar.get_expanded_info(detailed=True), ensure_ascii=False)
            return {
                "avatar_info": avatar_info,
                "location": context.location_name,
                "world_info": world_info,
                "event_key": event_type.event_key,
                "event_desc": t(event_type.desc_id),
                "tone": cls._tone_label(event_type.tone),
            }

        avatar_a_info = json.dumps(
            source_avatar.get_expanded_info(other_avatar=target_avatar, detailed=True),
            ensure_ascii=False,
        )
        avatar_b_info = json.dumps(target_avatar.get_info(detailed=True), ensure_ascii=False)
        return {
            "avatar_a_name": source_avatar.name,
            "avatar_b_name": target_avatar.name,
            "avatar_a_info": avatar_a_info,
            "avatar_b_info": avatar_b_info,
            "location": context.location_name,
            "world_info": world_info,
            "event_key": event_type.event_key,
            "event_desc": t(event_type.desc_id),
            "tone": cls._tone_label(event_type.tone),
            "relation_hint": cls._relation_hint_label(event_type.relation_hint),
            "current_relation_summary": cls._build_current_relation_summary(source_avatar, target_avatar),
        }

    @staticmethod
    def _tone_label(tone: MinorEventTone) -> str:
        labels = {
            MinorEventTone.NEUTRAL: "中性日常",
            MinorEventTone.WARM: "略带善意",
            MinorEventTone.TENSE: "略带紧张",
            MinorEventTone.COMPETITIVE: "轻微竞争",
        }
        return labels[tone]

    @staticmethod
    def _relation_hint_label(relation_hint: MinorEventRelationHint) -> str:
        labels = {
            MinorEventRelationHint.NONE: "不涉及关系变化倾向",
            MinorEventRelationHint.MAYBE_UP: "可表现出细微升温",
            MinorEventRelationHint.MAYBE_DOWN: "可表现出细微降温",
            MinorEventRelationHint.MIXED: "可以偏冷也可以偏暖，视情境而定",
        }
        return labels[relation_hint]

    @staticmethod
    def _build_current_relation_summary(avatar_a: Avatar, avatar_b: Avatar) -> str:
        relation_a = avatar_a.get_relation(avatar_b)
        relation_b = avatar_b.get_relation(avatar_a)
        numeric_a = avatar_a.get_numeric_relation(avatar_b)
        numeric_b = avatar_b.get_numeric_relation(avatar_a)
        return (
            f"{avatar_a.name}对{avatar_b.name}："
            f"身份关系={relation_a or '无'}，"
            f"数值关系={numeric_a}，"
            f"友好度={avatar_a.get_friendliness(avatar_b)}；"
            f"{avatar_b.name}对{avatar_a.name}："
            f"身份关系={relation_b or '无'}，"
            f"数值关系={numeric_b}，"
            f"友好度={avatar_b.get_friendliness(avatar_a)}"
        )

    @staticmethod
    def _build_event(context: MinorEventContext, event_text: str) -> Event:
        related_avatars = [context.source_avatar.id]
        if context.target_avatar is not None:
            related_avatars.append(context.target_avatar.id)
        return Event(
            context.source_avatar.world.month_stamp,
            event_text,
            related_avatars=related_avatars,
            is_major=False,
            is_story=False,
        )

    @classmethod
    async def _apply_pair_friendliness_delta(cls, context: MinorEventContext, event_text: str) -> None:
        target_avatar = context.target_avatar
        if target_avatar is None:
            return

        a_to_b, b_to_a = await cls.resolve_minor_event_delta(context, event_text)
        RelationDeltaService.apply_bidirectional_delta(
            context.source_avatar,
            target_avatar,
            a_to_b,
            b_to_a,
        )
        current_month = int(context.source_avatar.world.month_stamp)
        ensure_numeric_relation_state(context.source_avatar, current_month=current_month)
        ensure_numeric_relation_state(target_avatar, current_month=current_month)

    @classmethod
    async def resolve_minor_event_delta(cls, context: MinorEventContext, event_text: str) -> tuple[int, int]:
        target_avatar = context.target_avatar
        if target_avatar is None:
            return 0, 0
        return await RelationDeltaService.resolve_event_text_delta(
            action_key="random_minor_event",
            avatar_a=context.source_avatar,
            avatar_b=target_avatar,
            event_text=(
                f"[event_key={context.event_type.event_key}] "
                f"[tone={context.event_type.tone.value}] "
                f"[relation_hint={context.event_type.relation_hint.value}] "
                f"{event_text}"
            ),
        )


__all__ = ["RandomMinorEventService"]
