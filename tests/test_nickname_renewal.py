import pytest
from unittest.mock import MagicMock
from src.classes.nickname import can_get_nickname
from src.classes.nickname_data import Nickname
from src.utils.config import CONFIG

class TestNicknameRenewal:
    """测试绰号更新机制：十年一换"""

    def test_nickname_renewal_logic(self, dummy_avatar):
        """测试已拥有绰号的角色在不同时间点的绰号获取资格"""
        
        # 0. Mock 配置，降低获取门槛方便测试
        CONFIG.nickname.major_event_threshold = 1
        CONFIG.nickname.minor_event_threshold = 1
        
        # Mock 事件管理器，使其永远返回足够的事件数量
        dummy_avatar.world.event_manager.get_major_events_by_avatar = MagicMock(return_value=[1])
        dummy_avatar.world.event_manager.get_minor_events_by_avatar = MagicMock(return_value=[1])

        # 1. 初始状态：无绰号 -> 应该可以获取 (True)
        assert dummy_avatar.nickname is None
        assert can_get_nickname(dummy_avatar) is True

        # 2. 赋予初始绰号，生成时间为当前年份 (Year 1)
        current_year = dummy_avatar.world.month_stamp.get_year()  # Year 1
        dummy_avatar.nickname = Nickname(value="初出茅庐", reason="测试", created_year=current_year)
        
        # 3. 刚获得绰号当年 -> 不可获取 (False)
        assert can_get_nickname(dummy_avatar) is False

        # 4. 五年后 (Year 6) -> 差距 5 年 -> 不可获取 (False)
        dummy_avatar.world.month_stamp += 12 * 5
        assert dummy_avatar.world.month_stamp.get_year() - current_year == 5
        assert can_get_nickname(dummy_avatar) is False

        # 5. 九年后 (Year 10) -> 差距 9 年 -> 不可获取 (False)
        dummy_avatar.world.month_stamp += 12 * 4
        assert dummy_avatar.world.month_stamp.get_year() - current_year == 9
        assert can_get_nickname(dummy_avatar) is False

        # 6. 十年后 (Year 11) -> 差距 10 年 -> 可以获取 (True)
        dummy_avatar.world.month_stamp += 12 * 1
        assert dummy_avatar.world.month_stamp.get_year() - current_year == 10
        assert can_get_nickname(dummy_avatar) is True

        # 7. 十一年后 (Year 12) -> 差距 11 年 -> 可以获取 (True)
        dummy_avatar.world.month_stamp += 12 * 1
        assert dummy_avatar.world.month_stamp.get_year() - current_year == 11
        assert can_get_nickname(dummy_avatar) is True
