"""
Tests for src/classes/mutual_action/ modules.

This module tests mutual action classes including:
- Talk: initiate conversation
- Spar: friendly combat for weapon proficiency
- Impart: master teaching disciple

Testing Strategy:
    We mock `call_llm_with_task_name` to simulate LLM feedback responses.
    This allows testing the action logic without actual LLM calls.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.classes.mutual_action.talk import Talk
from src.classes.mutual_action.spar import Spar
from src.classes.mutual_action.impart import Impart
from src.classes.mutual_action.confess import Confess
from src.classes.mutual_action.swear_brotherhood import SwearBrotherhood
from src.classes.action_runtime import ActionStatus
from src.classes.relation.relation import Relation


class TestTalk:
    """Tests for Talk mutual action."""

    @pytest.fixture
    def target_avatar(self, base_world, dummy_avatar):
        """Create a target avatar for talk tests."""
        from src.classes.core.avatar import Avatar, Gender
        from src.classes.age import Age
        from src.systems.cultivation import Realm
        from src.systems.time import Year, Month, create_month_stamp
        from src.classes.root import Root
        from src.classes.alignment import Alignment
        from src.utils.id_generator import get_avatar_id

        target = Avatar(
            world=base_world,
            name="TalkTarget",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
            age=Age(25, Realm.Qi_Refinement),
            gender=Gender.FEMALE,
            pos_x=0,  # Same position as dummy_avatar
            pos_y=0,
            root=Root.WATER,
            personas=[],
            alignment=Alignment.NEUTRAL
        )
        target.weapon = MagicMock()
        target.weapon.get_detailed_info.return_value = "Test Weapon"
        target.thinking = ""
        target.short_term_objective = ""
        # Register in world
        base_world.avatar_manager.avatars[target.name] = target
        return target

    def test_talk_can_start_success(self, dummy_avatar, target_avatar):
        """Test that Talk can start when target is in observation range."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        
        with patch("src.classes.observe.is_within_observation", return_value=True):
            can_start, reason = action.can_start(target_avatar)
        
        assert can_start is True
        assert reason == ""

    def test_talk_cannot_start_target_not_in_range(self, dummy_avatar, target_avatar):
        """Test that Talk cannot start when target is out of range."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        
        with patch("src.classes.observe.is_within_observation", return_value=False):
            can_start, reason = action.can_start(target_avatar)
        
        assert can_start is False
        assert "不在交互范围内" in reason

    def test_talk_cannot_start_self_target(self, dummy_avatar):
        """Test that Talk cannot target self."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        can_start, reason = action.can_start(dummy_avatar)
        
        assert can_start is False
        assert "自己" in reason

    def test_talk_cannot_start_target_not_exist(self, dummy_avatar):
        """Test that Talk cannot start with non-existent target."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        can_start, reason = action.can_start("NonExistentAvatar")
        
        assert can_start is False
        assert "不存在" in reason

    def test_talk_start_returns_event(self, dummy_avatar, target_avatar):
        """Test that Talk.start() returns proper event."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        event = action.start(target_avatar)
        
        assert event is not None
        assert dummy_avatar.name in event.content
        assert target_avatar.name in event.content
        assert "攀谈" in event.content
        assert dummy_avatar.id in event.related_avatars
        assert target_avatar.id in event.related_avatars

    @pytest.mark.asyncio
    async def test_talk_step_with_accept_feedback(self, dummy_avatar, target_avatar):
        """Test Talk step flow when target accepts."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        action._start_month_stamp = 100
        
        # Mock target's methods for loading action chain
        target_avatar.load_decide_result_chain = MagicMock()
        target_avatar.commit_next_plan = MagicMock(return_value=None)
        
        mock_response = {
            target_avatar.name: {
                "thinking": "This person seems friendly.",
                "feedback": "Talk"
            }
        }
        
        with patch("src.classes.observe.is_within_observation", return_value=True):
            with patch("src.classes.mutual_action.mutual_action.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = mock_response
                
                # First step: trigger LLM task
                res1 = action.step(target_avatar)
                assert res1.status == ActionStatus.RUNNING
                assert action._feedback_task is not None
                
                # Wait for task
                await action._feedback_task
                
                # Second step: consume result
                res2 = action.step(target_avatar)
                assert res2.status == ActionStatus.COMPLETED
                
                # Should have accept event
                assert len(res2.events) >= 1
                assert "接受" in res2.events[0].content

    @pytest.mark.asyncio
    async def test_talk_step_with_reject_feedback(self, dummy_avatar, target_avatar):
        """Test Talk step flow when target rejects."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        action._start_month_stamp = 100
        
        mock_response = {
            target_avatar.name: {
                "thinking": "I don't want to talk.",
                "feedback": "Reject"
            }
        }
        
        with patch("src.classes.observe.is_within_observation", return_value=True):
            with patch("src.classes.mutual_action.mutual_action.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = mock_response
                
                res1 = action.step(target_avatar)
                assert action._feedback_task is not None
                await action._feedback_task
                res2 = action.step(target_avatar)
                
                assert res2.status == ActionStatus.COMPLETED
                assert len(res2.events) >= 1
                assert "拒绝" in res2.events[0].content

    def test_talk_step_with_none_target(self, dummy_avatar):
        """Test Talk step with None target returns FAILED."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        res = action.step(None)  # type: ignore[arg-type] - intentionally testing None input
        
        assert res.status == ActionStatus.FAILED


class TestSpar:
    """Tests for Spar mutual action."""

    @pytest.fixture
    def target_avatar(self, base_world, dummy_avatar):
        """Create a target avatar for spar tests."""
        from src.classes.core.avatar import Avatar, Gender
        from src.classes.age import Age
        from src.systems.cultivation import Realm
        from src.systems.time import Year, Month, create_month_stamp
        from src.classes.root import Root
        from src.classes.alignment import Alignment
        from src.utils.id_generator import get_avatar_id

        target = Avatar(
            world=base_world,
            name="SparTarget",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
            age=Age(25, Realm.Qi_Refinement),
            gender=Gender.MALE,
            pos_x=0,
            pos_y=0,
            root=Root.FIRE,
            personas=[],
            alignment=Alignment.NEUTRAL
        )
        target.weapon = MagicMock()
        target.weapon.get_detailed_info.return_value = "Test Sword"
        target.weapon_proficiency = 50.0
        target.thinking = ""
        target.short_term_objective = ""
        # Mock methods for spar
        target.increase_weapon_proficiency = MagicMock()
        target.add_event = MagicMock()
        base_world.avatar_manager.avatars[target.name] = target
        return target

    def test_spar_has_cooldown(self):
        """Test that Spar has cooldown configured."""
        assert Spar.ACTION_CD_MONTHS == 12

    def test_spar_start_returns_event(self, dummy_avatar, target_avatar):
        """Test that Spar.start() returns proper event."""
        action = Spar(dummy_avatar, dummy_avatar.world)
        event = action.start(target_avatar)
        
        assert event is not None
        assert dummy_avatar.name in event.content
        assert target_avatar.name in event.content
        assert "切磋" in event.content

    def test_spar_settle_feedback_accept(self, dummy_avatar, target_avatar):
        """Test that accepting spar increases weapon proficiency."""
        action = Spar(dummy_avatar, dummy_avatar.world)
        dummy_avatar.increase_weapon_proficiency = MagicMock()
        dummy_avatar.add_event = MagicMock()
        
        # Mock battle result
        with patch("src.classes.mutual_action.spar.decide_battle") as mock_battle:
            mock_battle.return_value = (dummy_avatar, target_avatar, 0, 0)
            
            action._settle_feedback(target_avatar, "Accept")
            
            # Both should have proficiency increased
            dummy_avatar.increase_weapon_proficiency.assert_called_once()
            target_avatar.increase_weapon_proficiency.assert_called_once()
            
            # Winner (dummy_avatar) should get more
            winner_gain = dummy_avatar.increase_weapon_proficiency.call_args[0][0]
            loser_gain = target_avatar.increase_weapon_proficiency.call_args[0][0]
            assert winner_gain > loser_gain

    def test_spar_settle_feedback_reject(self, dummy_avatar, target_avatar):
        """Test that rejecting spar does nothing."""
        action = Spar(dummy_avatar, dummy_avatar.world)
        dummy_avatar.increase_weapon_proficiency = MagicMock()
        
        action._settle_feedback(target_avatar, "Reject")
        
        # Should not increase proficiency
        dummy_avatar.increase_weapon_proficiency.assert_not_called()
        target_avatar.increase_weapon_proficiency.assert_not_called()

    @pytest.mark.asyncio
    async def test_spar_finish_generates_story(self, dummy_avatar, target_avatar):
        """Test that Spar.finish() generates a story event.
        
        Note: cooldown_action decorator wraps finish() to use **kwargs,
        so we must call with keyword arguments.
        """
        action = Spar(dummy_avatar, dummy_avatar.world)
        action._last_result = (dummy_avatar, target_avatar, 15.0, 5.0)
        
        with patch("src.classes.mutual_action.spar.StoryTeller.tell_story", new_callable=AsyncMock) as mock_story:
            mock_story.return_value = "A great sparring match occurred."
            
            # cooldown_action wraps finish to accept **kwargs
            result = action.finish(target_avatar=target_avatar)
            events = await result  # The wrapper returns coroutine
            
            assert len(events) == 1
            assert events[0].is_story is True
            assert "great sparring match" in events[0].content

    @pytest.mark.asyncio
    async def test_spar_finish_without_result(self, dummy_avatar, target_avatar):
        """Test that Spar.finish() returns empty list without result."""
        action = Spar(dummy_avatar, dummy_avatar.world)
        # No _last_result set
        
        # cooldown_action wraps finish to accept **kwargs
        result = action.finish(target_avatar=target_avatar)
        events = await result
        
        assert events == []


class TestImpart:
    """Tests for Impart mutual action."""

    @pytest.fixture
    def master_avatar(self, base_world):
        """Create a master avatar (high level).
        
        Note: Avatar's cultivation_progress defaults to level 0.
        We must manually set level to ensure level diff >= 20 for Impart.
        """
        from src.classes.core.avatar import Avatar, Gender
        from src.classes.age import Age
        from src.systems.cultivation import Realm, CultivationProgress
        from src.systems.time import Year, Month, create_month_stamp
        from src.classes.root import Root
        from src.classes.alignment import Alignment
        from src.utils.id_generator import get_avatar_id

        master = Avatar(
            world=base_world,
            name="MasterAvatar",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(1900), Month.JANUARY),
            age=Age(100, Realm.Nascent_Soul),
            gender=Gender.MALE,
            pos_x=0,
            pos_y=0,
            root=Root.GOLD,
            personas=[],
            alignment=Alignment.RIGHTEOUS
        )
        # Set high cultivation level (Nascent Soul = 91+)
        master.cultivation_progress = CultivationProgress(level=95, exp=0)
        master.weapon = MagicMock()
        master.weapon.get_detailed_info.return_value = "Master Sword"
        master.thinking = ""
        master.short_term_objective = ""
        base_world.avatar_manager.avatars[master.name] = master
        return master

    @pytest.fixture
    def disciple_avatar(self, base_world):
        """Create a disciple avatar (low level)."""
        from src.classes.core.avatar import Avatar, Gender
        from src.classes.age import Age
        from src.systems.cultivation import Realm, CultivationProgress
        from src.systems.time import Year, Month, create_month_stamp
        from src.classes.root import Root
        from src.classes.alignment import Alignment
        from src.utils.id_generator import get_avatar_id

        disciple = Avatar(
            world=base_world,
            name="DiscipleAvatar",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
            age=Age(20, Realm.Qi_Refinement),
            gender=Gender.FEMALE,
            pos_x=0,
            pos_y=0,
            root=Root.WATER,
            personas=[],
            alignment=Alignment.RIGHTEOUS
        )
        # Set low cultivation level (Qi Refinement = 1-30)
        disciple.cultivation_progress = CultivationProgress(level=10, exp=0)
        disciple.weapon = MagicMock()
        disciple.weapon.get_detailed_info.return_value = "Disciple Sword"
        disciple.thinking = ""
        disciple.short_term_objective = ""
        disciple.add_event = MagicMock()
        base_world.avatar_manager.avatars[disciple.name] = disciple
        return disciple

    def test_impart_has_cooldown(self):
        """Test that Impart has cooldown configured."""
        assert Impart.ACTION_CD_MONTHS == 6

    def test_impart_can_start_success(self, master_avatar, disciple_avatar):
        """Test Impart can start with valid master-disciple relation."""
        action = Impart(master_avatar, master_avatar.world)
        
        # Mock relation check: master has MASTER relation to disciple
        master_avatar.get_relation = MagicMock(return_value=Relation.IS_DISCIPLE_OF)
        
        with patch("src.classes.observe.is_within_observation", return_value=True):
            can_start, reason = action.can_start(target_avatar=disciple_avatar)
        
        assert can_start is True
        assert reason == ""

    def test_impart_cannot_start_not_allowed_relation(self, master_avatar, disciple_avatar):
        """Test Impart cannot start when target is not in allowed relations."""
        action = Impart(master_avatar, master_avatar.world)
        
        # Mock relation check: not allowed
        master_avatar.get_relation = MagicMock(return_value=Relation.IS_ENEMY_OF)
        
        with patch("src.classes.observe.is_within_observation", return_value=True):
            can_start, reason = action.can_start(target_avatar=disciple_avatar)
        
        assert can_start is False
        assert "目标不是你的徒弟" in reason

    def test_impart_cannot_start_level_diff_too_small(self, master_avatar, disciple_avatar):
        """Test Impart cannot start when level difference < 20."""
        action = Impart(master_avatar, master_avatar.world)
        
        # Mock relation check
        master_avatar.get_relation = MagicMock(return_value=Relation.IS_DISCIPLE_OF)
        
        # Set levels close together
        master_avatar.cultivation_progress.level = 25
        disciple_avatar.cultivation_progress.level = 10  # Diff = 15 < 20
        
        with patch("src.classes.observe.is_within_observation", return_value=True):
            can_start, reason = action.can_start(target_avatar=disciple_avatar)
        
        assert can_start is False
        assert "等级差不足20级" in reason

    def test_impart_cannot_start_target_not_in_range(self, master_avatar, disciple_avatar):
        """Test Impart cannot start when target out of range."""
        action = Impart(master_avatar, master_avatar.world)
        
        master_avatar.get_relation = MagicMock(return_value=Relation.IS_DISCIPLE_OF)
        
        with patch("src.classes.observe.is_within_observation", return_value=False):
            can_start, reason = action.can_start(target_avatar=disciple_avatar)
        
        assert can_start is False
        assert "不在交互范围内" in reason

    def test_impart_start_returns_event(self, master_avatar, disciple_avatar):
        """Test that Impart.start() returns proper event."""
        action = Impart(master_avatar, master_avatar.world)
        event = action.start(disciple_avatar)
        
        assert event is not None
        assert master_avatar.name in event.content
        assert disciple_avatar.name in event.content
        assert "传道" in event.content
        assert hasattr(action, '_impart_success')
        assert action._impart_success is False

    def test_impart_settle_feedback_accept(self, master_avatar, disciple_avatar):
        """Test that accepting impart gives exp to disciple."""
        action = Impart(master_avatar, master_avatar.world)
        action._impart_success = False
        action._impart_exp_gain = 0
        
        initial_exp = disciple_avatar.cultivation_progress.exp
        
        action._settle_feedback(disciple_avatar, "Accept")
        
        assert action._impart_success is True
        assert action._impart_exp_gain == 2000  # 100 * 5 * 4
        # Exp should be added to disciple
        assert disciple_avatar.cultivation_progress.exp > initial_exp

    def test_impart_settle_feedback_reject(self, master_avatar, disciple_avatar):
        """Test that rejecting impart does not give exp."""
        action = Impart(master_avatar, master_avatar.world)
        action._impart_success = False
        action._impart_exp_gain = 0
        
        initial_exp = disciple_avatar.cultivation_progress.exp
        
        action._settle_feedback(disciple_avatar, "Reject")
        
        assert action._impart_success is False
        # Exp should not change
        assert disciple_avatar.cultivation_progress.exp == initial_exp

    @pytest.mark.asyncio
    async def test_impart_finish_with_success(self, master_avatar, disciple_avatar):
        """Test Impart.finish() generates result event on success.
        
        Note: cooldown_action decorator wraps finish() to use **kwargs.
        """
        action = Impart(master_avatar, master_avatar.world)
        action._impart_success = True
        action._impart_exp_gain = 2000
        
        # cooldown_action wraps finish to accept **kwargs
        result = action.finish(target_avatar=disciple_avatar)
        events = await result
        
        assert len(events) == 1
        assert "2000" in events[0].content
        assert disciple_avatar.name in events[0].content

    @pytest.mark.asyncio
    async def test_impart_finish_with_failure(self, master_avatar, disciple_avatar):
        """Test Impart.finish() returns empty on rejection."""
        action = Impart(master_avatar, master_avatar.world)
        action._impart_success = False
        action._impart_exp_gain = 0
        
        # cooldown_action wraps finish to accept **kwargs
        result = action.finish(target_avatar=disciple_avatar)
        events = await result
        
        assert events == []


class TestConfess:
    """Tests for Confess mutual action."""

    @pytest.fixture
    def target_avatar(self, base_world, dummy_avatar):
        """Create a target avatar for confess tests."""
        from src.classes.core.avatar import Avatar, Gender
        from src.classes.age import Age
        from src.systems.cultivation import Realm
        from src.systems.time import Year, Month, create_month_stamp
        from src.classes.root import Root
        from src.classes.alignment import Alignment
        from src.utils.id_generator import get_avatar_id

        target = Avatar(
            world=base_world,
            name="ConfessTarget",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
            age=Age(25, Realm.Qi_Refinement),
            gender=Gender.FEMALE,
            pos_x=0,
            pos_y=0,
            root=Root.WATER,
            personas=[],
            alignment=Alignment.NEUTRAL
        )
        target.weapon = MagicMock()
        target.weapon.get_detailed_info.return_value = "Test Weapon"
        target.thinking = ""
        target.short_term_objective = ""
        base_world.avatar_manager.avatars[target.name] = target
        return target

    def test_confess_has_cooldown(self):
        """Test that Confess has cooldown configured."""
        assert Confess.ACTION_CD_MONTHS == 6

    def test_confess_can_start_success(self, dummy_avatar, target_avatar):
        """Test Confess can start when target is in range and not already lovers."""
        action = Confess(dummy_avatar, dummy_avatar.world)
        dummy_avatar.get_relation = MagicMock(return_value=None)
        
        with patch("src.classes.observe.is_within_observation", return_value=True):
            can_start, reason = action.can_start(target_avatar=target_avatar)
        
        assert can_start is True
        assert reason == ""

    def test_confess_cannot_start_already_lovers(self, dummy_avatar, target_avatar):
        """Test Confess cannot start when already lovers."""
        from src.i18n import t
        action = Confess(dummy_avatar, dummy_avatar.world)
        dummy_avatar.get_relation = MagicMock(return_value=Relation.IS_LOVER_OF)
        
        with patch("src.classes.observe.is_within_observation", return_value=True):
            can_start, reason = action.can_start(target_avatar=target_avatar)
        
        assert can_start is False
        assert t("Already lovers") in reason

    def test_confess_start_returns_event(self, dummy_avatar, target_avatar):
        """Test that Confess.start() returns proper major event."""
        action = Confess(dummy_avatar, dummy_avatar.world)
        event = action.start(target_avatar)
        
        assert event is not None
        assert dummy_avatar.name in event.content
        assert target_avatar.name in event.content
        assert dummy_avatar.id in event.related_avatars
        assert target_avatar.id in event.related_avatars
        assert event.is_major is True
        assert hasattr(action, '_confess_success')
        assert action._confess_success is False

    def test_confess_settle_feedback_accept(self, dummy_avatar, target_avatar):
        """Test that accepting confession updates relation."""
        action = Confess(dummy_avatar, dummy_avatar.world)
        dummy_avatar.become_lovers_with = MagicMock()
        
        action._settle_feedback(target_avatar, "Accept")
        
        dummy_avatar.become_lovers_with.assert_called_once_with(target_avatar)
        assert action._confess_success is True

    def test_confess_settle_feedback_reject(self, dummy_avatar, target_avatar):
        """Test that rejecting confession does not update relation."""
        action = Confess(dummy_avatar, dummy_avatar.world)
        dummy_avatar.become_lovers_with = MagicMock()
        
        action._settle_feedback(target_avatar, "Reject")
        
        dummy_avatar.become_lovers_with.assert_not_called()
        assert action._confess_success is False

    @pytest.mark.asyncio
    async def test_confess_finish_generates_story(self, dummy_avatar, target_avatar):
        """Test Confess.finish() generates result and story events."""
        action = Confess(dummy_avatar, dummy_avatar.world)
        action._confess_success = True
        
        with patch("src.classes.mutual_action.confess.StoryTeller.tell_story", new_callable=AsyncMock) as mock_story:
            mock_story.return_value = "A romantic confession story."
            
            # cooldown_action wraps finish to accept **kwargs
            result = action.finish(target_avatar=target_avatar)
            events = await result
            
            assert len(events) == 2
            assert events[0].is_major is True
            assert events[1].is_story is True
            assert "A romantic confession story." in events[1].content


class TestSwearBrotherhood:
    """Tests for SwearBrotherhood mutual action."""

    @pytest.fixture
    def target_avatar(self, base_world, dummy_avatar):
        """Create a target avatar for swear brotherhood tests."""
        from src.classes.core.avatar import Avatar, Gender
        from src.classes.age import Age
        from src.systems.cultivation import Realm
        from src.systems.time import Year, Month, create_month_stamp
        from src.classes.root import Root
        from src.classes.alignment import Alignment
        from src.utils.id_generator import get_avatar_id

        target = Avatar(
            world=base_world,
            name="SwearTarget",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
            age=Age(25, Realm.Qi_Refinement),
            gender=Gender.MALE,
            pos_x=0,
            pos_y=0,
            root=Root.FIRE,
            personas=[],
            alignment=Alignment.NEUTRAL
        )
        target.weapon = MagicMock()
        target.weapon.get_detailed_info.return_value = "Test Weapon"
        target.thinking = ""
        target.short_term_objective = ""
        base_world.avatar_manager.avatars[target.name] = target
        return target

    def test_swear_has_cooldown(self):
        """Test that SwearBrotherhood has cooldown configured."""
        assert SwearBrotherhood.ACTION_CD_MONTHS == 6

    def test_swear_can_start_success(self, dummy_avatar, target_avatar):
        """Test SwearBrotherhood can start when target is in range and not already sworn siblings."""
        action = SwearBrotherhood(dummy_avatar, dummy_avatar.world)
        dummy_avatar.get_relation = MagicMock(return_value=Relation.IS_FRIEND_OF)
        
        with patch("src.classes.observe.is_within_observation", return_value=True):
            can_start, reason = action.can_start(target_avatar=target_avatar)
        
        assert can_start is True
        assert reason == ""

    def test_swear_cannot_start_already_sworn(self, dummy_avatar, target_avatar):
        """Test SwearBrotherhood cannot start when already sworn siblings."""
        from src.i18n import t
        action = SwearBrotherhood(dummy_avatar, dummy_avatar.world)
        dummy_avatar.get_relation = MagicMock(return_value=Relation.IS_SWORN_SIBLING_OF)
        
        with patch("src.classes.observe.is_within_observation", return_value=True):
            can_start, reason = action.can_start(target_avatar=target_avatar)
        
        assert can_start is False
        assert t("Already sworn siblings") in reason

    def test_swear_start_returns_event(self, dummy_avatar, target_avatar):
        """Test that SwearBrotherhood.start() returns proper major event."""
        action = SwearBrotherhood(dummy_avatar, dummy_avatar.world)
        event = action.start(target_avatar)
        
        assert event is not None
        assert dummy_avatar.name in event.content
        assert target_avatar.name in event.content
        assert dummy_avatar.id in event.related_avatars
        assert target_avatar.id in event.related_avatars
        assert event.is_major is True
        assert hasattr(action, '_swear_success')
        assert action._swear_success is False

    def test_swear_settle_feedback_accept(self, dummy_avatar, target_avatar):
        """Test that accepting swear brotherhood updates relation."""
        action = SwearBrotherhood(dummy_avatar, dummy_avatar.world)
        dummy_avatar.become_sworn_sibling_with = MagicMock()
        
        action._settle_feedback(target_avatar, "Accept")
        
        dummy_avatar.become_sworn_sibling_with.assert_called_once_with(target_avatar)
        assert action._swear_success is True

    def test_swear_settle_feedback_reject(self, dummy_avatar, target_avatar):
        """Test that rejecting swear brotherhood does not update relation."""
        action = SwearBrotherhood(dummy_avatar, dummy_avatar.world)
        dummy_avatar.become_sworn_sibling_with = MagicMock()
        
        action._settle_feedback(target_avatar, "Reject")
        
        dummy_avatar.become_sworn_sibling_with.assert_not_called()
        assert action._swear_success is False

    @pytest.mark.asyncio
    async def test_swear_finish_generates_story(self, dummy_avatar, target_avatar):
        """Test SwearBrotherhood.finish() generates result and story events."""
        action = SwearBrotherhood(dummy_avatar, dummy_avatar.world)
        action._swear_success = True
        
        with patch("src.classes.mutual_action.swear_brotherhood.StoryTeller.tell_story", new_callable=AsyncMock) as mock_story:
            mock_story.return_value = "A legendary brotherhood story."
            
            # cooldown_action wraps finish to accept **kwargs
            result = action.finish(target_avatar=target_avatar)
            events = await result
            
            assert len(events) == 2
            assert events[0].is_major is True
            assert events[1].is_story is True
            assert "A legendary brotherhood story." in events[1].content


class TestMutualActionBase:
    """Tests for MutualAction base class."""

    @pytest.fixture
    def target_avatar(self, base_world, dummy_avatar):
        """Create a generic target avatar."""
        from src.classes.core.avatar import Avatar, Gender
        from src.classes.age import Age
        from src.systems.cultivation import Realm
        from src.systems.time import Year, Month, create_month_stamp
        from src.classes.root import Root
        from src.classes.alignment import Alignment
        from src.utils.id_generator import get_avatar_id

        target = Avatar(
            world=base_world,
            name="GenericTarget",
            id=get_avatar_id(),
            birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
            age=Age(25, Realm.Qi_Refinement),
            gender=Gender.FEMALE,
            pos_x=0,
            pos_y=0,
            root=Root.EARTH,
            personas=[],
            alignment=Alignment.NEUTRAL
        )
        target.weapon = MagicMock()
        target.weapon.get_detailed_info.return_value = "Test Weapon"
        target.thinking = ""
        target.is_dead = False
        base_world.avatar_manager.avatars[target.name] = target
        return target

    def test_cannot_start_with_dead_target(self, dummy_avatar, target_avatar):
        """Test that mutual action cannot start with dead target."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        target_avatar.is_dead = True
        
        can_start, reason = action.can_start(target_avatar)
        
        assert can_start is False
        assert "死亡" in reason

    def test_get_target_avatar_by_name(self, dummy_avatar, target_avatar):
        """Test _get_target_avatar with string name."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        
        result = action._get_target_avatar("GenericTarget")
        
        assert result == target_avatar

    def test_get_target_avatar_by_object(self, dummy_avatar, target_avatar):
        """Test _get_target_avatar with Avatar object."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        
        result = action._get_target_avatar(target_avatar)
        
        assert result == target_avatar

    def test_get_target_avatar_not_found(self, dummy_avatar):
        """Test _get_target_avatar returns None for non-existent name."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        
        result = action._get_target_avatar("NonExistent")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_step_running_then_completed(self, dummy_avatar, target_avatar):
        """Test that step returns RUNNING first, then COMPLETED."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        action._start_month_stamp = 100
        
        mock_response = {
            target_avatar.name: {
                "thinking": "Test thinking",
                "feedback": "Reject"
            }
        }
        
        with patch("src.classes.observe.is_within_observation", return_value=True):
            with patch("src.classes.mutual_action.mutual_action.call_llm_with_task_name", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = mock_response
                
                # First call should be RUNNING
                res1 = action.step(target_avatar)
                assert res1.status == ActionStatus.RUNNING
                assert action._feedback_task is not None
                
                # Wait for task
                await action._feedback_task
                
                # Second call should be COMPLETED
                res2 = action.step(target_avatar)
                assert res2.status == ActionStatus.COMPLETED
                assert action._feedback_task is None
                assert action._feedback_cached is None

    def test_build_prompt_infos(self, dummy_avatar, target_avatar):
        """Test _build_prompt_infos returns correct structure."""
        action = Talk(dummy_avatar, dummy_avatar.world)
        
        infos = action._build_prompt_infos(target_avatar)
        
        assert "world_info" in infos
        assert "avatar_infos" in infos
        assert "avatar_name_1" in infos
        assert "avatar_name_2" in infos
        assert "action_name" in infos
        assert "feedback_actions" in infos
        assert infos["avatar_name_1"] == dummy_avatar.name
        assert infos["avatar_name_2"] == target_avatar.name
