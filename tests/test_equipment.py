import pytest
from src.classes.items.weapon import Weapon, get_random_weapon_by_realm, weapons_by_id
from src.classes.items.auxiliary import Auxiliary, get_random_auxiliary_by_realm, auxiliaries_by_id
from src.systems.cultivation import Realm
from src.classes.weapon_type import WeaponType

class TestEquipment:
    def test_weapon_structure(self):
        """测试兵器数据结构和加载"""
        assert len(weapons_by_id) > 0
        
        # 检查任意一个兵器
        weapon = next(iter(weapons_by_id.values()))
        assert isinstance(weapon, Weapon)
        assert isinstance(weapon.realm, Realm)
        assert isinstance(weapon.weapon_type, WeaponType)
        assert weapon.name
        
        # 测试 info 方法
        info = weapon.get_info()
        assert info == weapon.name
        
        detailed = weapon.get_detailed_info()
        assert weapon.name in detailed
        assert str(weapon.realm) in detailed

    def test_weapon_random_generation(self):
        """测试按境界随机生成兵器"""
        # 测试练气期
        w_qi = get_random_weapon_by_realm(Realm.Qi_Refinement)
        if w_qi:
            assert w_qi.realm == Realm.Qi_Refinement
            
        # 测试筑基期
        w_found = get_random_weapon_by_realm(Realm.Foundation_Establishment)
        if w_found:
            assert w_found.realm == Realm.Foundation_Establishment
            
        # 测试金丹期
        w_core = get_random_weapon_by_realm(Realm.Core_Formation)
        if w_core:
            assert w_core.realm == Realm.Core_Formation

    def test_weapon_deepcopy(self):
        """测试兵器深拷贝独立性"""
        w1 = get_random_weapon_by_realm(Realm.Qi_Refinement)
        if not w1:
            pytest.skip("No Qi Refinement weapons available")
            
        w2 = get_random_weapon_by_realm(Realm.Qi_Refinement)
        # 即使随机到同一个原型，它们也应该是不同的对象
        # 注意：get_random_weapon_by_realm 内部已经做了 instantiate
        
        # 为了确保测试有效，我们手动获取同一个原型并 instantiate
        prototype = weapons_by_id[w1.id]
        w_copy1 = prototype.instantiate()
        w_copy2 = prototype.instantiate()
        
        assert w_copy1 is not w_copy2
        assert w_copy1.id == w_copy2.id
        
        # 修改一个不影响另一个
        w_copy1.special_data["test"] = 123
        assert "test" not in w_copy2.special_data

    def test_auxiliary_structure(self):
        """测试辅助装备数据结构和加载"""
        assert len(auxiliaries_by_id) > 0
        
        # 检查任意一个
        aux = next(iter(auxiliaries_by_id.values()))
        assert isinstance(aux, Auxiliary)
        assert isinstance(aux.realm, Realm)
        assert aux.name
        
        # 测试 info 方法
        info = aux.get_info()
        assert info == aux.name
        
        detailed = aux.get_detailed_info()
        assert aux.name in detailed
        assert str(aux.realm) in detailed

    def test_grade_renaming_compatibility(self):
        """测试 realm 改名后的兼容性（如果有必要）"""
        # 确保 weapon 和 auxiliary 确实有 realm 属性
        weapon = next(iter(weapons_by_id.values()))
        assert hasattr(weapon, 'realm')
        assert not hasattr(weapon, 'grade') # 确保改名彻底
        
        aux = next(iter(auxiliaries_by_id.values()))
        assert hasattr(aux, 'realm')
        assert not hasattr(aux, 'grade') # 确保改名彻底

