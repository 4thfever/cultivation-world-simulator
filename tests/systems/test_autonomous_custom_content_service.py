from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from src.classes.custom_content import CustomContentRegistry
from src.classes.story_event_service import StoryEventKind, StoryEventService
from src.classes.technique import techniques_by_id
from src.systems.autonomous_custom_content_service import (
    AutonomousCustomContentService,
    try_trigger_autonomous_custom_creation,
)
from src.systems.cultivation import Realm


@pytest.mark.asyncio
async def test_autonomous_creation_equips_technique_and_registers_content(base_world, dummy_avatar):
    CustomContentRegistry.reset()
    base_world.avatar_manager.register_avatar(dummy_avatar)

    with patch(
        "src.systems.autonomous_custom_content_service.generate_custom_content_draft",
        new_callable=AsyncMock,
    ) as mock_generate, patch(
        "src.classes.story_event_service.StoryEventService.should_trigger",
        return_value=False,
    ), patch(
        "random.choice",
        return_value="technique",
    ):
        mock_generate.return_value = {
            "category": "technique",
            "name": "九曜焚息诀",
            "desc": "火行吐纳功法",
            "effects": {"extra_respire_exp_multiplier": 0.2},
            "attribute": "FIRE",
            "grade": "UPPER",
            "effect_desc": "额外吐纳经验倍率 +20%",
            "is_custom": True,
        }

        events = await AutonomousCustomContentService.try_create_events(dummy_avatar, base_world)

    assert len(events) == 1
    assert "self-created technique" in events[0].content or "自创功法" in events[0].content
    assert dummy_avatar.technique is not None
    assert dummy_avatar.technique.name == "九曜焚息诀"
    assert int(dummy_avatar.technique.id) in CustomContentRegistry.custom_techniques_by_id
    assert techniques_by_id[int(dummy_avatar.technique.id)].name == "九曜焚息诀"


@pytest.mark.asyncio
async def test_autonomous_creation_forced_equips_weapon_and_sells_old(base_world, dummy_avatar):
    from tests.conftest import create_test_weapon

    CustomContentRegistry.reset()
    base_world.avatar_manager.register_avatar(dummy_avatar)
    old_weapon = create_test_weapon("旧剑", Realm.Qi_Refinement, weapon_id=2501)
    dummy_avatar.change_weapon(old_weapon)
    dummy_avatar.magic_stone = 0

    with patch(
        "src.systems.autonomous_custom_content_service.generate_custom_content_draft",
        new_callable=AsyncMock,
    ) as mock_generate, patch(
        "src.classes.story_event_service.StoryEventService.should_trigger",
        return_value=False,
    ), patch(
        "random.choice",
        return_value="weapon",
    ):
        mock_generate.return_value = {
            "category": "weapon",
            "realm": Realm.Qi_Refinement.value,
            "name": "新剑",
            "desc": "新兵器",
            "effects": {"extra_battle_strength_points": 3},
            "weapon_type": "SWORD",
            "effect_desc": "额外战斗力 +3",
            "is_custom": True,
        }

        events = await AutonomousCustomContentService.try_create_events(dummy_avatar, base_world)

    assert len(events) == 2
    assert dummy_avatar.weapon is not None
    assert dummy_avatar.weapon.name == "新剑"
    assert dummy_avatar.weapon.realm == Realm.Qi_Refinement
    assert dummy_avatar.magic_stone > 0
    assert "sold old equipment" in events[1].content or "卖出旧装备" in events[1].content


@pytest.mark.asyncio
async def test_autonomous_creation_story_uses_dedicated_story_kind(base_world, dummy_avatar):
    CustomContentRegistry.reset()
    base_world.avatar_manager.register_avatar(dummy_avatar)

    with patch(
        "src.systems.autonomous_custom_content_service.generate_custom_content_draft",
        new_callable=AsyncMock,
    ) as mock_generate, patch(
        "src.classes.story_event_service.StoryTeller.tell_story",
        new_callable=AsyncMock,
    ) as mock_tell, patch(
        "src.classes.story_event_service.StoryEventService.should_trigger",
        return_value=True,
    ), patch(
        "random.choice",
        return_value="technique",
    ):
        mock_generate.return_value = {
            "category": "technique",
            "name": "星火诀",
            "desc": "自创功法",
            "effects": {"extra_respire_exp_multiplier": 0.1},
            "attribute": "FIRE",
            "grade": "MIDDLE",
            "effect_desc": "额外吐纳经验倍率 +10%",
            "is_custom": True,
        }
        mock_tell.return_value = "自创故事正文"

        events = await AutonomousCustomContentService.try_create_events(dummy_avatar, base_world)

    assert len(events) == 2
    assert events[1].is_story is True
    mock_tell.assert_awaited_once()


@pytest.mark.asyncio
async def test_try_trigger_autonomous_custom_creation_respects_probability(base_world, dummy_avatar):
    with patch.object(AutonomousCustomContentService, "should_trigger", return_value=False), patch.object(
        AutonomousCustomContentService,
        "try_create_events",
        new_callable=AsyncMock,
    ) as mock_try:
        events = await try_trigger_autonomous_custom_creation(dummy_avatar, base_world)

    assert events == []
    mock_try.assert_not_called()


def test_autonomous_creation_story_probability_comes_from_config():
    probability = StoryEventService.get_probability(StoryEventKind.AUTONOMOUS_CREATION)
    assert probability == 0.5
