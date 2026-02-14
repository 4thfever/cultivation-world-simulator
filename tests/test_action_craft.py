
import pytest
from unittest.mock import MagicMock, patch
from src.classes.action.refine import Refine
from src.classes.action.cast import Cast
from src.systems.cultivation import Realm
from src.classes.material import Material

# -----------------------------------------------------------------------------
# Refine (炼丹) Tests
# -----------------------------------------------------------------------------

def test_refine_can_start_params(dummy_avatar):
    """测试炼丹动作的参数解析逻辑"""
    action = Refine(dummy_avatar, dummy_avatar.world)
    
    # 1. 缺少参数
    can, reason = action.can_start("")
    assert not can
    assert "not specified" in reason or "未指定" in reason

    # 2. 无效参数
    can, reason = action.can_start("INVALID_REALM_XYZ")
    assert not can
    assert "Invalid realm" in reason or "无效" in reason

    # 3. 有效参数 - 枚举值字符串 (Prompt 引导的格式)
    # 先给 Avatar 发点材料，否则会报材料不足
    mat = Material(id=1, name="TestMat", realm=Realm.Qi_Refinement, desc="desc")
    dummy_avatar.materials[mat] = 100
    
    can, reason = action.can_start("QI_REFINEMENT")
    assert can, f"Should accept enum value string. Reason: {reason}"

    # 4. 有效参数 - 枚举名字符串
    can, reason = action.can_start("Qi_Refinement")
    assert can, f"Should accept enum name string. Reason: {reason}"

    # 5. 有效参数 - Realm 对象
    can, reason = action.can_start(Realm.Qi_Refinement)
    assert can, f"Should accept Realm object. Reason: {reason}"

    # 6. 中文参数 (预期失败，因为 resolution 未调用 Realm.from_str，且 Prompt 已引导使用英文)
    # 注意：如果未来 resolution.py 改了，这个测试需要更新
    can, reason = action.can_start("练气")
    assert not can
    assert "Invalid realm" in reason or "无效" in reason

def test_refine_materials_check(dummy_avatar):
    """测试炼丹的材料检查逻辑"""
    action = Refine(dummy_avatar, dummy_avatar.world)
    target_realm = Realm.Qi_Refinement
    cost = action.COST # 3

    # 清空材料
    dummy_avatar.materials = {}
    
    # 1. 材料不足
    can, reason = action.can_start(target_realm)
    assert not can
    assert "Insufficient materials" in reason or "材料不足" in reason

    # 2. 材料足够 (同境界)
    mat = Material(id=1, name="TestMat", realm=target_realm, desc="desc")
    dummy_avatar.materials[mat] = cost
    can, reason = action.can_start(target_realm)
    assert can

    # 3. 材料足够 (混合材料，总数够)
    dummy_avatar.materials = {}
    mat1 = Material(id=1, name="Mat1", realm=target_realm, desc="desc")
    mat2 = Material(id=2, name="Mat2", realm=target_realm, desc="desc")
    dummy_avatar.materials[mat1] = 1
    dummy_avatar.materials[mat2] = cost # Total > cost
    can, reason = action.can_start(target_realm)
    assert can

    # 4. 只有高阶材料 (不应计入低阶炼丹)
    dummy_avatar.materials = {}
    high_mat = Material(id=3, name="HighMat", realm=Realm.Foundation_Establishment, desc="desc")
    dummy_avatar.materials[high_mat] = 10
    can, reason = action.can_start(target_realm)
    assert not can

