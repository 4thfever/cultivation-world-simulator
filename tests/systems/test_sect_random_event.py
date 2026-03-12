import pytest
from unittest.mock import AsyncMock, patch

from src.systems.sect_random_event import try_trigger_sect_random_event
from src.utils.llm.config import LLMMode


class DummySect:
    def __init__(self, sect_id: int, name: str):
        self.id = sect_id
        self.name = name
        self.magic_stone = 0
        self.is_active = True
        self.temporary_calls = []

    def get_detailed_info(self) -> str:
        return f"{self.name} detailed info"

    def add_temporary_sect_effect(self, *, effects, start_month, duration, source="sect_random_event"):
        self.temporary_calls.append(
            {
                "effects": dict(effects),
                "start_month": int(start_month),
                "duration": int(duration),
                "source": source,
            }
        )


@pytest.mark.asyncio
async def test_relation_event_two_sects(base_world):
    sect_a = DummySect(1, "A宗")
    sect_b = DummySect(2, "B宗")
    base_world.existed_sects = [sect_a, sect_b]

    records = [
        {
            "id": 1,
            "event_type": "relation_up",
            "weight": 1.0,
            "value": 12,
            "duration_months": 60,
        }
    ]

    with patch("src.systems.sect_random_event.game_configs") as mock_configs, \
        patch("src.systems.sect_random_event.call_llm_with_template", new_callable=AsyncMock) as mock_llm, \
        patch("src.systems.sect_random_event.random.random", return_value=0.0):
        mock_configs.get.return_value = records
        mock_llm.return_value = {"reason_fragment": "边境旧约重新谈判"}

        event = await try_trigger_sect_random_event(base_world)

    assert event is not None
    assert set(event.related_sects or []) == {1, 2}
    assert len(base_world.sect_relation_modifiers) == 1
    assert base_world.sect_relation_modifiers[0]["delta"] == 12
    assert base_world.sect_relation_modifiers[0]["duration"] == 60
    assert "边境旧约重新谈判" in event.content
    assert "Because" not in event.content
    assert mock_llm.await_args.kwargs["mode"] == LLMMode.FAST


@pytest.mark.asyncio
async def test_magic_stone_event_single_sect(base_world):
    sect_a = DummySect(1, "A宗")
    base_world.existed_sects = [sect_a]

    records = [
        {
            "id": 3,
            "event_type": "magic_stone_down",
            "weight": 1.0,
            "value": 150,
            "duration_months": 0,
        }
    ]

    with patch("src.systems.sect_random_event.game_configs") as mock_configs, \
        patch("src.systems.sect_random_event.call_llm_with_template", new_callable=AsyncMock) as mock_llm, \
        patch("src.systems.sect_random_event.random.random", return_value=0.0):
        mock_configs.get.return_value = records
        mock_llm.return_value = {"reason_fragment": "内务整顿资金紧张"}

        event = await try_trigger_sect_random_event(base_world)

    assert event is not None
    assert event.related_sects == [1]
    assert sect_a.magic_stone == -150
    assert len(base_world.sect_relation_modifiers) == 0
    assert len(sect_a.temporary_calls) == 0


@pytest.mark.asyncio
async def test_income_event_single_sect(base_world):
    sect_a = DummySect(1, "A宗")
    base_world.existed_sects = [sect_a]

    records = [
        {
            "id": 5,
            "event_type": "income_up",
            "weight": 1.0,
            "value": 0.8,
            "duration_months": 60,
        }
    ]

    with patch("src.systems.sect_random_event.game_configs") as mock_configs, \
        patch("src.systems.sect_random_event.call_llm_with_template", new_callable=AsyncMock) as mock_llm, \
        patch("src.systems.sect_random_event.random.random", return_value=0.0):
        mock_configs.get.return_value = records
        mock_llm.return_value = {"reason_fragment": "新商路税契暂时稳定"}

        event = await try_trigger_sect_random_event(base_world)

    assert event is not None
    assert event.related_sects == [1]
    assert len(sect_a.temporary_calls) == 1
    assert sect_a.temporary_calls[0]["effects"]["extra_income_per_tile"] == pytest.approx(0.8)


