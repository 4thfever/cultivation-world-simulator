import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from src.classes.age import Age
from src.classes.alignment import Alignment
from src.classes.core.avatar import Avatar, Gender
from src.classes.core.sect import Sect, SectHeadQuarter
from src.classes.sect_decider import SectDecider
from src.classes.sect_ranks import get_rank_from_realm
from src.classes.technique import Technique, TechniqueAttribute, TechniqueGrade, techniques_by_name
from src.classes.root import Root
from src.systems.cultivation import Realm
from src.systems.sect_decision_context import SectDecisionContext
from src.systems.time import Month, Year, create_month_stamp


def _create_avatar(world, *, avatar_id: str, name: str, alignment: Alignment) -> Avatar:
    avatar = Avatar(
        world=world,
        name=name,
        id=avatar_id,
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.MALE,
        pos_x=0,
        pos_y=0,
        root=Root.GOLD,
        personas=[],
        alignment=alignment,
    )
    avatar.personas = []
    avatar.weapon = None
    avatar.technique = None
    avatar.recalc_effects()
    return avatar


def _dummy_ctx(rogue: Avatar, member: Avatar, breaker: Avatar) -> SectDecisionContext:
    return SectDecisionContext(
        basic_structured={"name": "Test Sect"},
        basic_text="Test sect detailed info",
        power={"total_battle_strength": 100.0, "influence_radius": 2},
        territory={"tile_count": 5, "conflict_tile_count": 1, "headquarter_center": (1, 1)},
        self_assessment={
            "member_count": 2,
            "alive_member_count": 2,
            "peak_member_realm": str(member.cultivation_progress.realm),
            "patriarch_realm": "",
            "war_readiness": "stable",
            "resource_pressure": "normal",
            "can_afford_recruit_count": 2,
            "can_afford_support_count": 3,
        },
        economy={"current_magic_stone": 1000, "effective_income_per_tile": 10.0, "controlled_tile_income": 50.0},
        relations=[],
        relations_summary="total=0",
        history={"recent_events": [], "summary_text": ""},
        diplomacy_targets=[
            {
                "other_sect_id": 2,
                "other_sect_name": "Enemy Sect",
                "status": "peace",
                "war_months": 0,
                "peace_months": 24,
                "last_battle_month": None,
                "relation_value": -10,
            }
        ],
        active_wars=[],
        rule={"rule_id": "righteous_orthodoxy", "rule_desc": "不得勾结邪魔。"},
        recruitment_candidates=[
            {
                "avatar_id": rogue.id,
                "name": rogue.name,
                "alignment": str(rogue.alignment),
                "realm": str(rogue.cultivation_progress.realm),
                "magic_stone": int(rogue.magic_stone.value),
                "technique_name": "",
                "technique_grade": "",
                "technique_grade_rank": 0,
                "alignment_recruitable": True,
            }
        ],
        member_candidates=[
            {
                "avatar_id": member.id,
                "name": member.name,
                "alignment": str(member.alignment),
                "realm": str(member.cultivation_progress.realm),
                "rank": "",
                "magic_stone": int(member.magic_stone.value),
                "technique_name": "",
                "technique_grade": "",
                "technique_grade_rank": 1,
                "is_rule_breaker": False,
            },
            {
                "avatar_id": breaker.id,
                "name": breaker.name,
                "alignment": str(breaker.alignment),
                "realm": str(breaker.cultivation_progress.realm),
                "rank": "",
                "magic_stone": int(breaker.magic_stone.value),
                "technique_name": "",
                "technique_grade": "",
                "technique_grade_rank": 1,
                "is_rule_breaker": True,
            },
        ],
    )


