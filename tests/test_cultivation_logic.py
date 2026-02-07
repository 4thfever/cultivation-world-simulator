import pytest
from src.systems.cultivation import Realm, Stage, CultivationProgress

# ================= Realm Tests =================
def test_realm_comparison():
    assert Realm.Qi_Refinement < Realm.Foundation_Establishment
    assert Realm.Foundation_Establishment < Realm.Core_Formation
    assert Realm.Core_Formation < Realm.Nascent_Soul
    assert Realm.Nascent_Soul > Realm.Qi_Refinement

def test_realm_str_returns_translated_text_not_value():
    """Test that str(Realm) returns i18n translated text, not the raw enum value."""
    # str() should NOT return the uppercase enum value.
    assert str(Realm.Qi_Refinement) != "QI_REFINEMENT"
    assert str(Realm.Foundation_Establishment) != "FOUNDATION_ESTABLISHMENT"
    assert str(Realm.Core_Formation) != "CORE_FORMATION"
    assert str(Realm.Nascent_Soul) != "NASCENT_SOUL"

    # str() should return non-empty translated text.
    assert len(str(Realm.Qi_Refinement)) > 0
    assert len(str(Realm.Foundation_Establishment)) > 0
    assert len(str(Realm.Core_Formation)) > 0
    assert len(str(Realm.Nascent_Soul)) > 0

def test_realm_from_id():
    assert Realm.from_id(1) == Realm.Qi_Refinement
    assert Realm.from_id(4) == Realm.Nascent_Soul
    with pytest.raises(ValueError):
        Realm.from_id(0)

# ================= Stage Tests =================
def test_stage_comparison():
    assert Stage.Early_Stage < Stage.Middle_Stage
    assert Stage.Middle_Stage < Stage.Late_Stage

def test_stage_str_returns_translated_text_not_value():
    """Test that str(Stage) returns i18n translated text, not the raw enum value."""
    # str() should NOT return the uppercase enum value.
    assert str(Stage.Early_Stage) != "EARLY_STAGE"
    assert str(Stage.Middle_Stage) != "MIDDLE_STAGE"
    assert str(Stage.Late_Stage) != "LATE_STAGE"

    # str() should return non-empty translated text.
    assert len(str(Stage.Early_Stage)) > 0
    assert len(str(Stage.Middle_Stage)) > 0
    assert len(str(Stage.Late_Stage)) > 0

# ================= CultivationProgress Tests =================
def test_cp_initialization():
    cp = CultivationProgress(level=1, exp=0)
    assert cp.realm == Realm.Qi_Refinement
    assert cp.stage == Stage.Early_Stage

def test_cp_level_mapping():
    # Level 1-10 -> Early
    assert CultivationProgress(1).stage == Stage.Early_Stage
    assert CultivationProgress(10).stage == Stage.Early_Stage
    
    # Level 11-20 -> Middle
    assert CultivationProgress(11).stage == Stage.Middle_Stage
    assert CultivationProgress(20).stage == Stage.Middle_Stage
    
    # Level 21-30 -> Late
    assert CultivationProgress(21).stage == Stage.Late_Stage
    assert CultivationProgress(30).stage == Stage.Late_Stage
    
    # Level 31 -> Next Realm (Foundation)
    cp = CultivationProgress(31)
    assert cp.realm == Realm.Foundation_Establishment
    assert cp.stage == Stage.Early_Stage

def test_cp_bottleneck():
    # Level 30 is end of Qi Refinement (Late Stage)
    # According to code: bottleneck if level % 30 == 0
    cp = CultivationProgress(30)
    assert cp.is_in_bottleneck() is True
    assert cp.can_break_through() is True
    assert cp.can_cultivate() is False

    cp = CultivationProgress(29)
    assert cp.is_in_bottleneck() is False

def test_cp_add_exp_normal():
    cp = CultivationProgress(1, exp=0)
    required = cp.get_exp_required()
    
    # Add not enough to level up
    leveled = cp.add_exp(required - 1)
    assert leveled is False
    assert cp.level == 1
    assert cp.exp == required - 1

    # Add enough to level up
    leveled = cp.add_exp(2) # Total > required
    assert leveled is True
    assert cp.level == 2
    # Exp should be consumed
    assert cp.exp == 1 

def test_cp_add_exp_stops_at_bottleneck():
    # Start at level 29
    cp = CultivationProgress(29, exp=0)
    req_29 = cp.get_exp_required()
    
    # Add enough exp to theoretically go to 31
    # But should stop at 30 (bottleneck)
    # Need exp for 29->30.
    # At 30, it is bottleneck.
    
    cp.add_exp(req_29 + 100000) 
    
    assert cp.level == 30
    assert cp.is_in_bottleneck() is True
    # Exp should accumulate? Logic says:
    # if is_in_bottleneck(): break (inside while loop)
    # So extra exp stays in self.exp
    assert cp.exp >= 100000 

def test_cp_breakthrough():
    cp = CultivationProgress(30, exp=0)
    cp.break_through()
    assert cp.level == 31
    assert cp.realm == Realm.Foundation_Establishment
    assert cp.is_in_bottleneck() is False

def test_cp_serialization():
    cp = CultivationProgress(5, exp=123)
    data = cp.to_dict()
    assert data["level"] == 5
    assert data["exp"] == 123
    
    cp_new = CultivationProgress.from_dict(data)
    assert cp_new.level == 5
    assert cp_new.exp == 123
    assert cp_new.realm == Realm.Qi_Refinement



