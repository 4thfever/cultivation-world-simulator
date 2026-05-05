from src.classes.core.sect import sects_by_name
from src.classes.race import get_race
from src.classes.age import Age
from src.sim.avatar_init import (
    AvatarFactory,
    MortalPlan,
    PopulationPlanner,
    create_avatar_from_request,
    make_avatars,
)
from src.systems.cultivation import Realm
from src.systems.time import MonthStamp


def test_population_planner_assigns_only_accepting_sects_when_all_yao(monkeypatch):
    monkeypatch.setattr("src.sim.avatar_init.roll_avatar_race", lambda: get_race("fox"))
    academy = sects_by_name["浩然书院"]
    accepting = sects_by_name["凌霄剑宗"]

    plan = PopulationPlanner.plan_group(8, [academy, accepting])

    assert all(race.id == "fox" for race in plan.races)
    assert all(sect is not academy for sect in plan.sects if sect is not None)


def test_make_avatars_uses_yao_probability_and_respects_sect_policy(base_world, monkeypatch):
    monkeypatch.setattr("src.sim.avatar_init.roll_avatar_race", lambda: get_race("wolf"))
    academy = sects_by_name["浩然书院"]
    accepting = sects_by_name["凌霄剑宗"]

    avatars = make_avatars(base_world, count=6, current_month_stamp=MonthStamp(100 * 12), existed_sects=[academy, accepting])

    assert avatars
    assert {avatar.race.id for avatar in avatars.values()} == {"wolf"}
    assert all(avatar.sect is not academy for avatar in avatars.values())


def test_create_avatar_from_request_defaults_human_and_blocks_non_accepting_sect(base_world):
    academy = sects_by_name["浩然书院"]

    human_avatar = create_avatar_from_request(
        base_world,
        MonthStamp(100 * 12),
        name="Human",
        sect=academy,
    )
    yao_avatar = create_avatar_from_request(
        base_world,
        MonthStamp(100 * 12),
        name="Fox",
        race="fox",
        sect=academy,
    )

    assert human_avatar.race.id == "human"
    assert human_avatar.sect is academy
    assert yao_avatar.race.id == "fox"
    assert yao_avatar.sect is None


def test_yao_random_name_uses_race_surname(base_world):
    avatar = create_avatar_from_request(
        base_world,
        MonthStamp(100 * 12),
        race="snake",
    )

    assert avatar.race.id == "snake"
    assert avatar.name.startswith("蛇")


def test_avatar_factory_build_from_plan_applies_race(base_world):
    plan = MortalPlan(race=get_race("turtle"))

    avatar = AvatarFactory.build_from_plan(
        base_world,
        MonthStamp(100 * 12),
        name="Turtle",
        age=Age(20, Realm.Qi_Refinement, innate_max_lifespan=120),
        plan=plan,
        attach_relations=False,
        allow_random_goldfinger=False,
    )

    assert avatar.race.id == "turtle"
    assert avatar.effects.get("extra_max_lifespan") == 80
