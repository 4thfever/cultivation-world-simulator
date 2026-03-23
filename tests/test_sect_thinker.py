import pytest
from unittest.mock import MagicMock, patch

from src.classes.sect_thinker import SectThinker
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
        identity={
            "purpose": "守住门规与传承",
            "style": "行事审慎",
            "orthodoxy_name": "仙道",
            "rule_desc": "不得勾结邪魔。",
        },
        power={"total_battle_strength": 100.0, "influence_radius": 2},
        territory={"tile_count": 5, "conflict_tile_count": 1, "headquarter_center": (1, 1)},
        self_assessment={
            "member_count": 0,
            "alive_member_count": 0,
            "peak_member_realm": "",
            "patriarch_realm": "",
            "war_readiness": "stable",
            "resource_pressure": "normal",
            "can_afford_recruit_count": 0,
            "can_afford_support_count": 0,
        },
        economy={
            "current_magic_stone": 200,
            "effective_income_per_tile": 10.0,
            "controlled_tile_income": 50.0,
            "treasury_pressure": "tight",
            "estimated_member_upkeep": 30,
            "estimated_net_annual_balance": 20,
            "action_cost_notes": [
                "招募新人会增加未来供养成本。",
                "赐予功法会消耗宗门传承资源。",
            ],
        },
        rule={"rule_id": "righteous_orthodoxy", "rule_desc": "不得勾结邪魔。"},
        recruitment_candidates=[],
        member_candidates=[],
        relations=[],
        relations_summary="total=0",
        history={"recent_events": [], "summary_text": ""},
    )


@pytest.mark.asyncio
async def test_sect_thinker_returns_llm_content_when_valid():
    sect = _DummySect("Qingyun Sect")
    world = _DummyWorld()
    ctx = _dummy_ctx()

    payload = {
        "sect_thinking": "我宗已定取舍，当先稳住边界与资源，再循序扩充门徒与传承，以求中局主动。"
    }
    with patch.object(SectThinker, "_llm_available", return_value=True), patch(
        "src.classes.sect_thinker.call_llm_with_task_name",
        return_value=payload,
    ) as mock_llm:
        text = await SectThinker.think(sect, ctx, world, decision_summary="招徕散修 1 人。")

    assert text == payload["sect_thinking"][: SectThinker.MAX_LEN]
    kwargs = mock_llm.call_args.kwargs
    assert kwargs["infos"]["decision_summary"] == "招徕散修 1 人。"
    assert kwargs["infos"]["decision_interval_years"] == 1
    assert "守住门规与传承" in kwargs["infos"]["decision_context_info"]
    assert "供养成本" in kwargs["infos"]["decision_context_info"]


@pytest.mark.asyncio
async def test_sect_thinker_falls_back_when_llm_unavailable():
    sect = _DummySect("Qingyun Sect")
    world = _DummyWorld()
    ctx = _dummy_ctx()

    mock_service = MagicMock()
    mock_service.get_llm_runtime_config.return_value = (
        type("Profile", (), {"base_url": "", "model_name": "", "fast_model_name": ""})(),
        "",
    )
    with patch("src.classes.sect_thinker.get_settings_service", return_value=mock_service), patch(
        "src.classes.sect_thinker.get_logger"
    ) as mock_logger:
        text = await SectThinker.think(sect, ctx, world)

    assert text.startswith("我宗")
    assert 30 <= len(text) <= 100
    assert "LLM runtime config unavailable" in mock_logger.return_value.logger.warning.call_args.args[-1]


def test_sect_thinker_llm_available_uses_runtime_config():
    mock_service = MagicMock()
    mock_service.get_llm_runtime_config.return_value = (
        type("Profile", (), {"base_url": "http://test", "model_name": "test-model", "fast_model_name": "test-fast"})(),
        "secret",
    )
    with patch("src.classes.sect_thinker.get_settings_service", return_value=mock_service):
        assert SectThinker._llm_available() is True


@pytest.mark.asyncio
async def test_sect_thinker_warns_when_response_too_short():
    sect = _DummySect("Qingyun Sect")
    world = _DummyWorld()
    ctx = _dummy_ctx()
    mock_service = MagicMock()
    mock_service.get_llm_runtime_config.return_value = (
        type("Profile", (), {"base_url": "http://test", "model_name": "test-model", "fast_model_name": "test-fast"})(),
        "secret",
    )

    with patch("src.classes.sect_thinker.get_settings_service", return_value=mock_service), patch(
        "src.classes.sect_thinker.call_llm_with_task_name",
        return_value={"sect_thinking": "太短"},
    ), patch("src.classes.sect_thinker.get_logger") as mock_logger:
        text = await SectThinker.think(sect, ctx, world)

    assert text.startswith("我宗")
    assert "LLM response too short" in mock_logger.return_value.logger.warning.call_args.args[-1]
