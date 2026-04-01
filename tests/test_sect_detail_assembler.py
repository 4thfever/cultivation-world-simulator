from pathlib import Path

from src.classes.alignment import Alignment
from src.classes.core.sect import Sect, SectHeadQuarter
from src.classes.sect_ranks import get_rank_from_realm
from src.server.assemblers.sect_detail import build_sect_detail


def test_build_sect_detail_includes_yearly_income_and_upkeep(base_world):
    from src.classes.core.avatar import Avatar
    from src.classes.age import Age
    from src.classes.gender import Gender
    from src.classes.environment.sect_region import SectRegion
    from src.systems.cultivation import CultivationProgress
    from src.systems.time import MonthStamp

    world = base_world
    region_id = 1001
    cors = [(1, 1)]
    region = SectRegion(id=region_id, name="R1", desc="", sect_id=1, sect_name="测试宗门", cors=cors)
    world.map.regions[region_id] = region
    world.map.region_cors[region_id] = cors
    world.map.update_sect_regions()

    sect = Sect(
        id=1,
        name="测试宗门",
        desc="稳住传承",
        member_act_style="",
        alignment=Alignment.NEUTRAL,
        headquarter=SectHeadQuarter(name="驻地", desc="", image=Path("")),
        technique_names=[],
    )
    sect.set_war_weariness(27)
    world.existed_sects = [sect]
    world.sect_context.from_existed_sects(world.existed_sects)

    member = Avatar(
        world=world,
        name="弟子甲",
        id="member_a",
        birth_month_stamp=MonthStamp(1),
        age=Age(18, realm=0),
        gender=Gender.MALE,
    )
    member.cultivation_progress = CultivationProgress(1)
    member.join_sect(sect, get_rank_from_realm(member.cultivation_progress.realm))
    member.is_dead = False
    world.avatar_manager.avatars[member.id] = member

    detail = build_sect_detail(sect, world, object())

    summary = detail["economy_summary"]
    assert "estimated_yearly_income" in summary
    assert "estimated_yearly_upkeep" in summary
    assert summary["estimated_yearly_income"] > 0
    assert summary["estimated_yearly_upkeep"] == 15
    assert detail["war_weariness"] == 27
