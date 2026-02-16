from __future__ import annotations

from unittest.mock import patch

from src.classes.action_runtime import ActionPlan
from src.classes.core.avatar import Avatar, Gender
from src.classes.age import Age
from src.classes.environment.region import CultivateRegion
from src.classes.mutual_action.occupy import Occupy
from src.classes.root import Root
from src.classes.alignment import Alignment
from src.systems.cultivation import Realm
from src.systems.time import Year, Month, create_month_stamp
from src.utils.id_generator import get_avatar_id


def _create_avatar(world, name: str, realm: Realm, personas: list | None = None) -> Avatar:
    avatar = Avatar(
        world=world,
        name=name,
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, realm),
        gender=Gender.MALE,
        pos_x=0,
        pos_y=0,
        root=Root.GOLD,
        personas=personas or [],
        alignment=Alignment.RIGHTEOUS,
    )
    avatar.cultivation_progress.realm = realm
    world.avatar_manager.register_avatar(avatar)
    return avatar


def _add_cultivate_region(world, name: str = "RiskTestCave") -> CultivateRegion:
    region = CultivateRegion(id=999001, name=name, desc="test", essence_density=1)
    world.map.regions[region.id] = region
    return region


class _PersonaStub:
    def __init__(self, key: str = "", name: str = ""):
        self.key = key
        self.name = name


def test_occupy_risk_owner_none_allowed(base_world):
    challenger = _create_avatar(base_world, "ChallengerA", Realm.Qi_Refinement)
    action = Occupy(challenger, base_world)

    allowed, multiplier, reason = action._risk_evaluator(challenger, None)

    assert allowed is True
    assert multiplier == 1.0
    assert reason == "owner_none"


def test_occupy_risk_realm_delta_soft_decay(base_world):
    challenger = _create_avatar(base_world, "ChallengerB", Realm.Qi_Refinement)
    owner = _create_avatar(base_world, "OwnerB", Realm.Foundation_Establishment)
    action = Occupy(challenger, base_world)

    allowed, multiplier, reason = action._risk_evaluator(challenger, owner)

    assert allowed is True
    assert multiplier == 0.5
    assert reason == "soft_decay"


def test_occupy_risk_realm_delta_hard_block_non_reckless(base_world):
    challenger = _create_avatar(base_world, "ChallengerC", Realm.Qi_Refinement)
    owner = _create_avatar(base_world, "OwnerC", Realm.Core_Formation)
    action = Occupy(challenger, base_world)

    allowed, multiplier, reason = action._risk_evaluator(challenger, owner)

    assert allowed is False
    assert multiplier == 0.0
    assert reason == "hard_block"


def test_occupy_risk_realm_delta_hard_block_reckless_override_allowed(base_world):
    personas = [_PersonaStub(key="RASH", name="鲁莽")]
    challenger = _create_avatar(base_world, "ChallengerD", Realm.Qi_Refinement, personas=personas)
    owner = _create_avatar(base_world, "OwnerD", Realm.Core_Formation)
    action = Occupy(challenger, base_world)

    with patch("src.classes.mutual_action.occupy.random.random", return_value=0.01):
        allowed, multiplier, reason = action._risk_evaluator(challenger, owner)

    assert allowed is True
    assert multiplier == 1.0
    assert reason == "override_allowed"


def test_occupy_risk_realm_delta_hard_block_reckless_override_failed(base_world):
    personas = [_PersonaStub(key="RASH", name="鲁莽")]
    challenger = _create_avatar(base_world, "ChallengerE", Realm.Qi_Refinement, personas=personas)
    owner = _create_avatar(base_world, "OwnerE", Realm.Core_Formation)
    action = Occupy(challenger, base_world)

    with patch("src.classes.mutual_action.occupy.random.random", return_value=0.99):
        allowed, multiplier, reason = action._risk_evaluator(challenger, owner)

    assert allowed is False
    assert multiplier == 0.0
    assert reason == "hard_block"


def test_occupy_can_start_soft_decay_probability_applies(base_world):
    challenger = _create_avatar(base_world, "ChallengerF", Realm.Qi_Refinement)
    owner = _create_avatar(base_world, "OwnerF", Realm.Foundation_Establishment)
    region = _add_cultivate_region(base_world, name="SoftDecayCave")
    region.host_avatar = owner

    action = Occupy(challenger, base_world)

    with patch("src.classes.mutual_action.occupy.random.random", return_value=0.9):
        can_start, reason = action.can_start(region_name=region.name)

    assert can_start is False
    assert "Risk too high" in reason


def test_commit_next_plan_fallback_when_occupy_filtered(base_world):
    challenger = _create_avatar(base_world, "ChallengerG", Realm.Qi_Refinement)
    owner = _create_avatar(base_world, "OwnerG", Realm.Core_Formation)
    region = _add_cultivate_region(base_world, name="FallbackCave")
    region.host_avatar = owner

    challenger.planned_actions = [
        ActionPlan("Occupy", {"region_name": region.name}),
        ActionPlan("Cultivate", {}),
    ]

    start_event = challenger.commit_next_plan()

    assert challenger.current_action is not None
    assert challenger.current_action.action.__class__.__name__ == "Cultivate"
    assert start_event is not None