@pytest.mark.asyncio
async def test_sect_decider_executes_recruit_expel_reward_and_support(base_world):
    sect = Sect(
        id=1,
        name="Test Sect",
        desc="",
        member_act_style="",
        alignment=Alignment.RIGHTEOUS,
        headquarter=SectHeadQuarter(name="HQ", desc="", image=Path("")),
        technique_names=["测试上品金诀"],
        rule_id="righteous_orthodoxy",
        rule_desc="不得勾结邪魔。",
        magic_stone=1000,
    )

    reward_technique = Technique(
        id=99901,
        name="测试上品金诀",
        attribute=TechniqueAttribute.GOLD,
        grade=TechniqueGrade.UPPER,
        desc="",
        weight=1.0,
        condition="",
        sect_id=1,
    )
    low_technique = Technique(
        id=99902,
        name="测试下品金诀",
        attribute=TechniqueAttribute.GOLD,
        grade=TechniqueGrade.LOWER,
        desc="",
        weight=1.0,
        condition="",
        sect_id=None,
    )

    rogue = _create_avatar(base_world, avatar_id="rogue", name="Rogue", alignment=Alignment.RIGHTEOUS)
    member = _create_avatar(base_world, avatar_id="member", name="Member", alignment=Alignment.RIGHTEOUS)
    breaker = _create_avatar(base_world, avatar_id="breaker", name="Breaker", alignment=Alignment.EVIL)

    member.technique = low_technique
    member.magic_stone.value = 0
    breaker.magic_stone.value = 100
    member.join_sect(sect, get_rank_from_realm(member.cultivation_progress.realm))
    breaker.join_sect(sect, get_rank_from_realm(breaker.cultivation_progress.realm))

    base_world.avatar_manager.avatars = {
        rogue.id: rogue,
        member.id: member,
        breaker.id: breaker,
    }

    ctx = _dummy_ctx(rogue, member, breaker)
    old_tech = techniques_by_name.get(reward_technique.name)
    techniques_by_name[reward_technique.name] = reward_technique

    try:
        with patch(
            "src.classes.sect_decider.resolve_sect_recruitment",
            new=AsyncMock(return_value=type("Outcome", (), {"accepted": True, "result_text": "Rogue 答应了 Test Sect 的招徕。"})()),
        ), patch("src.classes.sect_decider.random.choice", return_value=reward_technique):
            result = await SectDecider.decide(sect, ctx, base_world)
    finally:
        if old_tech is None:
            techniques_by_name.pop(reward_technique.name, None)
        else:
            techniques_by_name[reward_technique.name] = old_tech

    assert rogue.sect == sect
    assert rogue.sect_rank is not None
    assert rogue.technique == reward_technique
    assert breaker.sect is None
    assert member.technique == reward_technique
    assert member.magic_stone.value == 300
    assert sect.magic_stone == 200
    assert result.recruitment_count == 1
    assert result.expulsion_count == 1
    assert result.technique_reward_count == 2
    assert result.support_count == 1
    assert "招徕散修 1 人" in result.summary_text
    assert any("逐出宗门" in event.content for event in result.events)


@pytest.mark.asyncio
async def test_sect_decider_skips_recruitment_when_funds_insufficient(base_world):
    sect = Sect(
        id=1,
        name="Poor Sect",
        desc="",
        member_act_style="",
        alignment=Alignment.RIGHTEOUS,
        headquarter=SectHeadQuarter(name="HQ", desc="", image=Path("")),
        technique_names=[],
        rule_id="righteous_orthodoxy",
        rule_desc="不得勾结邪魔。",
        magic_stone=400,
    )
    rogue = _create_avatar(base_world, avatar_id="rogue", name="Rogue", alignment=Alignment.RIGHTEOUS)
    base_world.avatar_manager.avatars = {rogue.id: rogue}
    ctx = SectDecisionContext(
        basic_structured={"name": "Poor Sect"},
        basic_text="",
        power={},
        territory={},
        self_assessment={},
        economy={},
        rule={"rule_id": "righteous_orthodoxy", "rule_desc": "不得勾结邪魔。"},
        recruitment_candidates=[
            {
                "avatar_id": rogue.id,
                "name": rogue.name,
                "alignment": str(rogue.alignment),
                "realm": str(rogue.cultivation_progress.realm),
                "magic_stone": int(rogue.magic_stone.value),
                "technique_name": "",
                "technique_grade": "",
                "technique_grade_rank": 0,
                "alignment_recruitable": True,
            }
        ],
        member_candidates=[],
        relations=[],
        relations_summary="",
        history={"recent_events": [], "summary_text": ""},
    )

    with patch("src.classes.sect_decider.resolve_sect_recruitment", new=AsyncMock()) as mock_resolve:
        result = await SectDecider.decide(sect, ctx, base_world)

    mock_resolve.assert_not_awaited()
    assert rogue.sect is None
    assert sect.magic_stone == 400
    assert result.recruitment_count == 0


