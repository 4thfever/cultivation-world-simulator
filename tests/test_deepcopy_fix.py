
import pytest
import copy
from src.classes.weapon import Weapon, WeaponType
from src.classes.equipment_grade import EquipmentGrade
from src.classes.sect import Sect, SectHeadQuarter
from src.classes.alignment import Alignment
from pathlib import Path

def test_weapon_deepcopy_does_not_copy_sect():
    # 1. 创建模拟的 Sect
    hq = SectHeadQuarter("HQ", "Desc", Path("img.png"))
    sect = Sect(
        id=1, name="TestSect", desc="Desc", member_act_style="Style",
        alignment=Alignment.Righteous, headquarter=hq, technique_names=[]
    )
    
    # 向 Sect 中添加一些可能导致问题的成员（虽然这里只是简单测试引用）
    # 在真实场景中，Sect.members 可能包含复杂的 Avatar 对象
    sect.members["dummy"] = "DummyAvatar"

    # 2. 创建 Weapon 并关联 Sect
    weapon = Weapon(
        id=101, name="TestWeapon", weapon_type=WeaponType.SWORD,
        grade=EquipmentGrade.COMMON, sect_id=1, desc="Desc", sect=sect
    )
    
    # 3. 深拷贝 Weapon
    weapon_copy = copy.deepcopy(weapon)
    
    # 4. 验证 Weapon 被复制了
    assert weapon_copy is not weapon
    assert weapon_copy.id == weapon.id
    
    # 5. 关键验证：Sect 应该是同一个对象（浅拷贝）
    assert weapon_copy.sect is sect
    assert weapon_copy.sect is weapon.sect
    
    # 验证 Sect 的成员没有被复制
    assert weapon_copy.sect.members is sect.members

def test_weapon_special_data_is_copied():
    # 验证 special_data 是否被正确深拷贝
    weapon = Weapon(
        id=101, name="TestWeapon", weapon_type=WeaponType.SWORD,
        grade=EquipmentGrade.COMMON, sect_id=None, desc="Desc"
    )
    weapon.special_data = {"souls": 10, "nested": {"a": 1}}
    
    weapon_copy = copy.deepcopy(weapon)
    
    assert weapon_copy.special_data == weapon.special_data
    assert weapon_copy.special_data is not weapon.special_data
    assert weapon_copy.special_data["nested"] is not weapon.special_data["nested"]

