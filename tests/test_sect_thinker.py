import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.classes.sect_thinker import SectThinker
from src.classes.language import language_manager
from src.i18n import reload_translations
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
        self.world_lore = type("WorldLore", (), {"text": ""})()

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
    assert "守住门规与传承" in kwargs["infos"]["decision_context_info"]
    assert "供养成本" in kwargs["infos"]["decision_context_info"]
    assert kwargs["infos"]["world_lore"] == ""


@pytest.mark.asyncio
async def test_sect_thinker_falls_back_when_llm_unavailable():
    sect = _DummySect("Qingyun Sect")
    world = _DummyWorld()
    ctx = _dummy_ctx()
    original_lang = str(language_manager)

    mock_service = MagicMock()
    mock_service.get_llm_runtime_config.return_value = (
        type("Profile", (), {"base_url": "", "model_name": "", "fast_model_name": ""})(),
        "",
    )
    try:
        language_manager._current = "zh-CN"
        reload_translations()
        with patch("src.classes.sect_thinker.get_settings_service", return_value=mock_service), patch(
            "src.classes.sect_thinker.get_logger"
        ) as mock_logger:
            text = await SectThinker.think(sect, ctx, world)

        assert text.startswith("我宗")
        assert 30 <= len(text) <= 100
        assert "LLM runtime config unavailable" in mock_logger.return_value.logger.warning.call_args.args[-1]
    finally:
        language_manager._current = original_lang
        reload_translations()


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
    original_lang = str(language_manager)
    mock_service = MagicMock()
    mock_service.get_llm_runtime_config.return_value = (
        type("Profile", (), {"base_url": "http://test", "model_name": "test-model", "fast_model_name": "test-fast"})(),
        "secret",
    )

    try:
        language_manager._current = "zh-CN"
        reload_translations()
        with patch("src.classes.sect_thinker.get_settings_service", return_value=mock_service), patch(
            "src.classes.sect_thinker.call_llm_with_task_name",
            return_value={"sect_thinking": "太短"},
        ), patch("src.classes.sect_thinker.get_logger") as mock_logger:
            text = await SectThinker.think(sect, ctx, world)

        assert text.startswith("我宗")
        assert "LLM response too short" in mock_logger.return_value.logger.warning.call_args.args[-1]
    finally:
        language_manager._current = original_lang
        reload_translations()


def test_sect_thinker_current_phenomenon_info_uses_i18n_fallback_text():
    original_lang = str(language_manager)
    try:
        language_manager._current = "zh-CN"
        reload_translations()
        world = type("World", (), {"current_phenomenon": None})()
        assert SectThinker._current_phenomenon_info(world) == "当前无天地异象。"

        world.current_phenomenon = type("Phenomenon", (), {"name": "", "desc": ""})()
        assert SectThinker._current_phenomenon_info(world) == "当前有天地异象，但描述缺失。"
    finally:
        language_manager._current = original_lang
        reload_translations()


@pytest.mark.parametrize(
    ("locale_code", "expected_snippet"),
    [
        ("en-US", "fully written in natural english"),
        ("vi-VN", "hoan toan bang tieng viet tu nhien"),
    ],
)
def test_sect_thinker_templates_force_target_language(locale_code: str, expected_snippet: str):
    template_path = Path(f"static/locales/{locale_code}/templates/sect_thinker.txt")
    content = template_path.read_text(encoding="utf-8")
    normalized = content.lower().translate(str.maketrans({"á": "a", "à": "a", "ả": "a", "ã": "a", "ạ": "a", "ă": "a", "ắ": "a", "ằ": "a", "ẳ": "a", "ẵ": "a", "ặ": "a", "â": "a", "ấ": "a", "ầ": "a", "ẩ": "a", "ẫ": "a", "ậ": "a", "đ": "d", "é": "e", "è": "e", "ẻ": "e", "ẽ": "e", "ẹ": "e", "ê": "e", "ế": "e", "ề": "e", "ể": "e", "ễ": "e", "ệ": "e", "í": "i", "ì": "i", "ỉ": "i", "ĩ": "i", "ị": "i", "ó": "o", "ò": "o", "ỏ": "o", "õ": "o", "ọ": "o", "ô": "o", "ố": "o", "ồ": "o", "ổ": "o", "ỗ": "o", "ộ": "o", "ơ": "o", "ớ": "o", "ờ": "o", "ở": "o", "ỡ": "o", "ợ": "o", "ú": "u", "ù": "u", "ủ": "u", "ũ": "u", "ụ": "u", "ư": "u", "ứ": "u", "ừ": "u", "ử": "u", "ữ": "u", "ự": "u", "ý": "y", "ỳ": "y", "ỷ": "y", "ỹ": "y", "ỵ": "y"}))

    assert expected_snippet in normalized
