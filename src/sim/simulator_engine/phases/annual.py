from __future__ import annotations

import asyncio

from src.classes.event import Event
from src.classes.sect_decider import SectDecider
from src.classes.sect_thinker import SectThinker
from src.i18n import t
from src.run.log import get_logger
from src.systems.time import Month
from src.utils.config import CONFIG


def _should_run_sect_decision_cycle(world) -> bool:
    current_year = int(world.month_stamp.get_year())
    start_year = int(getattr(world, "start_year", current_year))
    interval = int(getattr(CONFIG.sect, "decision_interval_years", 1))
    if interval <= 0 or current_year < start_year:
        return False
    return (current_year - start_year) % interval == 0


def _should_run_sect_thinking_cycle(world) -> bool:
    current_year = int(world.month_stamp.get_year())
    start_year = int(getattr(world, "start_year", current_year))
    interval = SectThinker.get_thinking_interval_years()
    if interval <= 0 or current_year < start_year:
        return False
    return (current_year - start_year) % interval == 0


async def run_annual_maintenance(simulator, ctx) -> None:
    # 年度维护统一收口在这里，避免一月专属逻辑散落在 step() 的多个分支里。
    # 顺序上保持：
    # 1. 刷新排行榜
    # 2. 更新宗门状态
    # 3. 执行配置驱动的宗门决策周期
    # 4. 生成宗门周期思考
    # 5. 清理长期死亡角色
    if not ctx.is_january:
        return

    world = simulator.world
    world.ranking_manager.update_rankings_with_world(world, ctx.living_avatars)

    sect_events = simulator.sect_manager.update_sects()
    if sect_events:
        ctx.events.extend(sect_events)

    ctx.events.extend(await phase_sect_periodic_decision(simulator))
    ctx.events.extend(await phase_sect_periodic_thinking(simulator))

    cleaned_count = world.avatar_manager.cleanup_long_dead_avatars(
        world.month_stamp,
        CONFIG.world.long_dead_cleanup_years,
    )
    if cleaned_count > 0:
        get_logger().logger.info("Cleaned up %s long-dead avatars.", cleaned_count)


async def phase_sect_periodic_decision(simulator) -> list[Event]:
    world = simulator.world
    if world.month_stamp.get_month() != Month.JANUARY:
        return []
    if not _should_run_sect_decision_cycle(world):
        return []

    sect_context = getattr(world, "sect_context", None)
    active_sects = (
        sect_context.get_active_sects()
        if sect_context is not None
        else (getattr(world, "existed_sects", []) or [])
    )
    if not active_sects:
        return []

    event_storage = getattr(getattr(world, "event_manager", None), "_storage", None)
    if event_storage is None:
        return []

    from src.classes.core.sect import get_sect_decision_context

    events: list[Event] = []
    for sect in active_sects:
        try:
            ctx = get_sect_decision_context(
                sect=sect,
                world=world,
                event_storage=event_storage,
            )
            result = await SectDecider.decide(sect, ctx, world)
            sect.last_decision_summary = result.summary_text
            events.extend(result.events)
            events.append(
                Event(
                    world.month_stamp,
                    result.summary_text,
                    related_sects=[int(sect.id)],
                    is_major=False,
                )
            )
        except Exception as exc:
            get_logger().logger.error(
                "Sect periodic decision failed for %s(%s): %s",
                getattr(sect, "name", "unknown"),
                getattr(sect, "id", "unknown"),
                exc,
                exc_info=True,
            )
    return events


async def phase_sect_periodic_thinking(simulator) -> list[Event]:
    world = simulator.world
    if world.month_stamp.get_month() != Month.JANUARY:
        return []
    if not _should_run_sect_thinking_cycle(world):
        return []

    sect_context = getattr(world, "sect_context", None)
    active_sects = (
        sect_context.get_active_sects()
        if sect_context is not None
        else (getattr(world, "existed_sects", []) or [])
    )
    if not active_sects:
        return []

    event_storage = getattr(getattr(world, "event_manager", None), "_storage", None)
    if event_storage is None:
        return []

    from src.classes.core.sect import get_sect_decision_context

    events: list[Event] = []

    async def _decide_one(sect):
        try:
            # 每个宗门单独构造决策上下文，并行生成 periodic_thinking。
            ctx = get_sect_decision_context(
                sect=sect,
                world=world,
                event_storage=event_storage,
            )
            sect.periodic_thinking = await SectThinker.think(
                sect,
                ctx,
                world,
                decision_summary=str(getattr(sect, "last_decision_summary", "") or ""),
            )
            events.append(
                Event(
                    world.month_stamp,
                    t(
                        "game.sect_thinking_event",
                        sect_name=sect.name,
                        thinking=sect.periodic_thinking,
                    ),
                    related_sects=[int(sect.id)],
                )
            )
        except Exception as exc:
            get_logger().logger.error(
                "Sect periodic thinking failed for %s(%s): %s",
                getattr(sect, "name", "unknown"),
                getattr(sect, "id", "unknown"),
                exc,
                exc_info=True,
            )

    await asyncio.gather(*[_decide_one(sect) for sect in active_sects])
    return events