@pytest.mark.asyncio
async def test_sect_decider_llm_plan_receives_detailed_info(base_world):
    sect = Sect(
        id=1,
        name="Wise Sect",
        desc="",
        member_act_style="",
        alignment=Alignment.RIGHTEOUS,
        headquarter=SectHeadQuarter(name="HQ", desc="", image=Path("")),
        technique_names=[],
        rule_id="righteous_orthodoxy",
        rule_desc="不得勾结邪魔。",
        magic_stone=1000,
    )
    rogue = _create_avatar(base_world, avatar_id="rogue", name="Rogue", alignment=Alignment.RIGHTEOUS)
    ctx = SectDecisionContext(
        basic_structured={"name": "Wise Sect"},
        basic_text="",
        identity={
            "purpose": "守正积势",
            "style": "行事果决",
            "orthodoxy_name": "仙道",
            "rule_desc": "不得勾结邪魔。",
        },
        power={},
        territory={},
        self_assessment={},
        economy={
            "treasury_pressure": "tight",
            "action_cost_notes": [
                "每成功招募一名新人会立即消耗 500 灵石，并增加后续年度成员供养支出。",
                "赐予功法会消耗宗门传承资源。",
            ],
        },
        relations=[],
        relations_summary="",
        history={"recent_events": [], "summary_text": ""},
        diplomacy_targets=[],
        active_wars=[],
        rule={"rule_id": "righteous_orthodoxy", "rule_desc": "不得勾结邪魔。"},
        recruitment_candidates=[
            {
                "avatar_id": rogue.id,
                "name": rogue.name,
                "alignment": str(rogue.alignment),
                "realm": str(rogue.cultivation_progress.realm),
                "magic_stone": int(rogue.magic_stone.value),
                "technique_name": "",
                "technique_grade": "",
                "technique_grade_rank": 0,
                "alignment_recruitable": True,
                "detailed_info": {"name": rogue.name, "bio": "detailed"},
            }
        ],
        member_candidates=[],
    )

    payload = {
        "thinking": "先观其人。",
        "recruit_avatar_ids": [rogue.id],
        "expel_avatar_ids": [],
        "reward_avatar_ids": [],
        "support_avatar_ids": [],
    }
    with patch.object(SectDecider, "_llm_available", return_value=True), patch(
        "src.classes.sect_decider.call_llm_with_task_name",
        new=AsyncMock(return_value=payload),
    ) as mock_llm:
        plan = await SectDecider._plan(sect, ctx, base_world, recruit_cost=500, support_amount=300)

    assert plan is not None
    infos = mock_llm.call_args.kwargs["infos"]
    assert "detailed_info" in infos["decision_context_info"]
    assert "bio" in infos["decision_context_info"]
    assert "守正积势" in infos["decision_context_info"]
    assert "传承资源" in infos["decision_context_info"]


@pytest.mark.asyncio
async def test_sect_decider_can_declare_war_from_llm_plan(base_world):
    sect = Sect(
        id=1,
        name="War Sect",
        desc="",
        member_act_style="",
        alignment=Alignment.RIGHTEOUS,
        headquarter=SectHeadQuarter(name="HQ", desc="", image=Path("")),
        technique_names=[],
        magic_stone=1000,
    )
    ctx = SectDecisionContext(
        basic_structured={"name": "War Sect"},
        basic_text="",
        power={},
        territory={},
        self_assessment={},
        economy={},
        relations=[],
        relations_summary="",
        history={"recent_events": [], "summary_text": ""},
        diplomacy_targets=[
            {
                "other_sect_id": 2,
                "other_sect_name": "Enemy Sect",
                "status": "peace",
                "war_months": 0,
                "peace_months": 12,
                "last_battle_month": None,
                "relation_value": -40,
            }
        ],
        active_wars=[],
        rule={},
        recruitment_candidates=[],
        member_candidates=[],
    )
    payload = {
        "thinking": "先压边界。",
        "declare_war_target_ids": [2],
        "seek_peace_target_ids": [],
        "recruit_avatar_ids": [],
        "expel_avatar_ids": [],
        "reward_avatar_ids": [],
        "support_avatar_ids": [],
    }
    with patch.object(SectDecider, "_llm_available", return_value=True), patch(
        "src.classes.sect_decider.call_llm_with_task_name",
        new=AsyncMock(return_value=payload),
    ):
        result = await SectDecider.decide(sect, ctx, base_world)

    assert base_world.are_sects_at_war(1, 2)
    assert result.war_declared_count == 1
    assert any("宣战" in event.content for event in result.events)


