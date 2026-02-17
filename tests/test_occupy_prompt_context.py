import pytest

from src.classes.core.avatar import Avatar, Gender
from src.classes.age import Age
from src.classes.environment.region import CultivateRegion, EssenceType
from src.classes.language import language_manager
from src.systems.cultivation import Realm
from src.systems.time import Year, Month, create_month_stamp
from src.utils.id_generator import get_avatar_id
from src.i18n import t


def _create_avatar(world, name: str, realm: Realm, x: int = 0, y: int = 0) -> Avatar:
    avatar = Avatar(
        world=world,
        name=name,
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, realm),
        gender=Gender.MALE,
        pos_x=x,
        pos_y=y,
        personas=[],
    )
    avatar.personas = []
    avatar.cultivation_progress.realm = realm
    return avatar


def test_world_info_includes_occupy_candidates_with_owner_and_gap(base_world, dummy_avatar):
    high_owner = _create_avatar(base_world, "HighOwner", Realm.Foundation_Establishment)

    occupied = CultivateRegion(
        id=101,
        name="Azure Cave",
        desc="occupied cave",
        essence_type=EssenceType.FIRE,
        essence_density=5,
    )
    occupied.host_avatar = high_owner

    unowned = CultivateRegion(
        id=102,
        name="Silent Ruin",
        desc="unowned ruin",
        essence_type=EssenceType.WATER,
        essence_density=3,
    )

    base_world.map.regions[occupied.id] = occupied
    base_world.map.regions[unowned.id] = unowned

    world_info = base_world.get_info(detailed=True, avatar=dummy_avatar)
    assert "Occupy Candidates" in world_info

    candidates = world_info["Occupy Candidates"]
    assert isinstance(candidates, list)

    by_region = {c["region_name"]: c for c in candidates}
    assert "Azure Cave" in by_region
    assert "Silent Ruin" in by_region

    occupied_info = by_region["Azure Cave"]
    assert occupied_info["owner_name"] == "HighOwner"
    assert occupied_info["your_realm"] == str(dummy_avatar.cultivation_progress.realm)
    assert occupied_info["owner_realm"] == str(high_owner.cultivation_progress.realm)
    assert occupied_info["major_realm_gap"] == 1
    assert "owner higher" in occupied_info["major_realm_gap_desc"]
    assert "severe injury/death" in occupied_info["risk_reminder"]

    unowned_info = by_region["Silent Ruin"]
    assert unowned_info["owner_name"] == "None"
    assert unowned_info["owner_realm"] == "None"
    assert unowned_info["major_realm_gap"] is None
    assert unowned_info["major_realm_gap_desc"] == "no owner"


def test_occupy_requirements_contains_risk_gap_and_persona_guidance_bilingual():
    original = str(language_manager)
    try:
        language_manager.set_language("zh-CN")
        zh_req = t("occupy_requirements")
        assert "Occupy Candidates" in zh_req
        assert "your_realm" in zh_req and "owner_realm" in zh_req
        assert "major_realm_gap_desc" in zh_req
        assert "重伤" in zh_req and "死亡" in zh_req
        assert "ADVENTUROUS" in zh_req and "TIMID" in zh_req

        language_manager.set_language("en-US")
        en_req = t("occupy_requirements")
        assert "Occupy Candidates" in en_req
        assert "your_realm" in en_req and "owner_realm" in en_req
        assert "major_realm_gap_desc" in en_req
        assert "severe injury" in en_req and "death" in en_req
        assert "ADVENTUROUS" in en_req and "TIMID" in en_req
    finally:
        language_manager.set_language(original)
