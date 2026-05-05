import re

from src.classes.core.avatar import Avatar, Gender
from src.classes.race import get_race, is_yao_avatar, roll_avatar_race
from src.classes.age import Age
from src.classes.alignment import Alignment
from src.classes.core.sect import sects_by_name
from src.classes.sect_ranks import SectRank
from src.classes.language import language_manager
from src.i18n import reload_translations
from src.systems.cultivation import Realm
from src.systems.time import Month, Year, create_month_stamp
from src.classes.root import Root


def _make_avatar(world, *, race_id: str = "human") -> Avatar:
    avatar = Avatar(
        world=world,
        name=f"{race_id}-avatar",
        id=f"{race_id}-avatar",
        birth_month_stamp=create_month_stamp(Year(1), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement, innate_max_lifespan=80),
        gender=Gender.MALE,
        pos_x=0,
        pos_y=0,
        root=Root.GOLD,
        alignment=Alignment.NEUTRAL,
        race=get_race(race_id),
        personas=[],
    )
    avatar.personas = []
    avatar.technique = None
    avatar.recalc_effects()
    return avatar


def test_race_config_loads_human_and_yao_effects(base_world):
    human = get_race("human")
    wolf = get_race("wolf")

    assert human.id == "human"
    assert human.effects == {}
    assert human.get_info(detailed=True)["desc"] == "你是一个普通的人类"

    avatar = _make_avatar(base_world, race_id="wolf")
    assert is_yao_avatar(avatar)
    assert avatar.effects.get("extra_battle_strength_points") == 2
    assert avatar.effects.get("extra_hunt_materials") == 2
    assert avatar.effects.get("extra_eat_mortals_exp_multiplier") == 0.5
    assert wolf.get_info()["name"] == "狼族"


def test_roll_avatar_race_probability_edges():
    assert roll_avatar_race(probability=0).id == "human"
    assert roll_avatar_race(probability=1).is_yao


def test_sect_race_policy_blocks_haoran_academy(base_world):
    academy = sects_by_name["浩然书院"]
    wolf_avatar = _make_avatar(base_world, race_id="wolf")
    human_avatar = _make_avatar(base_world, race_id="human")

    assert academy.accept_yao is False
    assert academy.accepts_avatar_race(wolf_avatar) is False
    assert academy.accepts_avatar_race(human_avatar) is True

    wolf_avatar.join_sect(academy, SectRank.OuterDisciple)
    assert wolf_avatar.sect is None

    human_avatar.join_sect(academy, SectRank.OuterDisciple)
    assert human_avatar.sect is academy


def _contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def test_english_race_detail_and_effect_text_have_no_chinese():
    original_lang = str(language_manager.current)
    try:
        language_manager.set_language("en-US")
        reload_translations()

        from src.classes.race import get_race, reload as reload_races

        reload_races()
        wolf_info = get_race("wolf").get_info(detailed=True)

        assert wolf_info["name"] == "Wolf Yao"
        assert not _contains_chinese(wolf_info["type_name"])
        assert not _contains_chinese(wolf_info["desc"])
        assert not _contains_chinese(wolf_info["effect_desc"])
        assert "Battle Strength" in wolf_info["effect_desc"]
        assert "Eat Mortals" in wolf_info["effect_desc"] or "mortal" in wolf_info["effect_desc"].lower()
    finally:
        language_manager.set_language(original_lang)
        reload_translations()
        from src.classes.race import reload as reload_races

        reload_races()
