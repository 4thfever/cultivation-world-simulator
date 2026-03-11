from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from src.classes.core.world import World
from src.classes.event import Event
from src.classes.sect_effect import EXTRA_INCOME_PER_TILE
from src.classes.language import LanguageType, language_manager
from src.run.log import get_logger
from src.systems.sect_relations import SectRelationReason
from src.utils.config import CONFIG
from src.utils.df import game_configs, get_float, get_int, get_str
from src.utils.llm.client import call_llm_with_task_name


EVENT_TYPE_RELATION_UP = "relation_up"
EVENT_TYPE_RELATION_DOWN = "relation_down"
EVENT_TYPE_MAGIC_STONE_UP = "magic_stone_up"
EVENT_TYPE_MAGIC_STONE_DOWN = "magic_stone_down"
EVENT_TYPE_INCOME_UP = "income_up"
EVENT_TYPE_INCOME_DOWN = "income_down"

RELATION_EVENT_TYPES = {EVENT_TYPE_RELATION_UP, EVENT_TYPE_RELATION_DOWN}
MAGIC_STONE_EVENT_TYPES = {EVENT_TYPE_MAGIC_STONE_UP, EVENT_TYPE_MAGIC_STONE_DOWN}
INCOME_EVENT_TYPES = {EVENT_TYPE_INCOME_UP, EVENT_TYPE_INCOME_DOWN}
ALL_EVENT_TYPES = RELATION_EVENT_TYPES | MAGIC_STONE_EVENT_TYPES | INCOME_EVENT_TYPES


@dataclass(frozen=True)
class SectRandomEventConfig:
    event_type: str
    value: float
    duration_months: int


def _pick_record(records: list[dict]) -> Optional[dict]:
    if not records:
        return None
    weights = [max(0.0, get_float(row, "weight", 1.0)) for row in records]
    if not any(weights):
        return random.choice(records)
    return random.choices(records, weights=weights, k=1)[0]


def _collect_active_sects(world: World) -> list:
    sects = getattr(world, "existed_sects", []) or []
    return [s for s in sects if getattr(s, "is_active", True)]


def _parse_event_config(record: dict) -> SectRandomEventConfig:
    legacy_relation_delta = get_str(record, "relation_delta")
    if legacy_relation_delta and legacy_relation_delta not in {"0", "0.0"}:
        raise ValueError(
            "Legacy field relation_delta is not supported in sect_random_event.csv. "
            "Use event_type=relation_up/relation_down with value instead."
        )

    event_type = get_str(record, "event_type").lower()
    if event_type not in ALL_EVENT_TYPES:
        raise ValueError(f"Invalid sect_random_event event_type={event_type!r}.")

    value = abs(get_float(record, "value", 0.0))
    if value <= 0:
        raise ValueError(f"Invalid sect_random_event value={value}, must be > 0.")

    duration = get_int(record, "duration_months", 0)
    if event_type in RELATION_EVENT_TYPES or event_type in INCOME_EVENT_TYPES:
        if duration <= 0:
            raise ValueError(
                f"Invalid sect_random_event duration_months={duration}, "
                f"event_type={event_type} requires duration_months > 0."
            )

    return SectRandomEventConfig(
        event_type=event_type,
        value=value,
        duration_months=duration,
    )


def _pick_participants(active_sects: list, event_type: str):
    if event_type in RELATION_EVENT_TYPES:
        if len(active_sects) < 2:
            return None, None
        return random.sample(active_sects, 2)
    if len(active_sects) < 1:
        return None, None
    return random.choice(active_sects), None


def _lang() -> str:
    return str(language_manager)


def _fallback_reason(event_type: str) -> str:
    lang = _lang()
    if lang == LanguageType.ZH_CN.value:
        return {
            EVENT_TYPE_RELATION_UP: "边界协约暂获共识",
            EVENT_TYPE_RELATION_DOWN: "边界利益冲突升级",
            EVENT_TYPE_MAGIC_STONE_UP: "宗门经营获得额外回报",
            EVENT_TYPE_MAGIC_STONE_DOWN: "宗门事务出现额外开销",
            EVENT_TYPE_INCOME_UP: "新商路带来稳定收益",
            EVENT_TYPE_INCOME_DOWN: "外部压力压缩了收益",
        }[event_type]
    if lang == LanguageType.ZH_TW.value:
        return {
            EVENT_TYPE_RELATION_UP: "邊界協約暫獲共識",
            EVENT_TYPE_RELATION_DOWN: "邊界利益衝突升級",
            EVENT_TYPE_MAGIC_STONE_UP: "宗門營運獲得額外回報",
            EVENT_TYPE_MAGIC_STONE_DOWN: "宗門事務出現額外開支",
            EVENT_TYPE_INCOME_UP: "新商路帶來穩定收益",
            EVENT_TYPE_INCOME_DOWN: "外部壓力壓縮了收益",
        }[event_type]
    return {
        EVENT_TYPE_RELATION_UP: "a temporary border consensus",
        EVENT_TYPE_RELATION_DOWN: "escalating border conflicts",
        EVENT_TYPE_MAGIC_STONE_UP: "unexpected operational gains",
        EVENT_TYPE_MAGIC_STONE_DOWN: "unexpected operational costs",
        EVENT_TYPE_INCOME_UP: "a newly opened trade route",
        EVENT_TYPE_INCOME_DOWN: "external pressure on revenue",
    }[event_type]