@pytest.mark.asyncio
async def test_no_event_when_reason_generation_raises(base_world):
    sect_a = DummySect(1, "A宗")
    sect_b = DummySect(2, "B宗")
    base_world.existed_sects = [sect_a, sect_b]

    records = [
        {
            "id": 2,
            "event_type": "relation_down",
            "weight": 1.0,
            "value": 12,
            "duration_months": 60,
        }
    ]

    with patch("src.systems.sect_random_event.game_configs") as mock_configs, \
        patch("src.systems.sect_random_event.call_llm_with_template", new_callable=AsyncMock) as mock_llm, \
        patch("src.systems.sect_random_event.random.random", return_value=0.0):
        mock_configs.get.return_value = records
        mock_llm.side_effect = RuntimeError("llm down")

        event = await try_trigger_sect_random_event(base_world)

    assert event is None
    assert len(base_world.sect_relation_modifiers) == 0
    assert sect_a.magic_stone == 0
    assert sect_b.magic_stone == 0
    assert len(sect_a.temporary_calls) == 0
    assert len(sect_b.temporary_calls) == 0


@pytest.mark.asyncio
async def test_no_event_when_reason_fragment_is_empty(base_world):
    sect_a = DummySect(1, "A宗")
    base_world.existed_sects = [sect_a]

    records = [
        {
            "id": 3,
            "event_type": "magic_stone_up",
            "weight": 1.0,
            "value": 150,
            "duration_months": 0,
        }
    ]

    with patch("src.systems.sect_random_event.game_configs") as mock_configs, \
        patch("src.systems.sect_random_event.call_llm_with_template", new_callable=AsyncMock) as mock_llm, \
        patch("src.systems.sect_random_event.random.random", return_value=0.0):
        mock_configs.get.return_value = records
        mock_llm.return_value = {"reason_fragment": "   "}

        event = await try_trigger_sect_random_event(base_world)

    assert event is None
    assert sect_a.magic_stone == 0
    assert len(sect_a.temporary_calls) == 0
    assert len(base_world.sect_relation_modifiers) == 0


@pytest.mark.asyncio
async def test_no_event_when_reason_payload_is_not_dict(base_world):
    sect_a = DummySect(1, "A宗")
    base_world.existed_sects = [sect_a]

    records = [
        {
            "id": 5,
            "event_type": "income_up",
            "weight": 1.0,
            "value": 0.8,
            "duration_months": 60,
        }
    ]

    with patch("src.systems.sect_random_event.game_configs") as mock_configs, \
        patch("src.systems.sect_random_event.call_llm_with_template", new_callable=AsyncMock) as mock_llm, \
        patch("src.systems.sect_random_event.random.random", return_value=0.0):
        mock_configs.get.return_value = records
        mock_llm.return_value = "invalid"

        event = await try_trigger_sect_random_event(base_world)

    assert event is None
    assert len(sect_a.temporary_calls) == 0
    assert len(base_world.sect_relation_modifiers) == 0
    assert sect_a.magic_stone == 0


@pytest.mark.asyncio
async def test_invalid_event_type_raises(base_world):
    sect_a = DummySect(1, "A宗")
    base_world.existed_sects = [sect_a]

    records = [{"id": 99, "event_type": "unknown", "weight": 1.0, "value": 1, "duration_months": 1}]

    with patch("src.systems.sect_random_event.game_configs") as mock_configs, \
        patch("src.systems.sect_random_event.random.random", return_value=0.0):
        mock_configs.get.return_value = records

        with pytest.raises(ValueError, match="Invalid sect_random_event event_type"):
            await try_trigger_sect_random_event(base_world)


@pytest.mark.asyncio
async def test_legacy_relation_delta_raises(base_world):
    sect_a = DummySect(1, "A宗")
    base_world.existed_sects = [sect_a]

    records = [
        {
            "id": 100,
            "event_type": "magic_stone_up",
            "weight": 1.0,
            "value": 100,
            "duration_months": 0,
            "relation_delta": -10,
        }
    ]

    with patch("src.systems.sect_random_event.game_configs") as mock_configs, \
        patch("src.systems.sect_random_event.random.random", return_value=0.0):
        mock_configs.get.return_value = records

        with pytest.raises(ValueError, match="Legacy field relation_delta is not supported"):
            await try_trigger_sect_random_event(base_world)
