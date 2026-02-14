import pytest
from unittest.mock import patch, MagicMock
from src.classes.mutual_action.gift import Gift
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.core.avatar import Avatar, Gender
from src.classes.age import Age
from src.systems.cultivation import Realm
from src.classes.relation.relation import Relation
from src.utils.id_generator import get_avatar_id
from src.systems.time import create_month_stamp, Year, Month

# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def target_avatar(base_world):
    """创建第二个角色作为赠送目标"""
    av = Avatar(
        world=base_world,
        name="TargetNPC",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.FEMALE,
        pos_x=0,
        pos_y=0,
        personas=[],  # 显式清空特质，避免随机特质影响价格测试
    )
    # 强制重算一次效果，确保属性干净
    av.recalc_effects()
    return av

@pytest.fixture
def gift_action(dummy_avatar, base_world):
    """初始化 Gift 动作"""
    # 模拟 _call_llm_feedback，避免 step 中调用 asyncio.get_running_loop()
    with patch.object(Gift, '_call_llm_feedback', new_callable=MagicMock) as mock_llm:
         # 返回一个 mock task，确保 task.done() 初始为 False，
         # 但在这里我们主要是为了让 step 不报错
         mock_llm.return_value = {} 
         
         action = Gift(dummy_avatar, base_world)
         
         # 我们直接 Mock 掉 step 里的异步创建任务逻辑，
         # 因为我们主要测试的是：
         # 1. 参数是否正确解析 (step -> _resolve_gift)
         # 2. _can_start 逻辑
         # 3. 反馈结算逻辑 _settle_feedback / _apply_gift
         
         # 但 step 本身有逻辑：
         # 1. 解析参数
         # 2. 检查 target
         # 3. 创建 task (这里会报错)
         
         # 我们采用 patch asyncio.get_running_loop 的方式更简单
         yield action

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

