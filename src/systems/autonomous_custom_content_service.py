from __future__ import annotations

import json
import random

from src.classes.core.avatar import Avatar
from src.classes.event import Event
from src.classes.story_event_service import StoryEventKind, StoryEventService
from src.classes.items.auxiliary import auxiliaries_by_id
from src.classes.items.weapon import weapons_by_id
from src.classes.technique import techniques_by_id
from src.i18n import t
from src.run.log import get_logger
from src.server.services.custom_content_service import (
    create_custom_content_from_draft,
    generate_custom_content_draft,
)
from src.utils.config import CONFIG


AUTONOMOUS_CREATION_CATEGORIES = ("technique", "weapon", "auxiliary")


class AutonomousCustomContentService:
    @classmethod
    def should_trigger(cls, avatar: Avatar) -> bool:
        base_prob = float(getattr(CONFIG.world, "autonomous_creation_probability", 0.0))
        if base_prob <= 0.0:
            return False
        if not avatar.can_trigger_world_event:
            return False
        return random.random() < base_prob

    @classmethod
    async def try_create_events(cls, avatar: Avatar, world) -> list[Event]:
        category = random.choice(AUTONOMOUS_CREATION_CATEGORIES)
        realm = avatar.cultivation_progress.realm if category in {"weapon", "auxiliary"} else None
        user_prompt = cls._build_user_prompt(avatar, category)

        try:
            draft = await generate_custom_content_draft(category, realm, user_prompt)
            payload = create_custom_content_from_draft(category, draft)
        except Exception as exc:
            get_logger().logger.error(
                "Failed autonomous custom creation for %s: %s",
                avatar.name,
                exc,
            )
            return []

        return await cls._apply_created_content(
            avatar=avatar,
            world=world,
            category=category,
            payload=payload,
        )

    @staticmethod
    def _build_user_prompt(avatar: Avatar, category: str) -> str:
        category_label_map = {
            "technique": "功法",
            "weapon": "兵器",
            "auxiliary": "辅助装备",
        }
        avatar_info = json.dumps(avatar.get_expanded_info(detailed=True), ensure_ascii=False)
        return (
            f"以下是这个角色的完整信息，请基于这些信息，为他创作一个新的{category_label_map[category]}。\n"
            "不需要追求全面，请你自行判断这个角色最独特、最值得抓住的一个方面，并围绕这一个方面来设计。\n"
            "尽量突出角色自己的经历、身份、性格、已有功法或装备风格，但不要面面俱到。\n\n"
            f"角色完整信息：\n{avatar_info}"
        )

    @classmethod
    async def _apply_created_content(
        cls,
        *,
        avatar: Avatar,
        world,
        category: str,
        payload: dict,
    ) -> list[Event]:
        events: list[Event] = []
        item_name = str(payload.get("name", "") or "")

        creation_event = Event(
            month_stamp=world.month_stamp,
            content=cls._build_creation_text(avatar.name, category, item_name),
            related_avatars=[avatar.id],
            is_major=True,
        )
        events.append(creation_event)

        if category == "technique":
            technique = techniques_by_id.get(int(payload["id"]))
            if technique is None:
                return events
            avatar.technique = technique
            avatar.recalc_effects()
        elif category == "weapon":
            weapon = weapons_by_id.get(int(payload["id"]))
            if weapon is None:
                return events
            old_name, refund = cls._force_equip_weapon_and_sell_old(avatar, weapon.instantiate())
            events.append(cls._build_exchange_event(world, avatar.id, item_name, old_name, refund, "weapon"))
        else:
            auxiliary = auxiliaries_by_id.get(int(payload["id"]))
            if auxiliary is None:
                return events
            old_name, refund = cls._force_equip_auxiliary_and_sell_old(avatar, auxiliary.instantiate())
            events.append(cls._build_exchange_event(world, avatar.id, item_name, old_name, refund, "auxiliary"))

        story_event = await StoryEventService.maybe_create_story(
            kind=StoryEventKind.AUTONOMOUS_CREATION,
            month_stamp=world.month_stamp,
            start_text=creation_event.content,
            result_text=" ".join(event.content for event in events),
            actors=[avatar],
            related_avatar_ids=[avatar.id],
            allow_relation_changes=False,
        )
        if story_event is not None:
            events.append(story_event)
        return events

    @staticmethod
    def _build_creation_text(avatar_name: str, category: str, item_name: str) -> str:
        if category == "technique":
            return t("{avatar} self-created technique '{item}'", avatar=avatar_name, item=item_name)
        if category == "weapon":
            return t("{avatar} self-created weapon '{item}'", avatar=avatar_name, item=item_name)
        return t("{avatar} self-created auxiliary equipment '{item}'", avatar=avatar_name, item=item_name)

    @staticmethod
    def _build_exchange_event(world, avatar_id: str, item_name: str, old_name: str | None, refund: int, kind: str) -> Event:
        if old_name:
            content = t(
                "Equipped newly created {kind} '{item}', sold old equipment '{old_item}' for {refund} spirit stones",
                kind=t("weapon") if kind == "weapon" else t("auxiliary"),
                item=item_name,
                old_item=old_name,
                refund=refund,
            )
        else:
            content = t(
                "Equipped newly created {kind} '{item}'",
                kind=t("weapon") if kind == "weapon" else t("auxiliary"),
                item=item_name,
            )
        return Event(
            month_stamp=world.month_stamp,
            content=content,
            related_avatars=[avatar_id],
            is_major=True,
        )

    @staticmethod
    def _force_equip_weapon_and_sell_old(avatar: Avatar, new_weapon) -> tuple[str | None, int]:
        old_name = None
        refund = 0
        if avatar.weapon is not None:
            old_name = avatar.weapon.name
            refund = avatar.sell_weapon(avatar.weapon)
        avatar.change_weapon(new_weapon)
        return old_name, refund

    @staticmethod
    def _force_equip_auxiliary_and_sell_old(avatar: Avatar, new_auxiliary) -> tuple[str | None, int]:
        old_name = None
        refund = 0
        if avatar.auxiliary is not None:
            old_name = avatar.auxiliary.name
            refund = avatar.sell_auxiliary(avatar.auxiliary)
        avatar.change_auxiliary(new_auxiliary)
        return old_name, refund


async def try_trigger_autonomous_custom_creation(avatar: Avatar, world) -> list[Event]:
    if not AutonomousCustomContentService.should_trigger(avatar):
        return []
    return await AutonomousCustomContentService.try_create_events(avatar, world)