async def _generate_reason_fragment(
    *,
    event_type: str,
    sect_a_name: str,
    sect_b_name: str,
    value: float,
    duration_months: int,
) -> str:
    infos = {
        "language": _lang(),
        "event_type": event_type,
        "sect_a_name": sect_a_name,
        "sect_b_name": sect_b_name,
        "value": value,
        "duration_months": duration_months,
        "target_chars": int(getattr(CONFIG.sect, "random_event_reason_max_chars", 20)),
    }

    try:
        result = await call_llm_with_task_name(
            task_name="sect_random_event_reason",
            template_path=CONFIG.paths.templates / "sect_random_event.txt",
            infos=infos,
        )
        if isinstance(result, dict):
            reason = str(result.get("reason_fragment", "")).strip()
            if reason:
                return reason
    except Exception as exc:
        get_logger().logger.error(
            "Failed to generate sect random event reason for sects %s and %s: %s",
            sect_a_name,
            sect_b_name,
            exc,
        )

    return _fallback_reason(event_type)


def _fmt_int(v: float) -> int:
    return int(round(v))


def _build_event_text(
    *,
    event_type: str,
    sect_a_name: str,
    sect_b_name: Optional[str],
    reason_fragment: str,
    value: float,
    duration_months: int,
) -> str:
    lang = _lang()

    if lang == LanguageType.ZH_CN.value:
        if event_type == EVENT_TYPE_RELATION_UP:
            return f"因{reason_fragment}，{sect_a_name}与{sect_b_name}关系改善（+{_fmt_int(value)}，持续{duration_months}个月）。"
        if event_type == EVENT_TYPE_RELATION_DOWN:
            return f"因{reason_fragment}，{sect_a_name}与{sect_b_name}关系恶化（-{_fmt_int(value)}，持续{duration_months}个月）。"
        if event_type == EVENT_TYPE_MAGIC_STONE_UP:
            return f"因{reason_fragment}，{sect_a_name}获得灵石+{_fmt_int(value)}。"
        if event_type == EVENT_TYPE_MAGIC_STONE_DOWN:
            return f"因{reason_fragment}，{sect_a_name}损失灵石-{_fmt_int(value)}。"
        if event_type == EVENT_TYPE_INCOME_UP:
            return f"因{reason_fragment}，{sect_a_name}每地块年收入修正+{value:.1f}（持续{duration_months}个月）。"
        return f"因{reason_fragment}，{sect_a_name}每地块年收入修正-{value:.1f}（持续{duration_months}个月）。"

    if lang == LanguageType.ZH_TW.value:
        if event_type == EVENT_TYPE_RELATION_UP:
            return f"因{reason_fragment}，{sect_a_name}與{sect_b_name}關係改善（+{_fmt_int(value)}，持續{duration_months}個月）。"
        if event_type == EVENT_TYPE_RELATION_DOWN:
            return f"因{reason_fragment}，{sect_a_name}與{sect_b_name}關係惡化（-{_fmt_int(value)}，持續{duration_months}個月）。"
        if event_type == EVENT_TYPE_MAGIC_STONE_UP:
            return f"因{reason_fragment}，{sect_a_name}獲得靈石+{_fmt_int(value)}。"
        if event_type == EVENT_TYPE_MAGIC_STONE_DOWN:
            return f"因{reason_fragment}，{sect_a_name}損失靈石-{_fmt_int(value)}。"
        if event_type == EVENT_TYPE_INCOME_UP:
            return f"因{reason_fragment}，{sect_a_name}每地塊年收入修正+{value:.1f}（持續{duration_months}個月）。"
        return f"因{reason_fragment}，{sect_a_name}每地塊年收入修正-{value:.1f}（持續{duration_months}個月）。"

    if event_type == EVENT_TYPE_RELATION_UP:
        return (
            f"Because {reason_fragment}, relations between {sect_a_name} and {sect_b_name} improved "
            f"(+{_fmt_int(value)} for {duration_months} months)."
        )
    if event_type == EVENT_TYPE_RELATION_DOWN:
        return (
            f"Because {reason_fragment}, relations between {sect_a_name} and {sect_b_name} worsened "
            f"(-{_fmt_int(value)} for {duration_months} months)."
        )
    if event_type == EVENT_TYPE_MAGIC_STONE_UP:
        return f"Because {reason_fragment}, {sect_a_name} gained +{_fmt_int(value)} magic stones."
    if event_type == EVENT_TYPE_MAGIC_STONE_DOWN:
        return f"Because {reason_fragment}, {sect_a_name} lost -{_fmt_int(value)} magic stones."
    if event_type == EVENT_TYPE_INCOME_UP:
        return (
            f"Because {reason_fragment}, {sect_a_name} gained +{value:.1f} extra income per tile "
            f"for {duration_months} months."
        )
    return (
        f"Because {reason_fragment}, {sect_a_name} suffered -{value:.1f} income per tile "
        f"for {duration_months} months."
    )