class TestGiftAction:

    # --- 1. 赠送灵石 ---

    def test_gift_spirit_stone_success(self, gift_action, dummy_avatar, target_avatar):
        """测试赠送灵石成功"""
        dummy_avatar.magic_stone = 1000
        target_avatar.magic_stone = 0
        
        # Mock asyncio loop just to pass the step() check
        with patch("asyncio.get_running_loop", return_value=MagicMock()):
            gift_action.step(target_avatar, item_id="SPIRIT_STONE", amount=100)
            
        can_start, reason = gift_action._can_start(target_avatar)
        assert can_start is True, f"Should be able to start: {reason}"
        
        # 模拟接受
        gift_action._settle_feedback(target_avatar, "Accept")
        
        assert dummy_avatar.magic_stone == 900
        assert target_avatar.magic_stone == 100
        assert gift_action._gift_success is True

    def test_gift_spirit_stone_insufficient(self, gift_action, dummy_avatar, target_avatar):
        """测试灵石不足"""
        dummy_avatar.magic_stone = 50
        
        with patch("asyncio.get_running_loop", return_value=MagicMock()):
             gift_action.step(target_avatar, item_id="SPIRIT_STONE", amount=100)
             
        can_start, reason = gift_action._can_start(target_avatar)
        
        assert can_start is False
        assert "灵石不足" in reason

    # --- 2. 赠送素材 ---

    def test_gift_material_success(self, gift_action, dummy_avatar, target_avatar, mock_item_data):
        """测试赠送素材成功"""
        test_material = mock_item_data["obj_material"]
        dummy_avatar.add_material(test_material, quantity=5)
        
        with patch("asyncio.get_running_loop", return_value=MagicMock()):
            # 非灵石强制数量 1
            gift_action.step(target_avatar, item_id=str(test_material.id), amount=999) 
        
        can_start, reason = gift_action._can_start(target_avatar)
        assert can_start is True
        
        gift_action._settle_feedback(target_avatar, "Accept")
        
        assert dummy_avatar.get_material_quantity(test_material) == 4
        assert target_avatar.get_material_quantity(test_material) == 1
        assert gift_action._current_gift_context["amount"] == 1

    def test_gift_material_not_owned(self, gift_action, dummy_avatar, target_avatar, mock_item_data):
        """测试赠送未持有的素材"""
        test_material = mock_item_data["obj_material"]
        
        with patch("asyncio.get_running_loop", return_value=MagicMock()):
            gift_action.step(target_avatar, item_id=str(test_material.id), amount=1)
            
        can_start, reason = gift_action._can_start(target_avatar)
        assert can_start is False

    # --- 3. 赠送装备 ---

    def test_gift_weapon_success_and_auto_equip(self, gift_action, dummy_avatar, target_avatar, mock_item_data):
        """测试赠送装备成功，且目标自动装备"""
        test_weapon = mock_item_data["obj_weapon"]
        dummy_avatar.weapon = test_weapon
        assert target_avatar.weapon is None
        
        with patch("asyncio.get_running_loop", return_value=MagicMock()):
            gift_action.step(target_avatar, item_id=str(test_weapon.id), amount=1)
        
        can_start, reason = gift_action._can_start(target_avatar)
        assert can_start is True
        
        gift_action._settle_feedback(target_avatar, "Accept")
        
        assert dummy_avatar.weapon is None
        assert target_avatar.weapon == test_weapon

    def test_gift_weapon_fail_not_equipped(self, gift_action, dummy_avatar, target_avatar, mock_item_data):
        """测试赠送未装备的装备"""
        test_weapon = mock_item_data["obj_weapon"]
        
        with patch("asyncio.get_running_loop", return_value=MagicMock()):
            gift_action.step(target_avatar, item_id=str(test_weapon.id), amount=1)
            
        can_start, reason = gift_action._can_start(target_avatar)
        assert can_start is False

    def test_gift_weapon_target_trade_in(self, gift_action, dummy_avatar, target_avatar, mock_item_data):
        """测试目标已有装备时，收到新装备会自动折价卖出旧的"""
        from tests.conftest import create_test_weapon
        from src.systems.cultivation import Realm
        
        new_weapon = mock_item_data["obj_weapon"]
        dummy_avatar.weapon = new_weapon
        
        old_weapon = create_test_weapon("旧铁剑", Realm.Qi_Refinement, weapon_id=999)     
        # old_weapon.price = 100 # Prices 系统接管后，价格由 Realm 决定 (练气期=150)，不再手动指定
        target_avatar.weapon = old_weapon
        target_avatar.magic_stone = 0
        
        with patch("asyncio.get_running_loop", return_value=MagicMock()):
            gift_action.step(target_avatar, item_id=str(new_weapon.id), amount=1)
            
        gift_action._settle_feedback(target_avatar, "Accept")
        
        assert target_avatar.weapon == new_weapon
        # 练气期武器基准价 150，卖出倍率 1.0 (无特质加成) -> 150
        assert target_avatar.magic_stone == 150

    # --- 4. 上下文与描述 ---

    def test_prompt_info_description(self, gift_action, dummy_avatar, target_avatar, mock_item_data):
        """验证传给 LLM 的 prompt 中包含具体物品描述"""
        test_weapon = mock_item_data["obj_weapon"]
        dummy_avatar.weapon = test_weapon
        
        with patch("asyncio.get_running_loop", return_value=MagicMock()):
            gift_action.step(target_avatar, item_id=str(test_weapon.id))
            
        infos = gift_action._build_prompt_infos(target_avatar)
        
        assert f"[{test_weapon.name}]" in infos["action_info"]
        assert "赠送" in infos["action_info"]

    def test_prompt_info_description_stones(self, gift_action, dummy_avatar, target_avatar):
        dummy_avatar.magic_stone = 1000
        
        with patch("asyncio.get_running_loop", return_value=MagicMock()):
            gift_action.step(target_avatar, item_id="SPIRIT_STONE", amount=500)
            
        infos = gift_action._build_prompt_infos(target_avatar)
        assert "500 灵石" in infos["action_info"]
    
    def test_gift_invalid_id(self, gift_action, dummy_avatar, target_avatar):
        """测试传入无效 ID"""
        with patch("asyncio.get_running_loop", return_value=MagicMock()):
            gift_action.step(target_avatar, item_id="invalid_id_999", amount=1)
            
        can_start, reason = gift_action._can_start(target_avatar)
        assert can_start is False
        assert "Item not found" in reason or "未找到物品" in reason
