import pytest
from unittest.mock import patch

from src.classes.sect_decider import SectDecider
from src.systems.sect_decision_context import SectDecisionContext


class _DummySect:
    def __init__(self, name: str):
        self.name = name


class _DummyPhenomenon:
    def __init__(self, name: str, desc: str):
        self.name = name
        self.desc = desc


class _DummyWorld:
    def __init__(self):
        self.current_phenomenon = _DummyPhenomenon("Heaven Tide", "Spiritual qi surges")

    def get_info(self, detailed: bool = False):
        return {"world_state": "stable", "detailed": detailed}


def _dummy_ctx() -> SectDecisionContext:
    return SectDecisionContext(
        basic_structured={"name": "Test Sect"},
        basic_text="Test sect detailed info",
        power={"total_battle_strength": 100.0, "influence_radius": 2},
        territory={"tile_count": 5, "conflict_tile_count": 1, "headquarter_center": (1, 1)},
        economy={"current_magic_stone": 200, "effective_income_per_tile": 10.0, "controlled_tile_income": 50.0},
        relations=[],
        relations_summary="total=0",
        history={"recent_events": [], "summary_text": ""},
    )


@pytest.mark.asyncio
async def test_sect_decider_returns_llm_content_when_valid():
    sect = _DummySect("Qingyun Sect")
    world = _DummyWorld()
    ctx = _dummy_ctx()

    payload = {
        "sect_thinking": "Our sect sees fragmentation among rivals, so we should secure borders and resources first, then build a selective alliance to gain initiative."
    }
    with patch.object(SectDecider, "_llm_available", return_value=True), patch(
        "src.classes.sect_decider.call_llm_with_task_name",
        return_value=payload,
    ) as mock_llm:
        text = await SectDecider.decide(sect, ctx, world)

    assert text == payload["sect_thinking"][: SectDecider.MAX_LEN]
    assert mock_llm.called
    kwargs = mock_llm.call_args.kwargs
    assert "world_info" in kwargs["infos"]
    assert "current_phenomenon_info" in kwargs["infos"]


@pytest.mark.asyncio
async def test_sect_decider_falls_back_when_llm_unavailable():
    sect = _DummySect("Qingyun Sect")
    world = _DummyWorld()
    ctx = _dummy_ctx()

    with patch.object(SectDecider, "_llm_available", return_value=False):
        text = await SectDecider.decide(sect, ctx, world)

    assert text.startswith("我宗")
    assert 30 <= len(text) <= 100
