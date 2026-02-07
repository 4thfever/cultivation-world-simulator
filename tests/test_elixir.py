import pytest
import asyncio
from typing import Dict

from src.classes.items.elixir import Elixir, ElixirType, ConsumedElixir, _load_elixirs
from src.classes.core.avatar import Avatar
from src.systems.cultivation import Realm
from src.classes.effect import EffectsMixin
from src.systems.time import create_month_stamp, Year, Month

# ==========================================
# Fixtures
# ==========================================

@pytest.fixture
def test_elixirs() -> Dict[str, Elixir]:
    """
    手动构造一组测试用丹药，避免依赖外部CSV配置
    """
    # 1. 练气期破境丹（普通）
    breakthrough = Elixir(
        id=1001,
        name="测试破境丹",
        realm=Realm.Qi_Refinement,
        type=ElixirType.Breakthrough,
        desc="测试用",
        price=100,
        effects=[{"duration_month": 10, "extra_breakthrough_success_rate": 0.1}],
        effect_desc="突破率+10%"
    )

    # 2. 练气期延寿丹（无限时长）
    lifespan_qi = Elixir(
        id=1002,
        name="测试长生丹",
        realm=Realm.Qi_Refinement,
        type=ElixirType.Lifespan,
        desc="测试用",
        price=200,
        effects=[{"extra_max_lifespan": 10}], # 无 duration_month 视为永久
        effect_desc="寿元+10"
    )
    
    # 3. 筑基期延寿丹（境界更高）
    lifespan_found = Elixir(
        id=1003,
        name="测试筑基长生丹",
        realm=Realm.Foundation_Establishment,
        type=ElixirType.Lifespan,
        desc="测试用",
        price=500,
        effects=[{"extra_max_lifespan": 20}],
        effect_desc="寿元+20"
    )

    # 4. 燃血丹（混合时效：前3个月加攻，前10个月减防）
    # 注意：模拟csv中的 [{"duration_month": 3, "val": 1}, {"duration_month": 10, "val": -1}]
    burn_blood = Elixir(
        id=1004,
        name="测试燃血丹",
        realm=Realm.Qi_Refinement,
        type=ElixirType.BurnBlood,
        desc="测试用",
        price=50,
        effects=[
            {"duration_month": 3, "extra_battle_strength_points": 10},
            {"duration_month": 10, "extra_defense_points": -5}
        ],
        effect_desc="爆发"
    )

    return {
        "breakthrough": breakthrough,
        "lifespan_qi": lifespan_qi,
        "lifespan_found": lifespan_found,
        "burn_blood": burn_blood
    }

# ==========================================
# Tests
# ==========================================

class TestElixirBasic:
    """测试基本加载和数据结构"""
    
    def test_load_config_structure(self):
        """测试从实际CSV加载的机制是否正常工作（不校验具体数值，只校验结构）"""
        ids, names = _load_elixirs()
        assert len(ids) > 0, "应该能加载到丹药数据"
        first_elixir = list(ids.values())[0]
        assert isinstance(first_elixir, Elixir)
        assert isinstance(first_elixir.effects, (dict, list))

    def test_elixir_info(self, test_elixirs):
        """测试信息显示"""
        elixir = test_elixirs["breakthrough"]
        info = elixir.get_detailed_info()
        assert "测试破境丹" in info
        assert "练气" in info
        assert "破境" in info

