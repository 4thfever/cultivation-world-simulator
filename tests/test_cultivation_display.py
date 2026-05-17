from types import SimpleNamespace

from src.classes.race import get_race
from src.classes.core.orthodoxy import get_orthodoxy
from src.systems.cultivation import CultivationProgress
from src.systems.cultivation import Realm, Stage
from src.systems.cultivation_display import (
    build_avatar_cultivation_display,
    build_cultivation_display,
    resolve_cultivation_alias_profile,
)
from src.utils.df import game_configs


def _avatar(*, level: int, orthodoxy_id: str | None = None, race_id: str = "human"):
    return SimpleNamespace(
        cultivation_progress=CultivationProgress(level=level),
        orthodoxy=get_orthodoxy(orthodoxy_id) if orthodoxy_id else None,
        race=get_race(race_id),
    )


def test_same_level_uses_different_display_profiles():
    progress = CultivationProgress(level=42)

    canonical = build_cultivation_display(progress, profile_id="dao")
    martial = build_cultivation_display(progress, profile_id="wu")
    confucian = build_cultivation_display(progress, profile_id="confucianism")
    buddhist = build_cultivation_display(progress, profile_id="buddhism")
    yao = build_cultivation_display(progress, profile_id="yao")

    assert canonical["realm_id"] == "FOUNDATION_ESTABLISHMENT"
    assert canonical["stage_id"] == "MIDDLE_STAGE"
    assert canonical["display_full_name"] == "筑基中期"
    assert martial["display_full_name"] == "易筋中成"
    assert confucian["display_full_name"] == "明理中境"
    assert buddhist["display_full_name"] == "比丘中境"
    assert yao["display_full_name"] == "化形中期"

    for item in [canonical, martial, confucian, buddhist, yao]:
        assert item["canonical_full_name"] == "筑基中期"
        assert item["realm_id"] == "FOUNDATION_ESTABLISHMENT"
        assert item["stage_id"] == "MIDDLE_STAGE"


def test_avatar_profile_prefers_yao_race_over_orthodoxy():
    avatar = _avatar(level=65, orthodoxy_id="wu", race_id="fox")

    assert resolve_cultivation_alias_profile(avatar) == "yao"

    display = build_avatar_cultivation_display(avatar)
    assert display["profile_id"] == "yao"
    assert display["realm_id"] == "CORE_FORMATION"
    assert display["display_full_name"] == "妖丹初期"
    assert display["canonical_full_name"] == "金丹前期"


def test_avatar_profile_uses_orthodoxy_for_human_and_sanxiu_fallback():
    martial_avatar = _avatar(level=92, orthodoxy_id="wu")
    rogue_avatar = _avatar(level=12)

    martial_display = build_avatar_cultivation_display(martial_avatar)
    rogue_display = build_avatar_cultivation_display(rogue_avatar)

    assert martial_display["profile_id"] == "wu"
    assert martial_display["display_full_name"] == "武圣初成"
    assert martial_display["canonical_full_name"] == "元婴前期"

    assert rogue_display["profile_id"] == "sanxiu"
    assert rogue_display["display_full_name"] == "练气中期"
    assert rogue_display["realm_id"] == "QI_REFINEMENT"


def test_missing_profile_falls_back_to_canonical_dao_display():
    display = build_cultivation_display(CultivationProgress(level=31), profile_id="unknown")

    assert display["profile_id"] == "dao"
    assert display["display_full_name"] == "筑基前期"
    assert display["canonical_full_name"] == "筑基前期"


def test_cultivation_alias_config_covers_every_profile_realm_and_stage():
    profiles = {"dao", "sanxiu", "wu", "confucianism", "buddhism", "yao"}
    rows = game_configs["cultivation_alias"]
    keys = {
        (row["profile_id"], row["realm_key"], row["stage_key"])
        for row in rows
    }

    missing = [
        (profile_id, realm.value, stage.value)
        for profile_id in sorted(profiles)
        for realm in Realm
        for stage in Stage
        if (profile_id, realm.value, stage.value) not in keys
    ]

    assert missing == []
