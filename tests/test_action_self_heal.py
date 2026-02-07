import pytest
from unittest.mock import MagicMock, patch

from src.classes.action.self_heal import SelfHeal
from src.classes.environment.sect_region import SectRegion
from src.classes.environment.region import NormalRegion
from src.classes.environment.tile import Tile, TileType
from src.classes.core.sect import Sect
from src.classes.hp import HP

class TestSelfHealAction:
    
    @pytest.fixture
    def healing_avatar(self, dummy_avatar):
        """
        基于 dummy_avatar 扩展，
        设置 HP 为半血，以便可以进行疗伤。
        """
        dummy_avatar.hp = HP(100, 50) # 50/100 HP
        # effects 是 property，无法直接赋值，需要 mock 或者通过 effects mixin 覆盖
        # 这里 dummy_avatar 使用了 Real Avatar 类，所以 effects property 会去读 self._effects 或者计算
        return dummy_avatar

    @pytest.fixture
    def sect_region(self):
        return SectRegion(id=999, name="青云门总部", desc="测试宗门总部")
    
    @pytest.fixture
    def normal_region(self):
        return NormalRegion(id=101, name="荒野", desc="测试荒野")

    @pytest.fixture
    def mock_sect(self, sect_region):
        sect = MagicMock(spec=Sect)
        sect.name = "青云门"
        # 确保 headquarter.name 和 region.name 一致
        sect.headquarter = MagicMock()
        sect.headquarter.name = sect_region.name
        return sect

    def test_can_start_basic(self, healing_avatar):
        """测试基本启动条件：HP不满即可"""
        # Action 类通常需要 (avatar, world) 参数
        action = SelfHeal(healing_avatar, healing_avatar.world)
        can, reason = action.can_start()
        assert can is True
        assert reason == ""

    def test_cannot_start_full_hp(self, healing_avatar):
        """测试满血不能启动"""
        healing_avatar.hp.cur = 100
        action = SelfHeal(healing_avatar, healing_avatar.world)
        can, reason = action.can_start()
        assert can is False
        assert "HP已满" in reason

    def test_execute_in_wild_no_bonus(self, healing_avatar, normal_region):
        """测试在野外（非宗门）的基础回复（10%）"""
        # 设置位置
        healing_avatar.tile = Tile(0, 0, TileType.PLAIN)
        healing_avatar.tile.region = normal_region
        healing_avatar.sect = None # 散修
        
        # Mock effects 为空
        with patch.object(type(healing_avatar), 'effects', new_callable=lambda: {}) as mock_effects:
             action = SelfHeal(healing_avatar, healing_avatar.world)
             action._execute()

        # 预期：基础回复 10% * 100 = 10
        # 初始 50 -> 60
        assert healing_avatar.hp.cur == 60
        assert action._healed_total == 10

    def test_execute_in_wild_with_persona_bonus(self, healing_avatar, normal_region):
        """测试在野外带有 '苟' 特质加成（+50% efficiency）"""
        # 设置位置
        healing_avatar.tile = Tile(0, 0, TileType.PLAIN)
        healing_avatar.tile.region = normal_region
        
        # Mock effects 带有加成
        with patch.object(type(healing_avatar), 'effects', new_callable=lambda: {"extra_self_heal_efficiency": 0.5}):
            action = SelfHeal(healing_avatar, healing_avatar.world)
            action._execute()

        # 预期：基础 0.1 * (1 + 0.5) = 0.15
        # 回复 15 点 -> 50 + 15 = 65
        assert healing_avatar.hp.cur == 65
        assert action._healed_total == 15

    def test_execute_in_sect_hq_as_member(self, healing_avatar, sect_region, mock_sect):
        """测试宗门弟子在总部回复（直接回满）"""
        # 设置位置
        # TileType.SECT 可能不存在，检查源码通常用 TileType.CITY 或 PLAIN，关键是 region
        # 如果需要区分 TileType，请检查 src/classes/tile.py，这里先用 PLAIN 并确保 region 是 SectRegion
        # 不过为了保险，我们可以查看 TileType 定义。
        # 暂时用 PLAIN，关键是 region 类型。
        healing_avatar.tile = Tile(0, 0, TileType.PLAIN)
        healing_avatar.tile.region = sect_region
        
        # 设置宗门身份
        healing_avatar.sect = mock_sect

        with patch.object(type(healing_avatar), 'effects', new_callable=lambda: {}):
            action = SelfHeal(healing_avatar, healing_avatar.world)
            action._execute()

        # 预期：直接回满 -> 100
        assert healing_avatar.hp.cur == 100
        assert action._healed_total == 50

    def test_execute_in_sect_hq_not_member(self, healing_avatar, sect_region):
        """测试非本门弟子在某宗门总部（视为普通区域回复）"""
        # 设置位置
        healing_avatar.tile = Tile(0, 0, TileType.PLAIN)
        healing_avatar.tile.region = sect_region
        
        # 散修（或无匹配宗门）
        healing_avatar.sect = None 

        with patch.object(type(healing_avatar), 'effects', new_callable=lambda: {}):
            action = SelfHeal(healing_avatar, healing_avatar.world)
            action._execute()

        # 预期：基础回复 10% = 10
        assert healing_avatar.hp.cur == 60
        assert action._healed_total == 10

    def test_heal_overflow_clamp(self, healing_avatar, normal_region):
        """测试回复溢出处理（不超过 MaxHP）"""
        healing_avatar.hp.cur = 95 # 只差5点
        healing_avatar.tile = Tile(0, 0, TileType.PLAIN)
        healing_avatar.tile.region = normal_region

        with patch.object(type(healing_avatar), 'effects', new_callable=lambda: {}):
            action = SelfHeal(healing_avatar, healing_avatar.world)
            action._execute()

        # 预期：基础回复 10点，但只缺5点 -> 回复5点，当前100
        assert healing_avatar.hp.cur == 100
        assert action._healed_total == 5