@pytest.mark.asyncio
async def test_refine_execution_flow(dummy_avatar):
    """测试炼丹的执行流程：扣材料 -> 成功/失败 -> 产出"""
    action = Refine(dummy_avatar, dummy_avatar.world)
    target_realm = Realm.Qi_Refinement
    cost = action.COST

    # 准备材料
    mat = Material(id=1, name="TestMat", realm=target_realm, desc="desc")
    dummy_avatar.materials[mat] = cost + 2 # 多给一点

    # Start
    event = action.start(target_realm)
    assert event is not None
    assert action.target_realm == target_realm
    
    # 验证材料已扣除
    assert dummy_avatar.materials[mat] == 2

    # Mock 成功率 (100% 成功)
    # Refine.SUCCESS_RATES[Realm.Qi_Refinement] = 0.6
    # 我们可以 mock random.random 来控制结果
    
    # Case A: Success
    with patch("random.random", return_value=0.0): # 0.0 < success_rate
        with patch("src.classes.action.refine.get_random_elixir_by_realm") as mock_get_elixir:
            with patch("src.classes.action.refine.handle_item_exchange", new_callable=MagicMock) as mock_exchange:
                # Setup mock return
                mock_elixir = MagicMock()
                mock_elixir.name = "Godly Pill"
                mock_get_elixir.return_value = mock_elixir
                
                # handle_item_exchange 是 async，Mock 需要是 awaitable
                # 但原始代码里是用 await handle_item_exchange(...)
                # 如果 handle_item_exchange 是 import 进来的函数，用 patch 即可
                # 注意：src.classes.single_choice.handle_item_exchange
                
                # 配置 mock_exchange 的返回值 (events, result_text)
                async def async_return(*args, **kwargs):
                    return ([], "Exchange Result")
                mock_exchange.side_effect = async_return
                
                events = await action.finish()
                
                assert len(events) == 2 # 1 success event + 1 exchange event
                assert "succeeded" in events[0].content or "成功" in events[0].content
                mock_get_elixir.assert_called_once_with(target_realm)
                mock_exchange.assert_called_once()

    # Case B: Fail
    action.target_realm = target_realm # Reset
    with patch("random.random", return_value=0.99): # 0.99 > success_rate
         events = await action.finish()
         assert len(events) == 1
         assert "failed" in events[0].content or "失败" in events[0].content


# -----------------------------------------------------------------------------
# Cast (铸造) Tests
# -----------------------------------------------------------------------------

def test_cast_can_start_params(dummy_avatar):
    """测试铸造动作的参数解析"""
    action = Cast(dummy_avatar, dummy_avatar.world)
    
    # 基本参数测试
    can, reason = action.can_start("QI_REFINEMENT")
    # Need materials
    mat = Material(id=1, name="TestMat", realm=Realm.Qi_Refinement, desc="desc")
    dummy_avatar.materials[mat] = 100
    
    can, reason = action.can_start("QI_REFINEMENT")
    assert can
    
    can, reason = action.can_start("INVALID")
    assert not can

def test_cast_materials_check(dummy_avatar):
    """测试铸造的材料消耗 (COST=5)"""
    action = Cast(dummy_avatar, dummy_avatar.world)
    target_realm = Realm.Qi_Refinement
    cost = action.COST # 5

    dummy_avatar.materials = {}
    
    # 1. 不足
    mat = Material(id=1, name="TestMat", realm=target_realm, desc="desc")
    dummy_avatar.materials[mat] = cost - 1
    can, reason = action.can_start(target_realm)
    assert not can
    
    # 2. 足够
    dummy_avatar.materials[mat] = cost
    can, reason = action.can_start(target_realm)
    assert can

@pytest.mark.asyncio
async def test_cast_execution_flow(dummy_avatar):
    """测试铸造流程"""
    action = Cast(dummy_avatar, dummy_avatar.world)
    target_realm = Realm.Qi_Refinement
    cost = action.COST

    mat = Material(id=1, name="TestMat", realm=target_realm, desc="desc")
    dummy_avatar.materials[mat] = cost
    
    action.start(target_realm)
    assert dummy_avatar.materials.get(mat, 0) == 0

    # Test Success (Weapon)
    with patch("random.random", side_effect=[0.0, 0.0]): # First: check success, Second: check is_weapon (<0.5)
        with patch("src.classes.action.cast.get_random_weapon_by_realm") as mock_get_weapon:
            with patch("src.classes.action.cast.handle_item_exchange") as mock_exchange:
                mock_weapon = MagicMock()
                mock_weapon.name = "Godly Sword"
                mock_get_weapon.return_value = mock_weapon
                
                async def async_return(*args, **kwargs):
                    return ([], "Exchange Result")
                mock_exchange.side_effect = async_return
                
                events = await action.finish()
                
                assert len(events) == 2
                assert "succeeded" in events[0].content or "成功" in events[0].content
                # 应该是兵器
                assert "weapon" in events[0].content or "兵器" in events[0].content or "sword" in events[0].content.lower()

