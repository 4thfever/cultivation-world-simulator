import pytest
from unittest.mock import MagicMock, patch
import asyncio

from src.classes.action.play import Reading, TeaTasting, Traveling, ZitherPlaying
from src.classes.mutual_action.play import TeaParty, Chess
from src.classes.event import Event
from src.utils.config import CONFIG

class TestActionPlay:
    
    @pytest.fixture
    def play_avatar(self, dummy_avatar):
        """配置一个适合消遣的角色"""
        # 确保没有初始临时效果
        dummy_avatar.temporary_effects = []
        return dummy_avatar

    def test_single_play_action_instantiation(self, play_avatar):
        """测试单人消遣动作实例化"""
        world = play_avatar.world
        actions = [Reading, TeaTasting, Traveling, ZitherPlaying]
        
        for action_cls in actions:
            action = action_cls(play_avatar, world)
            assert action.duration_months == 1
            assert action.can_start()[0] is True

    @patch('src.classes.action.play.random.random')
    def test_single_play_benefit_trigger(self, mock_random, play_avatar):
        """测试单人消遣触发收益"""
        # mock random < 0.05 to trigger benefit
        # CONFIG.play.base_benefit_probability is 0.05
        mock_random.return_value = 0.01 
        
        action = Reading(play_avatar, play_avatar.world)
        
        # Execute finish (async)
        events = asyncio.run(action.finish())
        
        # Check event content
        assert len(events) == 1
        # 检查是否包含突破概率提升的描述 (英文或中文，取决于环境，这里假设 conftest 强制了中文)
        # conftest.py force_chinese_language fixture sets language to zh-CN
        # "breakthrough probability increased by 20.0%" -> zh-CN: "心境提升，突破概率增加 20.0%"
        # Let's check for "20.0%" to be safe across languages if translation fails, 
        # or check the translation key if possible. But here we get the formatted string.
        assert "20.0%" in events[0].content
        
        # Check effect applied
        # Need to check if temporary_effects has the entry
        assert len(play_avatar.temporary_effects) == 1
        effect = play_avatar.temporary_effects[0]
        assert effect["source"] == "play_benefit"
        assert effect["effects"]["extra_breakthrough_success_rate"] == 0.2
        assert effect["duration"] == 1

    @patch('src.classes.action.play.random.random')
    def test_single_play_no_benefit(self, mock_random, play_avatar):
        """测试单人消遣未触发收益"""
        # mock random >= 0.05
        mock_random.return_value = 0.1 
        
        action = Reading(play_avatar, play_avatar.world)
        
        events = asyncio.run(action.finish())
        
        assert len(events) == 1
        assert "20.0%" not in events[0].content
        assert len(play_avatar.temporary_effects) == 0

    @patch('src.classes.mutual_action.play.random.random')
    def test_mutual_play_benefit(self, mock_random, play_avatar):
        """测试双人消遣触发收益"""
        # Setup target avatar
        target_avatar = MagicMock()
        target_avatar.name = "Friend"
        # MagicMock doesn't have temporary_effects list by default, but add_breakthrough_rate is called on it
        
        # mock random < 0.05
        mock_random.return_value = 0.01
        
        action = TeaParty(play_avatar, play_avatar.world)
        
        # Simulate feedback "Accept"
        action._settle_feedback(target_avatar, "Accept")
        
        # Check initiator benefit
        assert len(play_avatar.temporary_effects) == 1
        assert play_avatar.temporary_effects[0]["effects"]["extra_breakthrough_success_rate"] == 0.2
        
        # Check target benefit
        target_avatar.add_breakthrough_rate.assert_called_with(0.2)