def test_sect_decider_llm_available_uses_runtime_config():
    mock_service = MagicMock()
    mock_service.get_llm_runtime_config.return_value = (
        type("Profile", (), {"base_url": "http://test", "model_name": "test-model", "fast_model_name": "test-fast"})(),
        "secret",
    )

    with patch("src.classes.sect_decider.get_settings_service", return_value=mock_service):
        assert SectDecider._llm_available() is True


@pytest.mark.asyncio
async def test_sect_decider_warns_when_llm_runtime_config_unavailable(base_world):
    sect = Sect(
        id=1,
        name="Warn Sect",
        desc="",
        member_act_style="",
        alignment=Alignment.RIGHTEOUS,
        headquarter=SectHeadQuarter(name="HQ", desc="", image=Path("")),
        technique_names=[],
        magic_stone=1000,
    )
    ctx = SectDecisionContext(
        basic_structured={"name": "Warn Sect"},
        basic_text="",
        identity={},
        power={},
        territory={},
        self_assessment={},
        economy={},
        relations=[],
        relations_summary="",
        history={"recent_events": [], "summary_text": ""},
        diplomacy_targets=[],
        active_wars=[],
        rule={},
        recruitment_candidates=[],
        member_candidates=[],
    )
    mock_service = MagicMock()
    mock_service.get_llm_runtime_config.return_value = (
        type("Profile", (), {"base_url": "", "model_name": "", "fast_model_name": ""})(),
        "",
    )

    with patch("src.classes.sect_decider.get_settings_service", return_value=mock_service), patch(
        "src.classes.sect_decider.get_logger"
    ) as mock_logger:
        plan = await SectDecider._plan(sect, ctx, base_world, recruit_cost=500, support_amount=300)

    assert plan is None
    assert "LLM runtime config unavailable" in mock_logger.return_value.logger.warning.call_args.args[-1]


@pytest.mark.asyncio
async def test_sect_decider_warns_when_llm_plan_call_fails(base_world):
    sect = Sect(
        id=1,
        name="Warn Sect",
        desc="",
        member_act_style="",
        alignment=Alignment.RIGHTEOUS,
        headquarter=SectHeadQuarter(name="HQ", desc="", image=Path("")),
        technique_names=[],
        magic_stone=1000,
    )
    ctx = SectDecisionContext(
        basic_structured={"name": "Warn Sect"},
        basic_text="",
        identity={},
        power={},
        territory={},
        self_assessment={},
        economy={},
        relations=[],
        relations_summary="",
        history={"recent_events": [], "summary_text": ""},
        diplomacy_targets=[],
        active_wars=[],
        rule={},
        recruitment_candidates=[],
        member_candidates=[],
    )
    mock_service = MagicMock()
    mock_service.get_llm_runtime_config.return_value = (
        type("Profile", (), {"base_url": "http://test", "model_name": "test-model", "fast_model_name": "test-fast"})(),
        "secret",
    )

    with patch("src.classes.sect_decider.get_settings_service", return_value=mock_service), patch(
        "src.classes.sect_decider.call_llm_with_task_name",
        new=AsyncMock(side_effect=RuntimeError("boom")),
    ), patch("src.classes.sect_decider.get_logger") as mock_logger:
        plan = await SectDecider._plan(sect, ctx, base_world, recruit_cost=500, support_amount=300)

    assert plan is None
    assert "LLM plan failed: boom" in mock_logger.return_value.logger.warning.call_args.args[-1]
