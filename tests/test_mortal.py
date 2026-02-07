import pytest
from src.classes.mortal import Mortal
from src.classes.gender import Gender
from src.systems.time import MonthStamp

def test_mortal_initialization():
    """测试Mortal对象的基本初始化"""
    mortal = Mortal(
        id="test_id",
        name="Test Mortal",
        gender=Gender.MALE,
        birth_month_stamp=MonthStamp(100),
        parents=["parent1", "parent2"],
        born_region_id=1
    )
    
    assert mortal.id == "test_id"
    assert mortal.name == "Test Mortal"
    assert mortal.gender == Gender.MALE
    assert mortal.birth_month_stamp == 100
    assert mortal.parents == ["parent1", "parent2"]
    assert mortal.born_region_id == 1

def test_mortal_defaults():
    """测试Mortal对象的默认值"""
    mortal = Mortal(
        id="test_id_default",
        name="Default Mortal",
        gender=Gender.FEMALE,
        birth_month_stamp=MonthStamp(200)
    )
    
    assert mortal.parents == []
    assert mortal.born_region_id == -1

def test_mortal_to_dict():
    """测试序列化为字典"""
    mortal = Mortal(
        id="dict_id",
        name="Dict Mortal",
        gender=Gender.FEMALE,
        birth_month_stamp=MonthStamp(300),
        parents=["p1"],
        born_region_id=5
    )
    
    data = mortal.to_dict()
    
    assert data["id"] == "dict_id"
    assert data["name"] == "Dict Mortal"
    assert data["gender"] == "female"
    assert data["birth_month_stamp"] == 300
    assert data["parents"] == ["p1"]
    assert data["born_region_id"] == 5

def test_mortal_from_dict():
    """测试从字典反序列化"""
    data = {
        "id": "from_dict_id",
        "name": "From Dict Mortal",
        "gender": "male",
        "birth_month_stamp": 400,
        "parents": ["pA", "pB"],
        "born_region_id": 10
    }
    
    mortal = Mortal.from_dict(data)
    
    assert mortal.id == "from_dict_id"
    assert mortal.name == "From Dict Mortal"
    assert mortal.gender == Gender.MALE
    assert mortal.birth_month_stamp == 400
    assert mortal.parents == ["pA", "pB"]
    assert mortal.born_region_id == 10

def test_mortal_from_dict_defaults():
    """测试从不完整的字典反序列化（使用默认值）"""
    data = {
        "id": "minimal_id",
        "name": "Minimal Mortal",
        "gender": "female",
        "birth_month_stamp": 500
    }
    
    mortal = Mortal.from_dict(data)
    
    assert mortal.id == "minimal_id"
    assert mortal.parents == []
    assert mortal.born_region_id == -1

def test_mortal_serialization_cycle():
    """测试完整的序列化-反序列化循环"""
    original = Mortal(
        id="cycle_id",
        name="Cycle Mortal",
        gender=Gender.MALE,
        birth_month_stamp=MonthStamp(600),
        parents=["root"],
        born_region_id=99
    )
    
    data = original.to_dict()
    restored = Mortal.from_dict(data)
    
    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.gender == original.gender
    assert restored.birth_month_stamp == original.birth_month_stamp
    assert restored.parents == original.parents
    assert restored.born_region_id == original.born_region_id
    assert restored == original
