from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.classes.core.avatar import Avatar, Gender
from src.classes.environment.region import CityRegion
from src.classes.environment.tile import TileType
from src.classes.age import Age
from src.classes.alignment import Alignment
from src.classes.root import Root
from src.classes.items.weapon import Weapon
from src.classes.weapon_type import WeaponType
from src.systems.cultivation import Realm
from src.systems.opportunity import (
    OpportunityManager,
    OpportunityOutcome,
    OpportunityRecord,
    OpportunityTargetType,
    get_opportunity_context_text,
    load_opportunities,
    phase_check_opportunities,
    serialize_opportunities,
    try_generate_opportunity,
)
from src.systems.time import Month, Year, create_month_stamp
from src.systems.single_choice import ItemExchangeKind
from src.utils.id_generator import get_avatar_id


def _add_region(world, region_id: int, name: str, coords: list[tuple[int, int]]) -> CityRegion:
    region = CityRegion(id=region_id, name=name, desc="测试区域", cors=coords)
    world.map.regions[region_id] = region
    world.map.city_regions[region_id] = region
    world.map.region_cors[region_id] = coords
    for x, y in coords:
        tile = world.map.get_tile(x, y)
        tile.tile_type = TileType.CITY
        tile.region = region
    return region


def _place_avatar(avatar, x: int, y: int) -> None:
    avatar.pos_x = x
    avatar.pos_y = y
    avatar.tile = avatar.world.map.get_tile(x, y)


def _register(world, avatar) -> None:
    world.avatar_manager.register_avatar(avatar)


def _make_avatar(world, name: str, x: int, y: int) -> Avatar:
    avatar = Avatar(
        world=world,
        name=name,
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement, innate_max_lifespan=80),
        gender=Gender.MALE,
        pos_x=x,
        pos_y=y,
        root=Root.GOLD,
        personas=[],
        alignment=Alignment.RIGHTEOUS,
    )
    avatar.personas = []
    avatar.technique = None
    avatar.weapon = None
    avatar.auxiliary = None
    avatar.recalc_effects()
    _register(world, avatar)
    return avatar


def _record_for_region(avatar, region_id: int) -> OpportunityRecord:
    now = int(avatar.world.month_stamp)
    return OpportunityRecord(
        id="opp-region",
        avatar_id=avatar.id,
        target_type=OpportunityTargetType.REGION,
        target_id=str(region_id),
        hint_text="机缘感应：东南某处有缘法。",
        created_month=now - 1,
        expires_month=now + 60,
    )


@pytest.mark.asyncio
async def test_generate_opportunity_creates_hint_without_action_guidance(base_world, dummy_avatar, monkeypatch):
    _add_region(base_world, 101, "远城", [(5, 5)])
    base_world.avatar_manager.register_avatar(dummy_avatar)
    monkeypatch.setattr("src.systems.opportunity._opportunity_probability", lambda avatar: 1.0)
    monkeypatch.setattr("src.systems.opportunity._weighted_choice_from_mapping", lambda mapping, defaults: "region")

    events = await try_generate_opportunity(dummy_avatar, base_world)

    record = base_world.opportunity_manager.get_for_avatar(dummy_avatar.id)
    assert record is not None
    assert record.target_type == OpportunityTargetType.REGION
    assert len(events) == 1
    assert "机缘" in events[0].content
    assert "MoveTo" not in record.hint_text
    assert "suggested_search" not in get_opportunity_context_text(dummy_avatar)
    assert "risk_hint" not in get_opportunity_context_text(dummy_avatar)


