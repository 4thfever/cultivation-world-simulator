from __future__ import annotations

import json
import random
from typing import Any

from src.classes.core.avatar import Avatar
from src.classes.core.world import World
from src.classes.event import Event
from src.i18n import t
from src.run.log import get_logger
from src.utils.config import CONFIG
from src.utils.llm.client import call_llm_with_task_name


FATE_REVELATION_EVENT_TYPE = "fate_revelation"
FATE_REVELATION_TEMPLATE_NAME = "fate_revelation.txt"

_BANNED_ORACLE_FRAGMENTS = (
    "预示",
    "意味着",
    "代表",
    "说明",
    "将会",
    "必将",
    "注定",
    "系统",
    "属性",
    "概率",
    "奖励",
    "突破境界",
    "成仙",
    "飞升",
    "称帝",
    "必死",
    "复仇成功",
)

_BANNED_ORACLE_MARKS = ("：", ":", "（", "）", "(", ")")


def _location_name(avatar: Avatar) -> str:
    if avatar.tile and avatar.tile.region:
        return avatar.tile.region.name
    return t("unknown location")


def _current_phenomenon_info(world: World) -> str:
    phenomenon = getattr(world, "current_phenomenon", None)
    if phenomenon is None:
        return t("None")
    name = str(getattr(phenomenon, "name", "") or "")
    desc = str(getattr(phenomenon, "desc", "") or "")
    return f"{name}: {desc}".strip(": ")


def _to_json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def is_valid_oracle_text(text: str) -> bool:
    text = str(text or "").strip()
    if not text:
        return False
    if len(text) > 48:
        return False
    if any(fragment in text for fragment in _BANNED_ORACLE_FRAGMENTS):
        return False
    if any(mark in text for mark in _BANNED_ORACLE_MARKS):
        return False
    return True


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _build_fallback_event_text(trigger_text: str, oracle_text: str) -> str:
    return f"{trigger_text}冥冥中，一句命格浮上心头：『{oracle_text}』"


def _build_prompt_infos(avatar: Avatar, world: World) -> dict:
    location_name = _location_name(avatar)
    return {
        "avatar_info": _to_json_text(avatar.get_expanded_info(detailed=True)),
        "location": location_name,
        "current_action": avatar.current_action_name,
        "world_info": _to_json_text(world.get_info(avatar=avatar, detailed=True)),
        "current_phenomenon": _current_phenomenon_info(world),
    }


async def _generate_fate_revelation(avatar: Avatar, world: World) -> dict | None:
    try:
        result = await call_llm_with_task_name(
            task_name="fate_revelation",
            template_path=CONFIG.paths.templates / FATE_REVELATION_TEMPLATE_NAME,
            infos=_build_prompt_infos(avatar, world),
        )
    except Exception as exc:
        get_logger().logger.error(
            "Failed to generate fate revelation for %s: %s",
            avatar.name,
            exc,
            exc_info=True,
        )
        return None

    trigger_text = _normalize_text(result.get("trigger_text"))
    oracle_text = _normalize_text(result.get("oracle_text"))
    event_text = _normalize_text(result.get("event_text"))

    if not trigger_text or not is_valid_oracle_text(oracle_text):
        return None
    if not event_text:
        event_text = _build_fallback_event_text(trigger_text, oracle_text)

    location_name = _location_name(avatar)
    return {
        "trigger_text": trigger_text,
        "oracle_text": oracle_text,
        "event_text": event_text,
        "location": location_name,
    }


def should_trigger_fate_revelation(avatar: Avatar) -> bool:
    if getattr(avatar, "fate_revelation", None) is not None:
        return False
    if not avatar.can_trigger_world_event:
        return False

    base_prob = float(getattr(CONFIG.world, "fate_revelation_probability", 0.0005))
    if base_prob <= 0.0:
        return False
    return random.random() < base_prob


async def try_trigger_fate_revelation(avatar: Avatar, world: World) -> list[Event]:
    if not should_trigger_fate_revelation(avatar):
        return []

    revelation = await _generate_fate_revelation(avatar, world)
    if revelation is None:
        return []

    avatar.fate_revelation = {
        "trigger_text": revelation["trigger_text"],
        "oracle_text": revelation["oracle_text"],
        "revealed_month": int(world.month_stamp),
        "location": revelation["location"],
    }

    return [
        Event(
            world.month_stamp,
            revelation["event_text"],
            related_avatars=[avatar.id],
            is_major=True,
            is_story=False,
            event_type=FATE_REVELATION_EVENT_TYPE,
        )
    ]


__all__ = [
    "FATE_REVELATION_EVENT_TYPE",
    "is_valid_oracle_text",
    "should_trigger_fate_revelation",
    "try_trigger_fate_revelation",
]
