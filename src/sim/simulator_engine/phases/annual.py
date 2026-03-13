from __future__ import annotations

import asyncio

from src.classes.event import Event
from src.classes.sect_decider import SectDecider
from src.i18n import t
from src.run.log import get_logger
from src.systems.time import Month
from src.utils.config import CONFIG

SECT_THINKING_INTERVAL_YEARS = 5


async def run_annual_maintenance(simulator, ctx) -> None:
    # 年度维护统一收口在这里，避免一月专属逻辑散落在 step() 的多个分支里。
    # 顺序上保持：
    # 1. 刷新排行榜
    # 2. 更新宗门状态
    # 3. 生成宗门年度思考
    # 4. 清理长期死亡角色
    if not ctx.is_january:
        return

    world = simulator.world
    world.ranking_manager.update_rankings_with_world(world, ctx.living_avatars)

    sect_events = simulator.sect_manager.update_sects()
    if sect_events:
        ctx.events.extend(sect_events)

    ctx.events.extend(await phase_sect_yearly_thinking(simulator))

    cleaned_count = world.avatar_manager.cleanup_long_dead_avatars(
        world.month_stamp,
        CONFIG.game.long_dead_cleanup_years,
    )
    if cleaned_count > 0:
        get_logger().logger.info("Cleaned up %s long-dead avatars.", cleaned_count)


async def phase_sect_yearly_thinking(simulator) -> list[Event]:
    world = simulator.world
    if world.month_stamp.get_month() != Month.JANUARY:
        return []

    # 宗门年度思考不是每年都跑，而是相对 start_year 按固定间隔触发，
    # 这样可以控制 LLM 开销，也避免年更文本太密。
    current_year = int(world.month_stamp.get_year())
    start_year = int(getattr(world, "start_year", current_year))
    if current_year < start_year:
        return []
    if (current_year - start_year) % SECT_THINKING_INTERVAL_YEARS != 0:
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
            # 每个宗门单独构造决策上下文，并行生成 yearly_thinking。
            ctx = get_sect_decision_context(
                sect=sect,
                world=world,
                event_storage=event_storage,
            )
            sect.yearly_thinking = await SectDecider.decide(sect, ctx, world)
            events.append(
                Event(
                    world.month_stamp,
                    t(
                        "game.sect_thinking_event",
                        sect_name=sect.name,
                        thinking=sect.yearly_thinking,
                    ),
                    related_sects=[int(sect.id)],
                )
            )
        except Exception as exc:
            get_logger().logger.error(
                "Sect yearly thinking failed for %s(%s): %s",
                getattr(sect, "name", "unknown"),
                getattr(sect, "id", "unknown"),
                exc,
                exc_info=True,
            )

    await asyncio.gather(*[_decide_one(sect) for sect in active_sects])
    return events
