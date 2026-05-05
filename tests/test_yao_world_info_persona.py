from src.classes.persona import personas_by_name
from src.classes.race import get_race
from src.sim.avatar_init import _roll_social_initial_friendliness_pair


def test_world_info_contains_race_concept(base_world):
    info = base_world.static_info
    assert "种族" in info
    assert "狐、狼、鸟、蛇、龟" in info["种族"]


def test_cross_race_personas_loaded():
    kin = personas_by_name["亲近异类"]
    hate = personas_by_name["痛恨异类"]

    assert kin.effects["extra_cross_race_friendliness"] == 20
    assert hate.effects["extra_cross_race_friendliness"] == -25


def test_cross_race_friendliness_effect_changes_initial_bias(dummy_avatar, base_world, monkeypatch):
    from src.classes.core.avatar import Avatar, Gender
    from src.classes.age import Age
    from src.classes.alignment import Alignment
    from src.classes.root import Root
    from src.systems.cultivation import Realm
    from src.systems.time import Month, Year, create_month_stamp

    other = Avatar(
        world=base_world,
        name="Fox",
        id="fox",
        birth_month_stamp=create_month_stamp(Year(1), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement, innate_max_lifespan=80),
        gender=Gender.FEMALE,
        pos_x=0,
        pos_y=0,
        root=Root.GOLD,
        alignment=Alignment.NEUTRAL,
        race=get_race("fox"),
        personas=[],
    )
    dummy_avatar.race = get_race("human")
    dummy_avatar.personas = [personas_by_name["亲近异类"]]
    dummy_avatar.recalc_effects()
    other.personas = [personas_by_name["痛恨异类"]]
    other.recalc_effects()

    monkeypatch.setattr("src.sim.avatar_init._roll_social_initial_friendliness_pair_without_cross_race", lambda *_args: (0, 0))

    a_to_b, b_to_a = _roll_social_initial_friendliness_pair(dummy_avatar, other)

    assert a_to_b == 20
    assert b_to_a == -25
