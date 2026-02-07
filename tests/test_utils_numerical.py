import pytest
from src.classes.hp import HP
from src.systems.cultivation import Realm
from src.utils.distance import chebyshev_distance, manhattan_distance, euclidean_distance
from src.utils.id_generator import get_avatar_id
from src.utils.df import get_int, get_bool, get_list_int, get_float

# ================= HP Tests =================
def test_hp_initialization():
    hp = HP(max=100, cur=100)
    assert hp.max == 100
    assert hp.cur == 100

def test_hp_reduce():
    hp = HP(max=100, cur=100)
    alive = hp.reduce(30)
    assert hp.cur == 70
    assert alive is True

def test_hp_reduce_to_death():
    hp = HP(max=100, cur=10)
    alive = hp.reduce(20)
    assert hp.cur == -10
    assert alive is False

def test_hp_recover():
    hp = HP(max=100, cur=50)
    hp.recover(30)
    assert hp.cur == 80

def test_hp_recover_overflow():
    hp = HP(max=100, cur=90)
    hp.recover(20)
    assert hp.cur == 100

def test_hp_add_max():
    hp = HP(max=100, cur=100)
    hp.add_max(50)
    assert hp.max == 150
    assert hp.cur == 100

def test_hp_comparison():
    hp1 = HP(max=100, cur=50)
    hp2 = HP(max=100, cur=60)
    hp3 = HP(max=200, cur=50)
    
    assert hp1 < hp2
    assert hp1 == hp3 # Compares cur
    assert hp2 > hp1

def test_hp_serialization():
    hp = HP(max=100, cur=50)
    data = hp.to_dict()
    assert data == {"max": 100, "cur": 50}
    
    hp_new = HP.from_dict(data)
    assert hp_new == hp
    assert hp_new.max == hp.max

# ================= Distance Tests =================
def test_chebyshev_distance():
    p1 = (0, 0)
    p2 = (3, 4)
    # max(|3-0|, |4-0|) = 4
    assert chebyshev_distance(p1, p2) == 4

def test_manhattan_distance():
    p1 = (0, 0)
    p2 = (3, 4)
    # |3-0| + |4-0| = 7
    assert manhattan_distance(p1, p2) == 7

def test_euclidean_distance():
    p1 = (0, 0)
    p2 = (3, 4)
    # sqrt(3^2 + 4^2) = 5.0
    assert euclidean_distance(p1, p2) == 5.0

# ================= ID Generator Tests =================
def test_id_generator():
    id1 = get_avatar_id()
    id2 = get_avatar_id()
    assert isinstance(id1, str)
    assert len(id1) == 8
    assert id1 != id2

# ================= DF Helper Tests =================
def test_df_get_int():
    row = {"a": "123", "b": "12.3", "c": "abc"}
    assert get_int(row, "a") == 123
    assert get_int(row, "b") == 12 # int(12.3) -> 12
    assert get_int(row, "c", default=99) == 99
    assert get_int(row, "missing", default=0) == 0

def test_df_get_float():
    row = {"a": "12.5", "b": "invalid"}
    assert get_float(row, "a") == 12.5
    assert get_float(row, "b", default=1.0) == 1.0

def test_df_get_bool():
    row = {"a": "true", "b": "1", "c": "yes", "d": "false", "e": "0"}
    assert get_bool(row, "a") is True
    assert get_bool(row, "b") is True
    assert get_bool(row, "c") is True
    assert get_bool(row, "d") is False
    assert get_bool(row, "e") is False
    assert get_bool(row, "missing") is False

def test_df_get_list_int():
    row = {"a": "1|2|3", "b": "1,2,3", "c": "1|invalid|3"}
    # Default separator is likely '|' from CONFIG, but let's test with explicit separator if needed or assume default.
    # The code says `separator = CONFIG.df.ids_separator` if None.
    # We'll assume default is '|' or we can mock CONFIG. 
    # Actually, looking at the code: `if separator is None: separator = CONFIG.df.ids_separator`.
    # Let's provide explicit separator to be safe and independent of CONFIG.
    assert get_list_int(row, "a", separator="|") == [1, 2, 3]
    assert get_list_int(row, "c", separator="|") == [1, 3]



