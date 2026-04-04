from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.classes.action.catch import Catch
from src.classes.action.cooldown import cooldown_action
from src.classes.action.devour_people import DevourPeople
from src.classes.action.govern import Govern
from src.classes.action.targeting_mixin import TargetingMixin
from src.classes.event import Event
from src.classes.event_renderer import render_observed_event
from src.classes.items.auxiliary import Auxiliary
from src.classes.language import language_manager
from src.classes.relation.relation import Relation
from src.classes.relation.relation_resolver import RelationResolver
from src.systems.cultivation import Realm


class _DummyTargetingAction(TargetingMixin):
    def __init__(self, world, target=None):
        self.world = world
        self._target = target

    def find_avatar_by_name(self, name: str):
        return self._target


@cooldown_action
class _DemoCooldownAction:
    ACTION_CD_MONTHS = 3

    def __init__(self, avatar, world):
        self.avatar = avatar
        self.world = world

    def can_start(self):
        return True, ""


class _ResolverAvatar:
    def __init__(self, name: str, avatar_id: str, world):
        self.name = name
        self.id = avatar_id
        self.world = world
        self.relations = {}
        self.computed_relations = {}

    def get_relation(self, other):
        return None

    def get_info(self, detailed: bool = False):
        return {}

    def become_lovers_with(self, other):
        self.relations[other.id] = Relation.IS_LOVER_OF

    def set_relation(self, other, rel):
        self.relations[other.id] = rel

    def acknowledge_master(self, other):
        self.relations[other.id] = Relation.IS_MASTER_OF

    def accept_disciple(self, other):
        self.relations[other.id] = Relation.IS_DISCIPLE_OF

    def acknowledge_parent(self, other):
        self.relations[other.id] = Relation.IS_PARENT_OF

    def acknowledge_child(self, other):
        self.relations[other.id] = Relation.IS_CHILD_OF


def test_cooldown_reason_is_localized_in_english(dummy_avatar):
    original_lang = str(language_manager)
    try:
        language_manager.set_language("en-US")
        dummy_avatar._action_cd_last_months = {"_DemoCooldownAction": dummy_avatar.world.month_stamp - 1}
        action = _DemoCooldownAction(dummy_avatar, dummy_avatar.world)
        can_start, reason = action.can_start()
        assert can_start is False
        assert reason == "Action on cooldown, 2 month(s) remaining"
    finally:
        language_manager.set_language(original_lang)


def test_target_validation_reasons_are_localized_in_english(dummy_avatar):
    original_lang = str(language_manager)
    try:
        language_manager.set_language("en-US")
        action = _DummyTargetingAction(dummy_avatar.world)
        assert action.validate_target_avatar(None) == (None, False, "Missing target parameter")
        assert action.validate_target_avatar("ghost") == (None, False, "Target does not exist")

        dead_target = SimpleNamespace(is_dead=True)
        action = _DummyTargetingAction(dummy_avatar.world, target=dead_target)
        assert action.validate_target_avatar("ghost") == (None, False, "Target is already dead")
    finally:
        language_manager.set_language(original_lang)


@pytest.mark.asyncio
async def test_relation_resolver_event_text_is_localized_in_english(dummy_avatar):
    original_lang = str(language_manager)
    try:
        language_manager.set_language("en-US")
        world = SimpleNamespace(
            month_stamp=dummy_avatar.world.month_stamp,
            event_manager=SimpleNamespace(get_events_between=lambda *args, **kwargs: []),
        )
        avatar_a = _ResolverAvatar("Alpha", "a", world)
        avatar_b = _ResolverAvatar("Beta", "b", world)

        with patch(
            "src.classes.relation.relation_resolver.call_llm_with_task_name",
            new=AsyncMock(return_value={"changed": True, "change_type": "ADD", "relation": "IS_LOVER_OF", "reason": "shared hardship"}),
        ), patch("src.classes.relation.relation_resolver.configure_positive_bond_event"), patch(
            "src.classes.relation.relation_resolver.apply_positive_bond_warmth"
        ):
            event = await RelationResolver.resolve_pair(avatar_a, avatar_b)

        assert event is not None
        assert event.content == "Because shared hardship, Alpha became Beta's Lovers."
        assert "因为" not in event.content
    finally:
        language_manager.set_language(original_lang)


def test_observed_event_renderer_is_localized_in_english(dummy_avatar):
    original_lang = str(language_manager)
    try:
        language_manager.set_language("en-US")
        event = Event(
            dummy_avatar.world.month_stamp,
            "ignored",
            related_avatars=[dummy_avatar.id],
            event_type="bond_lovers_formed",
            render_params={
                "avatar_a_id": "a",
                "avatar_a_name": "Alpha",
                "avatar_b_id": "b",
                "avatar_b_name": "Beta",
                "bond_label_id": "bond_label_lovers",
            },
        )
        rendered = render_observed_event(
            event,
            {"propagation_kind": "close_relation_positive_bond", "subject_avatar_id": "a"},
        )
        assert rendered == "You learned that Alpha and Beta became Dao companions."
    finally:
        language_manager.set_language(original_lang)


def test_catch_uses_stable_sect_identifier(dummy_avatar):
    dummy_avatar.sect = SimpleNamespace(id=2, name_id="SECT_2_NAME", name="Beast Mountain")
    action = Catch(dummy_avatar, dummy_avatar.world)
    assert action.can_possibly_start() is True


@pytest.mark.asyncio
async def test_devour_people_uses_stable_auxiliary_identifier(avatar_in_city):
    auxiliary = Auxiliary(
        id=2064,
        name="Soul Banner",
        realm=Realm.Nascent_Soul,
        desc="test",
        name_id="AUXILIARY_2064_NAME",
        effects={},
        effect_desc="",
    )
    avatar_in_city.auxiliary = auxiliary
    before_population = avatar_in_city.tile.region.population
    action = DevourPeople(avatar_in_city, avatar_in_city.world)

    events = await action.finish()

    assert events == []
    assert auxiliary.special_data["devoured_souls"] > 0
    assert avatar_in_city.tile.region.population < before_population


@pytest.mark.asyncio
async def test_govern_story_prompt_is_localized_in_english(avatar_in_city):
    original_lang = str(language_manager)
    try:
        language_manager.set_language("en-US")
        avatar_in_city.official_rank = "COUNTY_MAGISTRATE"
        avatar_in_city.recalc_effects = MagicMock()
        action = Govern(avatar_in_city, avatar_in_city.world)

        with patch("src.classes.action.govern.calculate_governance_reputation_gain", return_value=3), \
             patch("src.classes.action.govern.get_governance_salary", return_value=10), \
             patch("src.classes.action.govern.apply_official_reputation_delta"), \
             patch("src.classes.action.govern.resolve_rank_changes", return_value=("COUNTY_MAGISTRATE", "COUNTY_MAGISTRATE")), \
             patch("src.classes.action.govern.StoryEventService.maybe_create_story", new=AsyncMock(return_value=None)) as mock_story:
            await action.finish()

        assert mock_story.await_args.kwargs["prompt"] == (
            "Focus on governance affairs, malevolent incidents, local strongmen, and political rivals creating obstacles."
        )
    finally:
        language_manager.set_language(original_lang)
