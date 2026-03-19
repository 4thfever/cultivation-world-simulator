from __future__ import annotations

import asyncio

from src.classes.celestial_phenomenon import get_random_celestial_phenomenon
from src.classes.core.avatar import Avatar
from src.classes.environment.region import CityRegion, CultivateRegion
from src.classes.event import Event
from src.classes.observe import get_avatar_observation_radius
from src.i18n import t
from src.systems.fortune import try_trigger_fortune, try_trigger_misfortune
from src.systems.random_minor_event import try_trigger_random_minor_event
from src.systems.sect_random_event import try_trigger_sect_random_event
from src.systems.time import Month


def phase_update_perception_and_knowledge(world, living_avatars: list[Avatar]) -> list[Event]:
    # 这个 phase 同时承担两件事：
    # 1. 根据观察半径刷新 known_regions
    # 2. 让尚无洞府的角色在观察到无主修炼地时尝试占据
    events: list[Event] = []
    avatars_with_home = set()

    cultivate_regions = [
        region
        for region in world.map.regions.values()
        if isinstance(region, CultivateRegion)
    ]
    for region in cultivate_regions:
        if region.host_avatar:
            avatars_with_home.add(region.host_avatar.id)

    for avatar in living_avatars:
        radius = get_avatar_observation_radius(avatar)

        # 先按包围盒缩小搜索范围，再用曼哈顿距离判断真正可见区域。
        start_x = max(0, avatar.pos_x - radius)
        end_x = min(world.map.width - 1, avatar.pos_x + radius)
        start_y = max(0, avatar.pos_y - radius)
        end_y = min(world.map.height - 1, avatar.pos_y + radius)

        observed_regions = set()
        for x in range(start_x, end_x + 1):
            for y in range(start_y, end_y + 1):
                if abs(x - avatar.pos_x) + abs(y - avatar.pos_y) > radius:
                    continue

                tile = world.map.get_tile(x, y)
                if tile.region:
                    observed_regions.add(tile.region)

        for region in observed_regions:
            avatar.known_regions.add(region.id)

            # 占地逻辑只允许“无主修炼区 + 角色尚无洞府”的组合进入。
            if not isinstance(region, CultivateRegion):
                continue
            if region.host_avatar is not None:
                continue
            if avatar.id in avatars_with_home:
                continue

            avatar.occupy_region(region)
            avatars_with_home.add(avatar.id)
            events.append(
                Event(
                    world.month_stamp,
                    t(
                        "{avatar_name} passed by {region_name}, found it ownerless, and occupied it.",
                        avatar_name=avatar.name,
                        region_name=region.name,
                    ),
                    related_avatars=[avatar.id],
                )
            )

    return events


async def phase_passive_effects(world, living_avatars: list[Avatar]) -> list[Event]:
    events: list[Event] = []
    for avatar in living_avatars:
        # 先处理本地状态副作用，再统一并发世界事件。
        avatar.process_elixir_expiration(int(world.month_stamp))
        avatar.update_time_effect()

    target_avatars = [avatar for avatar in living_avatars if avatar.can_trigger_world_event]
    results = await asyncio.gather(
        *[try_trigger_fortune(avatar) for avatar in target_avatars],
        *[try_trigger_misfortune(avatar) for avatar in target_avatars],
    )
    events.extend([event for result in results if result for event in result])
    return events


async def phase_random_minor_events(world, living_avatars: list[Avatar]) -> list[Event]:
    # 小随机事件和 fortune/misfortune 分开，便于分别控制概率与测试。
    target_avatars = [avatar for avatar in living_avatars if avatar.can_trigger_world_event]
    results = await asyncio.gather(
        *[try_trigger_random_minor_event(avatar, world) for avatar in target_avatars]
    )
    return [event for event in results if event]


async def phase_sect_random_event(world) -> list[Event]:
    event = await try_trigger_sect_random_event(world)
    return [event] if event else []


async def phase_process_gatherings(world) -> list[Event]:
    # 开局年份不触发聚会，避免世界尚未稳定时就生成大规模社交事件。
    if world.month_stamp.get_year() <= world.start_year:
        return []

    return await world.gathering_manager.check_and_run_all(world)


def phase_update_celestial_phenomenon(world) -> list[Event]:
    # 天象只在初始化时生成一次，或在每年一月检查是否到期切换。
    events: list[Event] = []
    current_year = world.month_stamp.get_year()
    current_month = world.month_stamp.get_month()

    should_update = False
    is_init = False

    if world.current_phenomenon is None:
        should_update = True
        is_init = True
    elif current_month == Month.JANUARY:
        elapsed_years = current_year - world.phenomenon_start_year
        if elapsed_years >= world.current_phenomenon.duration_years:
            should_update = True

    if not should_update:
        return events

    old_phenomenon = world.current_phenomenon
    new_phenomenon = get_random_celestial_phenomenon()
    if not new_phenomenon:
        return events

    # 切换世界级环境状态后，再补一条公开事件供前端和历史系统消费。
    world.current_phenomenon = new_phenomenon
    world.phenomenon_start_year = current_year

    if is_init:
        desc = t(
            "world_creation_phenomenon",
            name=new_phenomenon.name,
            desc=new_phenomenon.desc,
        )
    else:
        desc = t(
            "phenomenon_change",
            old_name=old_phenomenon.name,
            new_name=new_phenomenon.name,
            new_desc=new_phenomenon.desc,
        )

    events.append(Event(world.month_stamp, desc, related_avatars=None))
    return events


def phase_update_city_population(world) -> None:
    # 城市人口使用 logistic 公式按月自然变化。
    for region in world.map.regions.values():
        if isinstance(region, CityRegion):
            region.update_population_monthly()