async def try_trigger_sect_random_event(world: World) -> Optional[Event]:
    world.prune_expired_sect_relation_modifiers(int(world.month_stamp))

    base_prob = float(getattr(CONFIG.sect, "random_event_prob_per_month", 0.0))
    if base_prob <= 0.0:
        return None
    if random.random() >= base_prob:
        return None

    active_sects = _collect_active_sects(world)
    if not active_sects:
        return None

    record = _pick_record(game_configs.get("sect_random_event", []))
    if not record:
        return None

    cfg = _parse_event_config(record)

    sect_a, sect_b = _pick_participants(active_sects, cfg.event_type)
    if sect_a is None:
        return None
    if cfg.event_type in RELATION_EVENT_TYPES and sect_b is None:
        return None

    reason_fragment = await _generate_reason_fragment(
        event_type=cfg.event_type,
        sect_a_name=sect_a.name,
        sect_b_name=sect_b.name if sect_b else "",
        value=cfg.value,
        duration_months=cfg.duration_months,
    )

    if cfg.event_type == EVENT_TYPE_RELATION_UP and sect_b is not None:
        world.add_sect_relation_modifier(
            sect_a_id=sect_a.id,
            sect_b_id=sect_b.id,
            delta=_fmt_int(cfg.value),
            duration=cfg.duration_months,
            reason=SectRelationReason.RANDOM_EVENT.value,
            meta={"cause": reason_fragment},
        )
    elif cfg.event_type == EVENT_TYPE_RELATION_DOWN and sect_b is not None:
        world.add_sect_relation_modifier(
            sect_a_id=sect_a.id,
            sect_b_id=sect_b.id,
            delta=-_fmt_int(cfg.value),
            duration=cfg.duration_months,
            reason=SectRelationReason.RANDOM_EVENT.value,
            meta={"cause": reason_fragment},
        )
    elif cfg.event_type == EVENT_TYPE_MAGIC_STONE_UP:
        sect_a.magic_stone += _fmt_int(cfg.value)
    elif cfg.event_type == EVENT_TYPE_MAGIC_STONE_DOWN:
        sect_a.magic_stone -= _fmt_int(cfg.value)
    elif cfg.event_type == EVENT_TYPE_INCOME_UP:
        sect_a.add_temporary_sect_effect(
            effects={EXTRA_INCOME_PER_TILE: cfg.value},
            start_month=int(world.month_stamp),
            duration=cfg.duration_months,
            source="sect_random_event",
        )
    elif cfg.event_type == EVENT_TYPE_INCOME_DOWN:
        sect_a.add_temporary_sect_effect(
            effects={EXTRA_INCOME_PER_TILE: -cfg.value},
            start_month=int(world.month_stamp),
            duration=cfg.duration_months,
            source="sect_random_event",
        )

    related_sects = [sect_a.id]
    if sect_b is not None:
        related_sects.append(sect_b.id)

    event_text = _build_event_text(
        event_type=cfg.event_type,
        sect_a_name=sect_a.name,
        sect_b_name=sect_b.name if sect_b else None,
        reason_fragment=reason_fragment,
        value=cfg.value,
        duration_months=cfg.duration_months,
    )

    return Event(
        month_stamp=world.month_stamp,
        content=event_text,
        related_sects=related_sects,
        is_major=False,
        is_story=False,
    )
