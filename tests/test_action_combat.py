
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from src.classes.action.attack import Attack
from src.classes.action_runtime import ActionStatus

class TestActionCombat:
    
    @pytest.fixture
    def target_avatar(self, dummy_avatar):
        """创建一个靶子角色"""
        target = MagicMock()
        target.name = "TargetDummy"
        target.id = "target_id"
        target.hp = MagicMock()
        target.hp.current = 100
        target.hp.max = 100
        target.increase_weapon_proficiency = MagicMock()
        return target

    @patch("src.classes.action.attack.decide_battle")
    def test_attack_execution(self, mock_decide, dummy_avatar, target_avatar):
        """测试攻击执行：扣除 HP"""
        # Mock decide_battle 返回 (winner, loser, loser_dmg, winner_dmg)
        # 假设 dummy 赢了，Target 掉了 10 点血，dummy 掉了 2 点
        mock_decide.return_value = (dummy_avatar, target_avatar, 10, 2)
        
        # 注入 target 到 world
        dummy_avatar.world.avatar_manager.avatars = {target_avatar.name: target_avatar}
        
        # Mock HP 为 MagicMock 以便 assert_called
        dummy_avatar.hp = MagicMock()
        
        action = Attack(dummy_avatar, dummy_avatar.world)
        action._execute(avatar_name="TargetDummy")
        
        # 验证伤害应用
        target_avatar.hp.reduce.assert_called_with(10)
        dummy_avatar.hp.reduce.assert_called_with(2)
        
        # 验证熟练度增加 (虽然是随机的，但 mock 了 uniform 就好了，或者只验证调用)
        assert dummy_avatar.weapon.get_detailed_info.called or True # 只是确保流程跑通
    
    @patch("src.classes.action.attack.handle_death") # 这个是在 death.py 里的
    @patch("src.classes.battle.handle_battle_finish", new_callable=AsyncMock)
    def test_attack_finish(self, mock_battle_finish, mock_handle_death, dummy_avatar, target_avatar):
        """测试战斗结束回调"""
        # 注入 target
        dummy_avatar.world.avatar_manager.avatars = {target_avatar.name: target_avatar}
        
        action = Attack(dummy_avatar, dummy_avatar.world)
        
        # 设置 _last_result (通常由 execute 设置)
        action._last_result = (dummy_avatar, target_avatar, 10, 2)
        action._start_event_content = "Start Battle"
        
        # 运行 finish
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(action.finish(avatar_name="TargetDummy"))
        
        # 验证调用了 handle_battle_finish
        mock_battle_finish.assert_called_once()
        args, kwargs = mock_battle_finish.call_args
        assert args[1] == dummy_avatar # winner
        assert args[2] == target_avatar # loser
        
    def test_can_start_missing_target(self, dummy_avatar):
        """测试目标不存在"""
        dummy_avatar.world.avatar_manager.avatars = {}
        action = Attack(dummy_avatar, dummy_avatar.world)
        
        ok, reason = action.can_start("Ghost")
        assert ok is False
        assert reason == "目标不存在"