@pytest.mark.asyncio
async def test_region_opportunity_resolves_on_any_target_region_tile(base_world, dummy_avatar, monkeypatch):
    _add_region(base_world, 101, "远城", [(5, 5), (5, 6)])
    base_world.avatar_manager.register_avatar(dummy_avatar)
    base_world.opportunity_manager.add(_record_for_region(dummy_avatar, 101))
    _place_avatar(dummy_avatar, 5, 6)
    monkeypatch.setattr("src.systems.opportunity._pick_outcome", lambda: OpportunityOutcome.EMPTY)
    monkeypatch.setattr("src.classes.story_event_service.StoryEventService.should_trigger", lambda kind: False)

    events = await phase_check_opportunities(base_world, [dummy_avatar])

    assert base_world.opportunity_manager.get_for_avatar(dummy_avatar.id) is None
    assert any("无所得" in event.content or "灵机" in event.content for event in events)
    assert base_world.opportunity_manager.is_in_cooldown(dummy_avatar.id, int(base_world.month_stamp) + 1)


@pytest.mark.asyncio
async def test_avatar_opportunity_resolves_when_target_is_observable(base_world, dummy_avatar, monkeypatch):
    target = _make_avatar(base_world, "Target", 2, 0)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    now = int(base_world.month_stamp)
    base_world.opportunity_manager.add(
        OpportunityRecord(
            id="opp-avatar",
            avatar_id=dummy_avatar.id,
            target_type=OpportunityTargetType.AVATAR,
            target_id=target.id,
            hint_text="机缘感应：近处某人有缘法。",
            created_month=now - 1,
            expires_month=now + 60,
        )
    )
    monkeypatch.setattr("src.systems.opportunity._pick_outcome", lambda: OpportunityOutcome.EMPTY)
    monkeypatch.setattr("src.classes.story_event_service.StoryEventService.should_trigger", lambda kind: False)

    events = await phase_check_opportunities(base_world, [dummy_avatar, target])

    assert base_world.opportunity_manager.get_for_avatar(dummy_avatar.id) is None
    assert events[0].related_avatars == [dummy_avatar.id, target.id]


@pytest.mark.asyncio
async def test_opportunity_expires_and_sets_dissipated_cooldown(base_world, dummy_avatar):
    _add_region(base_world, 101, "远城", [(5, 5)])
    base_world.avatar_manager.register_avatar(dummy_avatar)
    record = _record_for_region(dummy_avatar, 101)
    record.expires_month = int(base_world.month_stamp)
    base_world.opportunity_manager.add(record)

    events = await phase_check_opportunities(base_world, [dummy_avatar])

    assert base_world.opportunity_manager.get_for_avatar(dummy_avatar.id) is None
    assert "散去" in events[0].content
    assert base_world.opportunity_manager.is_in_cooldown(dummy_avatar.id, int(base_world.month_stamp) + 1)


@pytest.mark.asyncio
async def test_avatar_target_death_dissipates_opportunity(base_world, dummy_avatar):
    target = _make_avatar(base_world, "Target", 5, 5)
    base_world.avatar_manager.register_avatar(dummy_avatar)
    target.set_dead("测试死亡", base_world.month_stamp)
    base_world.avatar_manager.handle_death(target.id)
    now = int(base_world.month_stamp)
    base_world.opportunity_manager.add(
        OpportunityRecord(
            id="opp-avatar",
            avatar_id=dummy_avatar.id,
            target_type=OpportunityTargetType.AVATAR,
            target_id=target.id,
            hint_text="机缘感应：某人有缘法。",
            created_month=now - 1,
            expires_month=now + 60,
        )
    )

    events = await phase_check_opportunities(base_world, [dummy_avatar])

    assert base_world.opportunity_manager.get_for_avatar(dummy_avatar.id) is None
    assert "断绝" in events[0].content


