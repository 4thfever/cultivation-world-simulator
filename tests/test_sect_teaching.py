from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.classes.age import Age
from src.classes.alignment import Alignment
from src.classes.core.avatar.core import Avatar
from src.classes.core.sect import Sect, SectHeadQuarter
from src.classes.gender import Gender
from src.classes.gathering.sect_teaching import SectTeachingConference
from src.classes.sect_ranks import SectRank
from src.systems.cultivation import CultivationProgress
from src.systems.time import MonthStamp


def _create_member(world, sect, avatar_id: str, name: str, level: int, rank: SectRank) -> Avatar:
    avatar = Avatar(
        world=world,
        name=name,
        id=avatar_id,
        birth_month_stamp=MonthStamp(1),
        age=Age(18, realm=0),
        gender=Gender.MALE,
    )
    avatar.cultivation_progress = CultivationProgress(level)
    avatar.join_sect(sect, rank)
    avatar.is_dead = False
    world.avatar_manager.avatars[avatar.id] = avatar
    return avatar


def test_build_sect_teaching_context_text_summarizes_decision_context(base_world):
    world = base_world
    sect = Sect(
        id=1,
        name="明心剑宗",
        desc="守正明心",
        member_act_style="稳重",
        alignment=Alignment.NEUTRAL,
        headquarter=SectHeadQuarter(name="山门", desc="云海之间", image=Path("")),
        technique_names=[],
    )
    teacher = _create_member(world, sect, "teacher_1", "讲师甲", 61, SectRank.Elder)
    world.event_manager._storage = MagicMock()

    mock_ctx = MagicMock()
    mock_ctx.active_wars = [{"other_sect_name": "赤炎宗", "status": "war"}]
    mock_ctx.economy = {"treasury_pressure": "tight"}
    mock_ctx.self_assessment = {"war_readiness": "stretched", "alive_member_count": 7}
    mock_ctx.territory = {"border_pressure_ratio": 0.35, "tile_count": 12}
    mock_ctx.power = {"total_battle_strength": 88.0}

    conference = SectTeachingConference()
    with patch("src.classes.core.sect.get_sect_decision_context", return_value=mock_ctx):
        text = conference._build_sect_teaching_context_text(sect, teacher)

    assert "明心剑宗" in text
    assert "与 赤炎宗 交战中" in text
    assert "财库偏紧" in text
    assert "备战状态 stretched" in text
    assert "边境压力：35%" in text
    assert "存活门人 7 人" in text
    assert "总战力约 88" in text


@pytest.mark.asyncio
async def test_generate_story_uses_refined_sect_context_in_details(base_world):
    world = base_world
    sect = Sect(
        id=1,
        name="太虚门",
        desc="清静无为",
        member_act_style="淡然",
        alignment=Alignment.NEUTRAL,
        headquarter=SectHeadQuarter(name="云台", desc="高台观星", image=Path("")),
        technique_names=[],
    )
    teacher = _create_member(world, sect, "teacher_1", "师尊甲", 61, SectRank.Elder)
    student = _create_member(world, sect, "student_1", "弟子乙", 1, SectRank.OuterDisciple)

    conference = SectTeachingConference()
    with patch.object(
        conference,
        "_build_sect_teaching_context_text",
        return_value="【宗门背景】当前与玄霜宗交战，财库平稳。",
    ), patch(
        "src.classes.gathering.sect_teaching.StoryEventService.maybe_create_gathering_story",
        new=AsyncMock(return_value=None),
    ) as mock_story:
        await conference._generate_story(
            sect=sect,
            teacher=teacher,
            students=[student],
            exp_gains=[(student, 42)],
            epiphany_list=[],
            month_stamp=world.month_stamp,
        )

    details_text = mock_story.await_args.kwargs["details_text"]
    assert "【宗门背景】当前与玄霜宗交战，财库平稳。" in details_text
    assert "师尊甲:" in details_text
    assert "- 弟子乙:" in details_text
