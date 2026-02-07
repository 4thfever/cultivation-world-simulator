import pytest
from src.classes.mortal import Mortal
from src.sim.managers.mortal_manager import MortalManager
from src.systems.time import MonthStamp
from src.classes.gender import Gender

@pytest.fixture
def manager():
    return MortalManager()

@pytest.fixture
def current_time():
    return MonthStamp(1000)

def test_register_and_get_mortal(manager):
    mortal = Mortal(
        id="m1",
        name="Test Mortal",
        gender=Gender.MALE,
        birth_month_stamp=MonthStamp(0),
        parents=[]
    )
    manager.register_mortal(mortal)
    
    assert manager.get_mortal("m1") == mortal
    assert manager.get_mortal("non_existent") is None

def test_remove_mortal(manager):
    mortal = Mortal(
        id="m1",
        name="Test Mortal",
        gender=Gender.MALE,
        birth_month_stamp=MonthStamp(0),
        parents=[]
    )
    manager.register_mortal(mortal)
    manager.remove_mortal("m1")
    
    assert manager.get_mortal("m1") is None

def test_get_awakening_candidates(manager, current_time):
    # current_time = 1000 months
    
    # 1. 刚出生 (0岁) -> 不符合 >= 16岁
    m1 = Mortal(id="m1", name="Baby", gender=Gender.MALE, 
                birth_month_stamp=MonthStamp(1000), parents=[])
    
    # 2. 恰好 16岁 (16 * 12 = 192 months old) -> birth = 1000 - 192 = 808
    m2 = Mortal(id="m2", name="Teen", gender=Gender.FEMALE, 
                birth_month_stamp=MonthStamp(808), parents=[])
    
    # 3. 20岁 -> 符合
    m3 = Mortal(id="m3", name="Adult", gender=Gender.MALE, 
                birth_month_stamp=MonthStamp(760), parents=[])
                
    manager.register_mortal(m1)
    manager.register_mortal(m2)
    manager.register_mortal(m3)
    
    candidates = manager.get_awakening_candidates(current_time, min_age=16)
    
    candidate_ids = {m.id for m in candidates}
    assert "m1" not in candidate_ids
    assert "m2" in candidate_ids
    assert "m3" in candidate_ids

def test_cleanup_dead_mortals(manager, current_time):
    # current_time = 1000
    # max_lifespan = 100 years = 1200 months
    
    # 1. 正常存活 (50岁)
    # 1000 - (50*12) = 400
    m1 = Mortal(id="m1", name="Living", gender=Gender.MALE,
                birth_month_stamp=MonthStamp(400), parents=[])
                
    # 2. 刚死 (100岁)
    # 1000 - (100*12) = -200
    m2 = Mortal(id="m2", name="Dead", gender=Gender.MALE,
                birth_month_stamp=MonthStamp(-200), parents=[])
                
    # 3. 早就死了 (150岁)
    m3 = Mortal(id="m3", name="LongDead", gender=Gender.MALE,
                birth_month_stamp=MonthStamp(-800), parents=[])
                
    manager.register_mortal(m1)
    manager.register_mortal(m2)
    manager.register_mortal(m3)
    
    removed_count = manager.cleanup_dead_mortals(current_time, max_lifespan=100)
    
    assert removed_count == 2
    assert manager.get_mortal("m1") is not None
    assert manager.get_mortal("m2") is None
    assert manager.get_mortal("m3") is None
