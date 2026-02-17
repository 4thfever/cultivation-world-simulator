import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from src.classes.core.orthodoxy import get_orthodoxy
from src.classes.action.respire import Respire

class TestRogueCultivatorOrthodoxy:
    """测试散修（无宗门角色）的道统逻辑"""

    def test_rogue_has_sanxiu_orthodoxy(self, dummy_avatar):
        """测试散修默认拥有'sanxiu'道统"""
        # 确保角色没有宗门
        dummy_avatar.sect = None
        
        # 检查 orthodoxy 属性
        orthodoxy = dummy_avatar.orthodoxy
        assert orthodoxy is not None
        assert orthodoxy.id == "sanxiu"
        assert orthodoxy.name == "ORTHODOXY_SANXIU_NAME"

    def test_rogue_effects_include_sanxiu(self, dummy_avatar):
        """测试散修的 effects 中包含散修道统的效果"""
        dummy_avatar.sect = None
        
        # 强制重算 effects (虽然 effects 是 property 动态计算的，但为了保险起见)
        effects = dummy_avatar.effects
        
        # 检查 legal_actions
        assert "legal_actions" in effects
        legal_actions = effects["legal_actions"]
        assert "Respire" in legal_actions
        
    def test_rogue_can_cultivate(self, dummy_avatar):
        """测试散修可以进行修炼动作"""
        dummy_avatar.sect = None
        
        # 创建修炼动作
        action = Respire(dummy_avatar, dummy_avatar.world)
        
        # 模拟瓶颈检查通过
        dummy_avatar.cultivation_progress.can_cultivate = MagicMock(return_value=True)
        
        # 检查 can_start
        can_start, reason = action.can_start()
        assert can_start is True
        assert reason == ""

    def test_rogue_cannot_meditate_by_default(self, dummy_avatar):
        """测试散修默认不能进行冥想（假设冥想是佛门特有）"""
        dummy_avatar.sect = None
        
        # 假设我们有一个冥想动作，它检查 'Meditate' 权限
        # 这里我们手动检查 effects，模拟 Meditate 动作的逻辑
        effects = dummy_avatar.effects
        legal_actions = effects.get("legal_actions", [])
        
        # 散修应该只有 Cultivate，没有 Meditate
        assert "Respire" in legal_actions
        assert "Meditate" not in legal_actions

    def test_join_sect_overrides_sanxiu(self, dummy_avatar):
        """测试加入宗门后，散修道统被宗门道统覆盖"""
        # 模拟一个佛门宗门
        mock_sect = MagicMock()
        mock_sect.name = "Test Buddhism Sect"
        mock_sect.orthodoxy_id = "buddhism"
        mock_sect.effects = {"legal_actions": ["Meditate"]} # 宗门自带的效果
        
        # 加入宗门
        dummy_avatar.sect = mock_sect
        
        # 检查 orthodoxy 属性
        assert dummy_avatar.orthodoxy.id == "buddhism"
        
        # 检查 effects
        # 注意：这里我们依赖 Mixin 的逻辑。
        # 当 self.sect 存在时，Mixin 会读取 self.sect 的效果，而不会读取 sanxiu 的效果。
        # 模拟 Sect 对象在 Mixin 中的行为比较复杂，因为 Mixin 会读取 self.sect.effects
        # 我们这里通过 mock get_effect_breakdown 的一部分或者直接检查最终 effects
        
        # 为了让测试真实有效，我们需要确保 get_effect_breakdown 逻辑正确执行
        # 因为 dummy_avatar 是真实的 Avatar 对象（虽然部分组件是 mock 的）
        # 我们只需要确保 mock_sect 表现得像真的一样
        
        # 重新创建 dummy_avatar 以确保干净状态
        dummy_avatar.sect = mock_sect
        
        # 检查 effects
        effects = dummy_avatar.effects
        legal_actions = effects.get("legal_actions", [])
        
        # 应该是佛门效果
        assert "Meditate" in legal_actions
        # 散修的 Cultivate 应该消失了（除非佛门也允许 Cultivate，但配置里佛门是 Meditate）
        assert "Respire" not in legal_actions
