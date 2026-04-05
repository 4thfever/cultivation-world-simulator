from src.classes.goldfinger import (
    build_goldfinger_story_hint,
    goldfingers_by_id,
    merge_story_prompt_with_goldfinger,
)


def _find_goldfinger_by_key(key: str):
    for goldfinger in goldfingers_by_id.values():
        if goldfinger.key == key:
            return goldfinger
    raise AssertionError(f"Goldfinger not found: {key}")


def test_goldfinger_configs_are_loaded():
    assert goldfingers_by_id
    assert _find_goldfinger_by_key("CHILD_OF_FORTUNE").name == "气运之子"
    assert _find_goldfinger_by_key("TRANSMIGRATOR").mechanism_type == "story_driven"


def test_goldfinger_effects_participate_in_breakdown(dummy_avatar):
    dummy_avatar.goldfinger = _find_goldfinger_by_key("CHILD_OF_FORTUNE")

    breakdown = dummy_avatar.get_effect_breakdown()

    assert any("气运之子" in source and effects.get("extra_luck") == 20 for source, effects in breakdown)


def test_avatar_structured_info_contains_goldfinger(dummy_avatar):
    dummy_avatar.goldfinger = _find_goldfinger_by_key("OLD_GRANDPA")
    dummy_avatar.goldfinger_state = {"mentor_mood": "stern"}

    info = dummy_avatar.get_structured_info()

    assert info["goldfinger"] is not None
    assert info["goldfinger"]["name"] == "随身老爷爷"
    assert info["goldfinger"]["mechanism_type"] == "story_driven"
    assert info["goldfinger"]["state"] == {"mentor_mood": "stern"}
    assert info["goldfinger"]["source_of_truth"] == "avatar.goldfinger"
    assert info["goldfinger"]["state_source_of_truth"] == "avatar.goldfinger_state"


def test_avatar_expanded_info_contains_structured_goldfinger_context(dummy_avatar):
    dummy_avatar.goldfinger = _find_goldfinger_by_key("TRANSMIGRATOR")
    dummy_avatar.goldfinger_state = {"story_focus": "modern_mindset"}

    info = dummy_avatar.get_expanded_info(detailed=True)

    assert info["goldfinger_context"] is not None
    assert info["goldfinger_context"]["name"] == "穿越者"
    assert info["goldfinger_context"]["story_prompt"] == dummy_avatar.goldfinger.story_prompt
    assert info["goldfinger_context"]["state"] == {"story_focus": "modern_mindset"}


def test_avatar_ai_context_uses_structured_goldfinger_source(dummy_avatar):
    from src.classes.core.avatar.info_presenter import get_avatar_ai_context

    dummy_avatar.goldfinger = _find_goldfinger_by_key("REINCARNATOR")
    dummy_avatar.goldfinger_state = {"last_regret": "late_breakthrough"}

    context = get_avatar_ai_context(dummy_avatar)

    assert context["self_profile"]["goldfinger"] is not None
    assert context["self_profile"]["goldfinger"]["name"] == "重生者"
    assert context["self_profile"]["goldfinger"]["state"] == {"last_regret": "late_breakthrough"}
    assert context["self_profile"]["goldfinger"]["source_of_truth"] == "avatar.goldfinger"


def test_build_goldfinger_story_hint_collects_all_actor_prompts(dummy_avatar):
    from src.classes.core.avatar import Avatar, Gender
    from src.classes.age import Age
    from src.systems.cultivation import Realm
    from src.utils.id_generator import get_avatar_id
    from src.classes.root import Root
    from src.classes.alignment import Alignment
    from src.systems.time import Month, Year, create_month_stamp

    dummy_avatar.goldfinger = _find_goldfinger_by_key("TRANSMIGRATOR")
    another_avatar = Avatar(
        world=dummy_avatar.world,
        name="SecondDummy",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(22, Realm.Qi_Refinement, innate_max_lifespan=80),
        gender=Gender.FEMALE,
        pos_x=1,
        pos_y=1,
        root=Root.WOOD,
        personas=[],
        alignment=Alignment.RIGHTEOUS,
    )
    another_avatar.goldfinger = _find_goldfinger_by_key("OLD_GRANDPA")

    hint = build_goldfinger_story_hint(dummy_avatar, another_avatar)

    assert "穿越者" in hint
    assert "随身老爷爷" in hint
    assert dummy_avatar.goldfinger.story_prompt in hint
    assert another_avatar.goldfinger.story_prompt in hint


def test_merge_story_prompt_with_goldfinger_preserves_base_prompt(dummy_avatar):
    dummy_avatar.goldfinger = _find_goldfinger_by_key("REINCARNATOR")

    merged = merge_story_prompt_with_goldfinger("基础故事提示", dummy_avatar)

    assert "基础故事提示" in merged
    assert "外挂相关重点" in merged
    assert "重生者" in merged
    assert dummy_avatar.goldfinger.story_prompt in merged
