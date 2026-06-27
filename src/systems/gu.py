from __future__ import annotations

from dataclasses import dataclass
import random
from typing import TYPE_CHECKING, Any

from src.classes.event import Event
from src.classes.relation.relations import add_friendliness
from src.i18n import t

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.items.auxiliary import Auxiliary


INFLICT_GU_ACTION = "InflictGu"

GU_QIANXIN = "qianxin"
GU_SHIXUE = "shixue"
GU_SHIYUAN = "shiyuan"
GU_LUANXIN = "luanxin"

GU_EFFECT_SOURCE_PREFIX = "effect_source_gu_"
GU_MIN_SUCCESS_RATE = 0.15
GU_MAX_SUCCESS_RATE = 0.90
GU_FAIL_DETECTED_RATE = 0.50


@dataclass(frozen=True)
class GuTypeConfig:
    key: str
    name_id: str
    base_duration_months: int


@dataclass(frozen=True)
class GuToolConfig:
    item_id: int
    base_success_rate: float


GU_TYPES: dict[str, GuTypeConfig] = {
    GU_QIANXIN: GuTypeConfig(GU_QIANXIN, "gu_qianxin_name", 24),
    GU_SHIXUE: GuTypeConfig(GU_SHIXUE, "gu_shixue_name", 18),
    GU_SHIYUAN: GuTypeConfig(GU_SHIYUAN, "gu_shiyuan_name", 24),
    GU_LUANXIN: GuTypeConfig(GU_LUANXIN, "gu_luanxin_name", 18),
}


GU_TOOL_CONFIGS: dict[int, GuToolConfig] = {
    2071: GuToolConfig(item_id=2071, base_success_rate=0.45),
    2072: GuToolConfig(item_id=2072, base_success_rate=0.52),
    2073: GuToolConfig(item_id=2073, base_success_rate=0.60),
    2074: GuToolConfig(item_id=2074, base_success_rate=0.68),
}


def is_valid_gu_type(gu_type: str) -> bool:
    return str(gu_type or "").strip().lower() in GU_TYPES


def normalize_gu_type(gu_type: str) -> str:
    return str(gu_type or "").strip().lower()


def get_gu_type_name(gu_type: str) -> str:
    key = normalize_gu_type(gu_type)
    cfg = GU_TYPES.get(key)
    return t(cfg.name_id) if cfg else str(gu_type)


def get_gu_type_options() -> list[dict[str, Any]]:
    return [
        {
            "value": cfg.key,
            "id": cfg.key,
            "name": t(cfg.name_id),
        }
        for cfg in GU_TYPES.values()
    ]


def get_gu_tool_config(auxiliary: "Auxiliary | None") -> GuToolConfig | None:
    if auxiliary is None:
        return None
    try:
        item_id = int(getattr(auxiliary, "id", 0) or 0)
    except (TypeError, ValueError):
        return None
    return GU_TOOL_CONFIGS.get(item_id)


def is_gu_tool(auxiliary: "Auxiliary | None") -> bool:
    return get_gu_tool_config(auxiliary) is not None


def has_gu_permission(avatar: "Avatar") -> bool:
    legal = getattr(avatar, "effects", {}).get("legal_actions", [])
    return INFLICT_GU_ACTION in legal


def compute_gu_success_rate(caster: "Avatar", target: "Avatar") -> float:
    tool_cfg = get_gu_tool_config(getattr(caster, "auxiliary", None))
    if tool_cfg is None:
        return 0.0

    caster_effects = getattr(caster, "effects", {})
    target_effects = getattr(target, "effects", {})
    rate = (
        tool_cfg.base_success_rate
        + float(caster_effects.get("extra_gu_success_rate", 0.0) or 0.0)
        - float(target_effects.get("extra_gu_resistance_rate", 0.0) or 0.0)
    )
    return max(GU_MIN_SUCCESS_RATE, min(GU_MAX_SUCCESS_RATE, rate))


def build_gu_effect(caster: "Avatar", gu_type: str) -> dict[str, Any]:
    key = normalize_gu_type(gu_type)
    cfg = GU_TYPES[key]
    extra_duration = int(getattr(caster, "effects", {}).get("extra_gu_duration_months", 0) or 0)
    return {
        "source": f"{GU_EFFECT_SOURCE_PREFIX}{key}",
        "gu_type": key,
        "caster_id": str(caster.id),
        "start_month": int(caster.world.month_stamp),
        "duration": max(1, cfg.base_duration_months + extra_duration),
        "last_tick_month": int(caster.world.month_stamp) - 1,
        "effects": {},
    }