class TestConsumption:
    """测试服用逻辑"""

    def test_consume_success(self, dummy_avatar, test_elixirs):
        """测试正常服用"""
        elixir = test_elixirs["breakthrough"]
        dummy_avatar.consume_elixir(elixir)
        
        assert len(dummy_avatar.elixirs) == 1
        record = dummy_avatar.elixirs[0]
        assert record.elixir.id == elixir.id
        assert record.consume_time == int(dummy_avatar.world.month_stamp)

    def test_consume_realm_restriction(self, dummy_avatar, test_elixirs):
        """测试境界限制：练气期不能吃筑基期丹药"""
        # 确认当前是练气期
        assert dummy_avatar.cultivation_progress.realm == Realm.Qi_Refinement
        
        elixir = test_elixirs["lifespan_found"] # 筑基期丹药
        success = dummy_avatar.consume_elixir(elixir)
        
        assert not success
        assert len(dummy_avatar.elixirs) == 0

    def test_consume_duplicate_lifespan(self, dummy_avatar, test_elixirs):
        """
        测试：同境界延寿丹再次服用，不会额外再次增加寿元。
        """
        elixir = test_elixirs["lifespan_qi"]
        
        # 1. 第一次服用
        base_lifespan = dummy_avatar.age.max_lifespan
        success1 = dummy_avatar.consume_elixir(elixir)
        assert success1
        
        # 检查属性变化
        new_lifespan = dummy_avatar.age.max_lifespan
        # 注意：这里假设 EffectsMixin 已经生效。如果有 extra_max_lifespan 效果，
        # recalc_effects 应该会把 10 加到 max_lifespan 上
        # 如果 EffectsMixin 的实现是将 effect 存在 self.effects_dict 中，
        # 而 Age.max_lifespan 是通过 property 计算 base + extra，那么这里应该能读到。
        # 如果是直接修改数值，则需要看具体实现。
        # 查看 avatar/core.py，Avatar 继承了 EffectsMixin。
        # 延寿效果通常对应 extra_max_lifespan，这应该在 Age 类或者 Avatar 属性计算中体现。
        # 假设 EffectsMixin 提供了 get_effect_value("extra_max_lifespan")
        
        # 我们通过 checking effect 值来验证
        assert dummy_avatar.effects.get("extra_max_lifespan") == 10
        
        # 2. 立即再次服用（应该失败）
        success2 = dummy_avatar.consume_elixir(elixir)
        assert not success2
        assert len(dummy_avatar.elixirs) == 1
        assert dummy_avatar.effects.get("extra_max_lifespan") == 10

        # 3. 推进时间很久（延寿丹是永久的，依然不能服用）
        dummy_avatar.world.month_stamp += 1000
        success3 = dummy_avatar.consume_elixir(elixir)
        assert not success3
        assert len(dummy_avatar.elixirs) == 1
        
    def test_consume_duplicate_expired(self, dummy_avatar, test_elixirs):
        """测试：过期后的丹药可以再次服用"""
        elixir = test_elixirs["breakthrough"] # 持续10个月
        
        # 1. 服用
        dummy_avatar.consume_elixir(elixir)
        assert len(dummy_avatar.elixirs) == 1
        
        # 2. 推进时间到过期 (当前 + 11)
        # consume_time 是服用时的 month_stamp
        # expire_time = consume_time + 10
        # current >= expire_time 时 is_completely_expired 为 True
        
        # 先推进9个月（还剩1个月）
        dummy_avatar.world.month_stamp += 9
        # 清理逻辑通常是被动触发的，这里我们手动触发或依赖服用时的检查
        # consume_elixir 内部会检查 is_completely_expired
        success_fail = dummy_avatar.consume_elixir(elixir)
        assert not success_fail # 还没过期，不能吃
        
        # 再推进2个月（共+11），过期了
        dummy_avatar.world.month_stamp += 2
        
        # 3. 再次服用（应该成功）
        # 注意：consume_elixir 内部逻辑是 "若已服用过同种且【未失效】的丹药，则无效"
        # 即使旧的记录还在 list 里（还没被清理），只要 is_completely_expired 返回 True，就可以再吃
        success_ok = dummy_avatar.consume_elixir(elixir)
        assert success_ok
        
        # 此时列表里可能有2个记录（旧的没清理的话），或者旧的被清理了（取决于实现，这里不强制要求清理，只要求能吃）
        # 查看代码：consume_elixir 没有清理逻辑，只是 append。清理逻辑在 process_elixir_expiration
        assert len(dummy_avatar.elixirs) == 2
        
        # 验证一个是过期的，一个是新的
        expired_one = dummy_avatar.elixirs[0]
        new_one = dummy_avatar.elixirs[1]
        assert expired_one.is_completely_expired(int(dummy_avatar.world.month_stamp))
        assert not new_one.is_completely_expired(int(dummy_avatar.world.month_stamp))

