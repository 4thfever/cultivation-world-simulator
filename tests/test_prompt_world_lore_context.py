from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.classes.ai import llm_ai
from src.classes.backstory import generate_backstory
from src.classes.long_term_objective import generate_long_term_objective
from src.classes.nickname import generate_nickname
from src.classes.story_teller import StoryTeller


@pytest.mark.asyncio
async def test_generate_backstory_passes_world_lore_separately(dummy_avatar):
    dummy_avatar.world.set_world_lore("天地秩序因上古大战而重写。")

    with patch("src.classes.backstory.call_llm_with_task_name", new=AsyncMock(return_value={"backstory": "出身寒门。"})) as mock_llm:
        await generate_backstory(dummy_avatar)

    infos = mock_llm.await_args.args[2]
    assert infos["world_lore"] == "天地秩序因上古大战而重写。"
    assert "天地秩序因上古大战而重写。" not in infos["world_info"]


@pytest.mark.asyncio
async def test_generate_nickname_passes_world_lore_separately(dummy_avatar):
    dummy_avatar.world.set_world_lore("正邪两道长年对峙。")
    dummy_avatar.world.event_manager.get_major_events_by_avatar = MagicMock(return_value=[])
    dummy_avatar.world.event_manager.get_minor_events_by_avatar = MagicMock(return_value=[])

    with patch("src.classes.nickname.call_llm_with_task_name", new=AsyncMock(return_value={"nickname": "寒锋", "thinking": "", "reason": "剑冷人静"})) as mock_llm:
        await generate_nickname(dummy_avatar)

    infos = mock_llm.await_args.args[2]
    assert infos["world_lore"] == "正邪两道长年对峙。"
    assert "正邪两道长年对峙。" not in str(infos["world_info"])


@pytest.mark.asyncio
async def test_generate_long_term_objective_passes_world_lore_separately(dummy_avatar):
    dummy_avatar.world.set_world_lore("王朝与宗门共治天下。")

    with patch(
        "src.classes.long_term_objective.call_llm_with_task_name",
        new=AsyncMock(return_value={"long_term_objective": "守住道心"}),
    ) as mock_llm:
        await generate_long_term_objective(dummy_avatar)

    infos = mock_llm.await_args.args[2]
    assert infos["world_lore"] == "王朝与宗门共治天下。"
    assert "王朝与宗门共治天下。" not in str(infos["world_info"])


@pytest.mark.asyncio
async def test_story_teller_passes_world_lore_separately(dummy_avatar):
    dummy_avatar.world.set_world_lore("天地灵机紊乱，旧秩序松动。")

    with patch("src.classes.story_teller.call_llm_with_task_name", new=AsyncMock(return_value={"story": "短故事"})) as mock_llm:
        await StoryTeller.tell_story("有人相遇", "各自离去", dummy_avatar)

    infos = mock_llm.await_args.args[2]
    assert infos["world_lore"] == "天地灵机紊乱，旧秩序松动。"
    assert "天地灵机紊乱，旧秩序松动。" not in str(infos["world_info"])


@pytest.mark.asyncio
async def test_llm_ai_passes_world_lore_separately(dummy_avatar):
    dummy_avatar.world.set_world_lore("秘境频开，诸宗争衡。")
    dummy_avatar.get_expanded_info = MagicMock(return_value={"name": dummy_avatar.name})
    dummy_avatar.world.get_observable_avatars = MagicMock(return_value=[])

    payload = {
        dummy_avatar.name: {
            "action_name_params_pairs": [["MoveToDirection", {"direction": "north"}]],
            "avatar_thinking": "先看看局势。",
            "current_emotion": "emotion_calm",
            "short_term_objective": "探路",
        }
    }
    with patch("src.classes.ai.call_llm_with_task_name", new=AsyncMock(return_value=payload)) as mock_llm, patch(
        "src.classes.ai.get_action_infos_str",
        return_value="MoveToDirection",
    ), patch(
        "src.classes.core.avatar.info_presenter.get_avatar_ai_context",
        return_value={},
    ):
        await llm_ai._decide(dummy_avatar.world, [dummy_avatar])

    infos = mock_llm.await_args.args[2]
    assert infos["world_lore"] == "秘境频开，诸宗争衡。"
    assert "秘境频开，诸宗争衡。" not in str(infos["world_info"])