def apply_gu_effect(target: "Avatar", effect: dict[str, Any]) -> None:
    target.temporary_effects.append(effect)


def roll_gu_success(caster: "Avatar", target: "Avatar") -> tuple[bool, float]:
    rate = compute_gu_success_rate(caster, target)
    return random.random() < rate, rate


def roll_gu_failure_detected() -> bool:
    return random.random() < GU_FAIL_DETECTED_RATE


def process_avatar_gu_effects(avatar: "Avatar", current_month: int) -> list[Event]:
    events: list[Event] = []
    for effect in list(getattr(avatar, "temporary_effects", []) or []):
        gu_type = normalize_gu_type(str(effect.get("gu_type", "")))
        if gu_type not in GU_TYPES:
            continue
        start_month = _int_or_default(effect.get("start_month"), current_month)
        duration = _int_or_default(effect.get("duration"), 0)
        if current_month >= start_month + duration:
            continue
        last_tick_month = _int_or_default(effect.get("last_tick_month"), start_month - 1)
        if last_tick_month >= current_month:
            continue

        event = _tick_gu_effect(avatar, effect, gu_type, current_month)
        effect["last_tick_month"] = current_month
        if event is not None:
            events.append(event)
    return events


def _int_or_default(value: Any, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _tick_gu_effect(
    avatar: "Avatar",
    effect: dict[str, Any],
    gu_type: str,
    current_month: int,
) -> Event | None:
    if gu_type == GU_QIANXIN:
        return _tick_qianxin(avatar, effect, current_month)
    if gu_type == GU_SHIXUE:
        return _tick_shixue(avatar, current_month)
    if gu_type == GU_SHIYUAN:
        return _tick_shiyuan(avatar, current_month)
    if gu_type == GU_LUANXIN:
        return _tick_luanxin(avatar, current_month)
    return None


def _find_caster(avatar: "Avatar", effect: dict[str, Any]) -> "Avatar | None":
    caster_id = str(effect.get("caster_id", "") or "")
    manager = getattr(getattr(avatar, "world", None), "avatar_manager", None)
    if manager is None or not caster_id:
        return None
    if hasattr(manager, "get_avatar"):
        return manager.get_avatar(caster_id)
    return getattr(manager, "avatars", {}).get(caster_id)


def _tick_qianxin(avatar: "Avatar", effect: dict[str, Any], current_month: int) -> Event | None:
    caster = _find_caster(avatar, effect)
    if caster is None or getattr(caster, "is_dead", False):
        return None
    add_friendliness(avatar, caster, 1, current_month=current_month)
    return None


def _tick_shixue(avatar: "Avatar", current_month: int) -> Event | None:
    damage = max(1, int(getattr(avatar.hp, "max", 0) * 0.02))
    avatar.hp.reduce(damage)
    if current_month % 6 != 0:
        return None
    return Event(
        avatar.world.month_stamp,
        t("{target}'s {gu_name} took effect, losing {amount} HP.",
          target=avatar.name, gu_name=get_gu_type_name(GU_SHIXUE), amount=damage),
        related_avatars=[avatar.id],
    )


def _tick_shiyuan(avatar: "Avatar", current_month: int) -> Event | None:
    current_exp = int(getattr(avatar.cultivation_progress, "exp", 0) or 0)
    loss = min(current_exp, 50)
    avatar.cultivation_progress.exp = current_exp - loss
    if current_month % 6 != 0:
        return None
    return Event(
        avatar.world.month_stamp,
        t("{target}'s {gu_name} took effect, losing {amount} cultivation experience.",
          target=avatar.name, gu_name=get_gu_type_name(GU_SHIYUAN), amount=loss),
        related_avatars=[avatar.id],
    )


def _tick_luanxin(avatar: "Avatar", current_month: int) -> Event | None:
    if random.random() >= 0.30:
        return None
    current_exp = int(getattr(avatar.cultivation_progress, "exp", 0) or 0)
    loss = min(current_exp, 80)
    avatar.cultivation_progress.exp = current_exp - loss
    return Event(
        avatar.world.month_stamp,
        t("{target}'s {gu_name} took effect, losing {amount} cultivation experience.",
          target=avatar.name, gu_name=get_gu_type_name(GU_LUANXIN), amount=loss),
        related_avatars=[avatar.id],
    )
