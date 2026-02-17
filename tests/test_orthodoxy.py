import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from src.classes.core.orthodoxy import get_orthodoxy, orthodoxy_by_id, Orthodoxy
from src.classes.core.sect import Sect, sects_by_id
from src.classes.core.avatar.core import Avatar
from src.classes.action.respire import Respire
from src.systems.cultivation import Realm
EXTRA_RESPIRE_EXP_MULTIPLIER = "extra_respire_exp_multiplier"

class TestOrthodoxyData:
    """测试道统数据的加载和基本结构"""

    def test_orthodoxy_loaded(self):
        """确保道统数据已加载且包含预期的ID"""
        assert "dao" in orthodoxy_by_id
        assert "buddhism" in orthodoxy_by_id
        assert "confucianism" in orthodoxy_by_id

    def test_orthodoxy_attributes(self):
        """测试道统对象的属性"""
        dao = get_orthodoxy("dao")
        assert dao.id == "dao"
        assert dao.name # Should not be empty
        assert dao.desc # Should not be empty
        assert isinstance(dao.effects, dict)
        
    def test_orthodoxy_info(self):
        """测试 get_info 方法"""
        buddhism = get_orthodoxy("buddhism")
        info = buddhism.get_info(detailed=False)
        assert "id" in info
        assert "name" in info
        assert "desc" not in info
        
        detailed_info = buddhism.get_info(detailed=True)
        assert "desc" in detailed_info
        assert "effect_desc" in detailed_info

class TestSectIntegration:
    """测试宗门与道统的集成"""

    def test_sect_default_orthodoxy(self):
        """测试未指定道统的宗门默认为道门"""
        # 假设 ID 1 的宗门 (凌霄剑宗) 没有指定道统，应默认为 dao
        sect_1 = sects_by_id.get(1)
        if sect_1:
            assert sect_1.orthodoxy_id == "dao"

    def test_sect_explicit_orthodoxy(self):
        """测试指定道统的宗门"""
        # 须弥禅院 (ID 7) 指定为 buddhism
        sect_7 = sects_by_id.get(7)
        if sect_7:
            assert sect_7.orthodoxy_id == "buddhism"
            # 检查 buddhism 的 effect 是否存在 (legal_actions: ['Meditate'])
            assert "legal_actions" in sect_7.effects
            assert "Meditate" in sect_7.effects["legal_actions"]

        # 浩然书院 (ID 13) 指定为 confucianism
        sect_13 = sects_by_id.get(13)
        if sect_13:
            assert sect_13.orthodoxy_id == "confucianism"
            assert "legal_actions" in sect_13.effects
            assert "Educate" in sect_13.effects["legal_actions"]

    def test_sect_info_contains_orthodoxy(self):
        """测试宗门信息包含道统"""
        sect_7 = sects_by_id.get(7)
        if sect_7:
            info = sect_7.get_info()
            assert "佛" in info or "Buddhism" in info # Depends on language, but key should be translated
            
            detailed = sect_7.get_detailed_info()
            assert "佛" in detailed or "Buddhism" in detailed

class TestOrthodoxyEffects:
    """测试道统效果在游戏逻辑中的生效情况"""

    def test_respire_exp_multiplier(self, dummy_avatar):
        """测试修炼经验倍率加成"""
        # 1. 设置角色为道门宗门成员 (或者直接修改 effects)
        # 这里直接模拟 effects 字典，因为我们测的是 Cultivate action 对 effect 的响应
        
        # 基础经验
        dummy_avatar.cultivation_progress.is_in_bottleneck = MagicMock(return_value=False)
        dummy_avatar.cultivation_progress.add_exp = MagicMock()
        
        action = Respire(dummy_avatar, dummy_avatar.world)
        
        # Mock _get_matched_essence_density to return specific density for predictable base exp
        # BASE_EXP_PER_DENSITY = 100. Let's say density 1. Base exp = 100.
        action._get_matched_essence_density = MagicMock(return_value=1)
        
        with patch.object(Avatar, 'effects', new_callable=PropertyMock) as mock_effects:
            # Case 1: No multiplier
            mock_effects.return_value = {}
            action._execute()
            # Expect 100 exp
            dummy_avatar.cultivation_progress.add_exp.assert_called_with(100)
            
            # Case 2: 0.5 multiplier (Dao)
            mock_effects.return_value = {EXTRA_RESPIRE_EXP_MULTIPLIER: 0.5}
            action._execute()
            # Expect 100 * (1 + 0.5) = 150
            dummy_avatar.cultivation_progress.add_exp.assert_called_with(150)
            
            # Case 3: 1.0 multiplier + extra fixed exp
            mock_effects.return_value = {
                EXTRA_RESPIRE_EXP_MULTIPLIER: 1.0,
                "extra_respire_exp": 50
            }
            action._execute()
            # Base 100 + Extra 50 = 150.
            # Multiplier applies to total exp (base + extra)
            # exp = 150 * (1 + 1.0) = 300
            dummy_avatar.cultivation_progress.add_exp.assert_called_with(300)
