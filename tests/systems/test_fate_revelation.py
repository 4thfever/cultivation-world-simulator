from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.systems.fate_revelation import (
    FATE_REVELATION_EVENT_TYPE,
    is_valid_oracle_text,
    should_trigger_fate_revelation,
    try_trigger_fate_revelation,
)


def test_oracle_text_validation_allows_poetic_forms():
    assert is_valid_oracle_text("遇潮而圆，见信而寂")
    assert is_valid_oracle_text("千山暮雪倾东海，初日潮头又上来")
    assert is_valid_oracle_text("花落非春尽，钟鸣不是归")


def test_oracle_text_validation_rejects_explanations():
    assert not is_valid_oracle_text("这预示着他将会飞升")
    assert not is_valid_oracle_text("命格：贵人相助")
    assert not is_valid_oracle_text("系统显示属性奖励")


def test_should_not_trigger_when_avatar_already_has_fate(dummy_avatar, monkeypatch):
    dummy_avatar.fate_revelation = {
        "trigger_text": "旧雨落在石阶上。",
        "oracle_text": "旧雨照灯，潮回无岸",
    }
    monkeypatch.setattr("src.systems.fate_revelation.random.random", lambda: 0.0)

    assert should_trigger_fate_revelation(dummy_avatar) is False


def test_should_not_trigger_when_probability_zero(dummy_avatar, monkeypatch):
    monkeypatch.setattr("src.systems.fate_revelation.CONFIG.world.fate_revelation_probability", 0.0)
    monkeypatch.setattr("src.systems.fate_revelation.random.random", lambda: 0.0)

    assert should_trigger_fate_revelation(dummy_avatar) is False


@pytest.mark.asyncio
async def test_try_trigger_fate_revelation_writes_avatar_and_event(dummy_avatar, monkeypatch):
    dummy_avatar.fate_revelation = None
    monkeypatch.setattr("src.systems.fate_revelation.CONFIG.world.fate_revelation_probability", 1.0)
    monkeypatch.setattr("src.systems.fate_revelation.random.random", lambda: 0.0)

    llm_result = {
        "trigger_text": "青溪渡口忽有逆流成圆，几片残叶贴着水面缓缓不散。",
        "oracle_text": "千山暮雪倾东海，初日潮头又上来",
        "event_text": "青溪渡口忽有逆流成圆，几片残叶贴着水面缓缓不散。TestDummy凝神看去，心中浮起一句命格：『千山暮雪倾东海，初日潮头又上来』",
    }
    with patch(
        "src.systems.fate_revelation.call_llm_with_task_name",
        new_callable=AsyncMock,
        return_value=llm_result,
    ) as mock_call:
        events = await try_trigger_fate_revelation(dummy_avatar, dummy_avatar.world)

    assert len(events) == 1
    event = events[0]
    assert event.is_major is True
    assert event.is_story is False
    assert event.event_type == FATE_REVELATION_EVENT_TYPE
    assert event.related_avatars == [dummy_avatar.id]
    assert "千山暮雪倾东海" in event.content
    assert dummy_avatar.fate_revelation is not None
    assert dummy_avatar.fate_revelation["oracle_text"] == llm_result["oracle_text"]
    assert dummy_avatar.fate_revelation["trigger_text"] == llm_result["trigger_text"]
    assert dummy_avatar.fate_revelation["revealed_month"] == int(dummy_avatar.world.month_stamp)
    assert mock_call.call_args.kwargs["task_name"] == "fate_revelation"


@pytest.mark.asyncio
async def test_try_trigger_fate_revelation_rejects_bad_oracle(dummy_avatar, monkeypatch):
    dummy_avatar.fate_revelation = None
    monkeypatch.setattr("src.systems.fate_revelation.CONFIG.world.fate_revelation_probability", 1.0)
    monkeypatch.setattr("src.systems.fate_revelation.random.random", lambda: 0.0)

    llm_result = {
        "trigger_text": "夜雨打在废碑上，石缝里有微光一闪而灭。",
        "oracle_text": "这预示着他将会飞升",
        "event_text": "坏输出",
    }
    with patch(
        "src.systems.fate_revelation.call_llm_with_task_name",
        new_callable=AsyncMock,
        return_value=llm_result,
    ):
        events = await try_trigger_fate_revelation(dummy_avatar, dummy_avatar.world)

    assert events == []
    assert dummy_avatar.fate_revelation is None
