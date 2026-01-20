"""
Tests for src/classes/action/cooldown.py

Tests the cooldown_action decorator behavior.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.classes.action.cooldown import cooldown_action
from src.classes.mutual_action.impart import Impart


class TestCooldownAction:
    """Tests for cooldown_action decorator."""

    @pytest.mark.asyncio
    async def test_cooldown_recorded_after_finish_executes(self):
        """
        Test that cooldown is recorded AFTER finish() executes, not before.
        
        This was a bug where the sync wrapper recorded cooldown before
        awaiting the async original_finish().
        """
        world = MagicMock()
        world.month_stamp = 100

        master = MagicMock()
        master.name = "Master"
        master._action_cd_last_months = {}

        action = Impart(master, world)
        action._impart_success = True
        action._impart_exp_gain = 2000

        target = MagicMock()
        target.name = "Disciple"
        target.id = "disciple_id"

        # Before calling finish, no cooldown recorded.
        assert "Impart" not in master._action_cd_last_months

        # Call finish and await it.
        events = await action.finish(target_avatar=target)

        # After await, cooldown should be recorded.
        assert "Impart" in master._action_cd_last_months
        assert master._action_cd_last_months["Impart"] == 100

    def test_cooldown_check_in_can_start(self):
        """Test that can_start checks cooldown correctly."""
        world = MagicMock()
        world.month_stamp = 100

        master = MagicMock()
        master.name = "Master"
        master._action_cd_last_months = {"Impart": 98}  # Used 2 months ago

        action = Impart(master, world)

        # Impart has 6 month cooldown, only 2 months passed.
        can_start, reason = action.can_start(target_avatar=MagicMock())
        
        assert can_start is False
        assert "冷却中" in reason
        assert "4" in reason  # 6 - 2 = 4 months remaining

    def test_cooldown_expired_allows_start(self):
        """Test that can_start allows action after cooldown expires."""
        world = MagicMock()
        world.month_stamp = 110

        master = MagicMock()
        master.name = "Master"
        master.get_relation = MagicMock(return_value=None)
        master._action_cd_last_months = {"Impart": 100}  # Used 10 months ago
        master.cultivation_progress = MagicMock()
        master.cultivation_progress.level = 50

        action = Impart(master, world)

        target = MagicMock()
        target.is_dead = False
        
        # Impart has 6 month cooldown, 10 months passed - should be allowed.
        # Note: will fail on other checks (relation), but not on cooldown.
        with patch("src.classes.observe.is_within_observation", return_value=True):
            can_start, reason = action.can_start(target_avatar=target)
        
        # Should not fail due to cooldown.
        assert "冷却" not in reason

    @pytest.mark.asyncio
    async def test_cooldown_not_recorded_on_finish_failure(self):
        """
        Test that cooldown is NOT recorded if finish() raises an exception.
        
        This is the key test that reveals the async/await bug:
        - Buggy code: records cooldown BEFORE awaiting, so cooldown is recorded even on failure
        - Fixed code: awaits first, so exception prevents cooldown from being recorded
        """

        class ActionError(Exception):
            pass

        # Create a simple action class with finish that raises.
        @cooldown_action
        class FailingAction:
            ACTION_CD_MONTHS = 6

            def __init__(self, avatar, world):
                self.avatar = avatar
                self.world = world

            def can_start(self, **params):
                return True, ""

            async def finish(self, **params):
                raise ActionError("Action failed!")

        world = MagicMock()
        world.month_stamp = 100

        avatar = MagicMock()
        avatar.name = "Test"
        avatar._action_cd_last_months = {}

        action = FailingAction(avatar, world)

        # Before calling finish, no cooldown recorded.
        assert "FailingAction" not in avatar._action_cd_last_months

        # Call finish - should raise.
        with pytest.raises(ActionError):
            await action.finish()

        # Cooldown should NOT be recorded because action failed.
        assert "FailingAction" not in avatar._action_cd_last_months
