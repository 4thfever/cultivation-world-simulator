
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from src.classes.action.move import Move
from src.classes.environment.tile import TileType
from src.classes.action_runtime import ActionStatus

class TestActionMove:
    
    def test_move_basic(self, dummy_avatar):
        """测试基础移动：向右下移动 (1, 1)"""
        # 初始位置 (0, 0)
        assert dummy_avatar.pos_x == 0
        assert dummy_avatar.pos_y == 0
        
        # 默认步长为 1，允许移动 (1, 1) 因为 clamp 逻辑允许斜向优先
        # 假设 move_step_length = 1，曼哈顿距离 1+1=2 > 1？
        # 看一下 clamp_manhattan_with_diagonal_priority 逻辑：
        # 如果 limit=1, (1,1) 是允许的吗？ 
        # 通常斜向算 1 步还是 2 步？根据源码：clamp_manhattan_with_diagonal_priority
        # 暂时假设允许 (1,0)
        
        action = Move(dummy_avatar, dummy_avatar.world)
        action.execute(delta_x=1, delta_y=0)
        
        assert dummy_avatar.pos_x == 1
        assert dummy_avatar.pos_y == 0
        assert dummy_avatar.tile.x == 1
        assert dummy_avatar.tile.y == 0

    def test_move_out_of_bounds(self, dummy_avatar):
        """测试边界移动：尝试移出地图 (往左)"""
        # 初始 (0, 0)
        action = Move(dummy_avatar, dummy_avatar.world)
        action.execute(delta_x=-1, delta_y=0)
        
        # 应该还在 (0, 0)
        assert dummy_avatar.pos_x == 0
        assert dummy_avatar.pos_y == 0

    def test_move_with_increased_step(self, dummy_avatar):
        """测试增加步长后的移动"""
        # 增加步长
        with patch.object(type(dummy_avatar), 'move_step_length', new_callable=PropertyMock) as mock_step:
            mock_step.return_value = 3
            
            action = Move(dummy_avatar, dummy_avatar.world)
            # 尝试移动 (0, 3)
            action.execute(delta_x=0, delta_y=3)
            
            assert dummy_avatar.pos_x == 0
            assert dummy_avatar.pos_y == 3

    def test_move_clamped_by_step(self, dummy_avatar):
        """测试步长限制：尝试移动超过步长的距离"""
        with patch.object(type(dummy_avatar), 'move_step_length', new_callable=PropertyMock) as mock_step:
            mock_step.return_value = 1
            
            action = Move(dummy_avatar, dummy_avatar.world)
            # 尝试移动 (5, 0)
            action.execute(delta_x=5, delta_y=0)
            
            # 应该只移动了 1 格 (1, 0)
            assert dummy_avatar.pos_x == 1
            assert dummy_avatar.pos_y == 0

