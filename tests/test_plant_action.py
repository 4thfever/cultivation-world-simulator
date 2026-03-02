import pytest
from src.classes.action.registry import ActionRegistry
from src.classes.action.plant import Plant
from src.systems.cultivation import Realm
from src.classes.environment.region import NormalRegion

def test_plant_action_registered():
    """验证 Plant 动作是否注册成功"""
    assert "Plant" in [cls.__name__ for cls in ActionRegistry.all()]

@pytest.mark.asyncio
async def test_plant_action_execution(dummy_avatar, base_world):
    """验证 Plant 动作的执行逻辑"""
    # 模拟在普通区域
    from unittest.mock import MagicMock
    dummy_avatar.tile.region = MagicMock(spec=NormalRegion)
    dummy_avatar.cultivation_progress.realm = Realm.Qi_Refinement
    dummy_avatar.magic_stone = 0
    
    # 无特质时的基础收益
    action = Plant(dummy_avatar, base_world)
    can_start, msg = action.can_start()
    assert can_start is True
    
    action._execute()
    assert dummy_avatar.magic_stone == 100
    assert action.gained_stones == 100

@pytest.mark.asyncio
async def test_plant_action_with_effect(dummy_avatar, base_world):
    """验证带有额外收益特质时的 Plant 动作"""
    from unittest.mock import MagicMock
    dummy_avatar.tile.region = MagicMock(spec=NormalRegion)
    dummy_avatar.cultivation_progress.realm = Realm.Foundation_Establishment
    dummy_avatar.magic_stone = 0
    
    # 模拟 FARMER 特质效果
    dummy_avatar.temporary_effects.append({
        "source": "test",
        "start_month": 0,
        "duration": 100,
        "effects": {"extra_plant_income": 50}
    })
    
    action = Plant(dummy_avatar, base_world)
    action._execute()
    # 筑基期 200 + 特质 50 = 250
    assert dummy_avatar.magic_stone == 250