@pytest.mark.asyncio
async def test_boon_outcome_adds_effect_and_recalculates(base_world, dummy_avatar, monkeypatch):
    _add_region(base_world, 101, "远城", [(5, 5)])
    base_world.avatar_manager.register_avatar(dummy_avatar)
    base_world.opportunity_manager.add(_record_for_region(dummy_avatar, 101))
    _place_avatar(dummy_avatar, 5, 5)
    monkeypatch.setattr("src.systems.opportunity._pick_outcome", lambda: OpportunityOutcome.BOON)
    monkeypatch.setattr(
        "src.systems.opportunity._load_boon_records",
        lambda owner: [
            {
                "effects": "{extra_max_hp: 50}",
                "duration_months": 0,
                "source": "effect_source_opportunity",
                "title": "灵机淬体",
                "weight": 1,
                "min_realm": "QI_REFINEMENT",
                "max_realm": "NASCENT_SOUL",
            }
        ],
    )
    monkeypatch.setattr("src.classes.story_event_service.StoryEventService.should_trigger", lambda kind: False)

    old_max = dummy_avatar.hp.max
    events = await phase_check_opportunities(base_world, [dummy_avatar])

    assert dummy_avatar.hp.max == old_max + 50
    assert dummy_avatar.persistent_effects
    assert any("灵机淬体" in event.content for event in events)


@pytest.mark.asyncio
async def test_equipment_outcome_grants_next_realm_weapon(base_world, dummy_avatar, monkeypatch):
    _add_region(base_world, 101, "远城", [(5, 5)])
    base_world.avatar_manager.register_avatar(dummy_avatar)
    base_world.opportunity_manager.add(_record_for_region(dummy_avatar, 101))
    _place_avatar(dummy_avatar, 5, 5)
    weapon = Weapon(
        id=999001,
        name="测试筑基剑",
        weapon_type=WeaponType.SWORD,
        realm=Realm.Foundation_Establishment,
        desc="测试",
        effects={},
    )
    monkeypatch.setattr("src.systems.opportunity._pick_outcome", lambda: OpportunityOutcome.EQUIPMENT)
    monkeypatch.setattr("src.systems.opportunity._pick_equipment", lambda owner: (weapon, ItemExchangeKind.WEAPON))
    monkeypatch.setattr("src.classes.story_event_service.StoryEventService.should_trigger", lambda kind: False)

    await phase_check_opportunities(base_world, [dummy_avatar])

    assert dummy_avatar.weapon is weapon


@pytest.mark.asyncio
async def test_injury_outcome_can_kill_avatar(base_world, dummy_avatar, monkeypatch):
    _add_region(base_world, 101, "远城", [(5, 5)])
    base_world.avatar_manager.register_avatar(dummy_avatar)
    base_world.opportunity_manager.add(_record_for_region(dummy_avatar, 101))
    _place_avatar(dummy_avatar, 5, 5)
    dummy_avatar.hp.cur = 1
    monkeypatch.setattr("src.systems.opportunity._pick_outcome", lambda: OpportunityOutcome.INJURY)
    monkeypatch.setattr("src.systems.opportunity._get_cfg_value", lambda name, default: 1.0 if name in {"injury_min_hp_ratio", "injury_max_hp_ratio"} else default)
    monkeypatch.setattr("src.classes.story_event_service.StoryEventService.should_trigger", lambda kind: False)

    events = await phase_check_opportunities(base_world, [dummy_avatar])

    assert dummy_avatar.is_dead is True
    assert dummy_avatar.id in base_world.avatar_manager.dead_avatars
    assert "身死道消" in events[0].content


def test_opportunity_serialization_round_trip(base_world, dummy_avatar):
    _add_region(base_world, 101, "远城", [(5, 5)])
    base_world.opportunity_manager.add(_record_for_region(dummy_avatar, 101))
    base_world.opportunity_manager.cooldowns[dummy_avatar.id] = int(base_world.month_stamp) + 12

    payload = serialize_opportunities(base_world)
    fresh_manager = OpportunityManager()
    base_world.opportunity_manager = fresh_manager
    load_opportunities(base_world, payload)

    restored = base_world.opportunity_manager.get_for_avatar(dummy_avatar.id)
    assert restored is not None
    assert restored.target_type == OpportunityTargetType.REGION
    assert base_world.opportunity_manager.cooldowns[dummy_avatar.id] == int(base_world.month_stamp) + 12