class TestExpirationAndEffects:
    """测试时效和效果计算"""

    def test_mixed_duration_effects(self, dummy_avatar, test_elixirs):
        """测试燃血丹的多段效果"""
        # 先计算基础值（排除丹药影响）
        dummy_avatar.recalc_effects()
        base_atk = dummy_avatar.effects.get("extra_battle_strength_points", 0)
        base_def = dummy_avatar.effects.get("extra_defense_points", 0)

        elixir = test_elixirs["burn_blood"]
        # effects: duration 3 (atk+10), duration 10 (def-5)
        
        dummy_avatar.consume_elixir(elixir)
        start_time = int(dummy_avatar.world.month_stamp)
        
        # 1. 刚服用 (Month 0)
        # 效果全在
        active = dummy_avatar.elixirs[0].get_active_effects(start_time)
        assert len(active) == 2
        
        dummy_avatar.recalc_effects()
        # 断言应当是 基础值 + 丹药增量
        assert dummy_avatar.effects.get("extra_battle_strength_points") == base_atk + 10
        assert dummy_avatar.effects.get("extra_defense_points") == base_def - 5

        # 2. 第 2 个月 (Month 0 + 2 < 3)
        current = start_time + 2
        active = dummy_avatar.elixirs[0].get_active_effects(current)
        assert len(active) == 2

        # 3. 第 5 个月 (Month 0 + 5)
        # 攻击buff(3个月)消失，防御debuff(10个月)还在
        current = start_time + 5
        dummy_avatar.world.month_stamp = create_month_stamp(Year(2000), Month.JANUARY) + 5 # Reset timestamp just to be safe
        # update world time manually
        dummy_avatar.world.month_stamp = start_time + 5
        
        # 主动触发清理或重算
        dummy_avatar.process_elixir_expiration(current) # 还没完全过期，不会移除Elixir对象
        dummy_avatar.recalc_effects() # 但 active effects 变了，重算属性
        
        # 验证 active effects
        active = dummy_avatar.elixirs[0].get_active_effects(current)
        assert len(active) == 1
        assert "extra_battle_strength_points" not in active[0]
        assert active[0]["extra_defense_points"] == -5
        
        # 验证属性面板
        # 注意：Avatar.recalc_effects() 会调用 self.get_all_effects()
        # get_all_effects 会遍历 elixirs 调用 get_active_effects
        assert dummy_avatar.effects.get("extra_battle_strength_points", 0) == base_atk
        assert dummy_avatar.effects.get("extra_defense_points") == base_def - 5

        # 4. 第 11 个月 (Month 0 + 11)
        # 全部过期
        current = start_time + 11
        dummy_avatar.world.month_stamp = current
        
        # 此时 is_completely_expired 应该是 True
        assert dummy_avatar.elixirs[0].is_completely_expired(current)
        
        # 触发清理
        dummy_avatar.process_elixir_expiration(current)
        assert len(dummy_avatar.elixirs) == 0
        
        # 属性恢复
        dummy_avatar.recalc_effects()
        assert dummy_avatar.effects.get("extra_defense_points", 0) == base_def

    def test_infinite_duration(self, dummy_avatar, test_elixirs):
        """测试无限时长（延寿丹）"""
        elixir = test_elixirs["lifespan_qi"]
        dummy_avatar.consume_elixir(elixir)
        
        # 推进 100 年
        dummy_avatar.world.month_stamp += 1200 
        current = int(dummy_avatar.world.month_stamp)
        
        assert not dummy_avatar.elixirs[0].is_completely_expired(current)
        dummy_avatar.process_elixir_expiration(current)
        assert len(dummy_avatar.elixirs) == 1
        
        # 效果依然在
        dummy_avatar.recalc_effects()
        assert dummy_avatar.effects.get("extra_max_lifespan") == 10

class TestSimulatorIntegration:
    """测试模拟器集成"""
    
    @pytest.mark.asyncio
    async def test_passive_update_loop(self, base_world, dummy_avatar, test_elixirs, mock_llm_managers):
        """测试在 Simulator step 中自动清理过期丹药"""
        from src.sim.simulator import Simulator
        
        # 准备环境
        sim = Simulator(base_world)
        # 确保 dummy_avatar 在世界管理器中（虽然 base_world 可能没有自动加进去）
        base_world.avatar_manager.avatars[dummy_avatar.id] = dummy_avatar
        
        # 构造一个超短效丹药 (持续1个月)
        short_elixir = Elixir(
            id=9999,
            name="瞬时丹",
            realm=Realm.Qi_Refinement,
            type=ElixirType.Breakthrough,
            desc="测试用",
            price=1,
            effects=[{"duration_month": 1, "test_val": 1}],
            effect_desc="瞬时"
        )
        dummy_avatar.consume_elixir(short_elixir)
        
        # 只需运行 2 个 step (month 0->1 还在, month 1->2 过期清理)
        # month 0: consume. expires at 0+1=1.
        # step 1: check expiration (time=0). not expired. time becomes 1.
        # step 2: check expiration (time=1). expired! cleaned. time becomes 2.
        for _ in range(2):
            await sim.step()
            
        # 检查是否自动清理
        assert len(dummy_avatar.elixirs) == 0

