from src.classes.action.eat_mortals import EatMortals
from src.classes.age import Age
from src.classes.alignment import Alignment
from src.classes.core.avatar import Avatar, Gender
from src.classes.emotions import EmotionType
from src.classes.environment.region import CityRegion
from src.classes.environment.tile import Tile, TileType
from src.classes.race import get_race
from src.classes.root import Root
from src.sim.simulator_engine.context import SimulationStepContext
from src.sim.simulator_engine.finalizer import finalize_step
from src.systems.cultivation import CultivationProgress, Realm
from src.systems.time import Month, Year, create_month_stamp
from src.utils.id_generator import get_avatar_id


def _city_region() -> CityRegion:
    return CityRegion(id=1001, name="TestCity", desc="测试城", cors=[(0, 0), (1, 0), (0, 1), (1, 1)])


def _make_avatar(
    world,
    *,
    name: str,
    region: CityRegion,
    race_id: str = "human",
    alignment: Alignment = Alignment.RIGHTEOUS,
    level: int = 1,
    pos: tuple[int, int] = (0, 0),
) -> Avatar:
    avatar = Avatar(
        world=world,
        name=name,
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(1), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement, innate_max_lifespan=80),
        gender=Gender.MALE,
        cultivation_progress=CultivationProgress(level=level),
        pos_x=pos[0],
        pos_y=pos[1],
        root=Root.GOLD,
        personas=[],
        alignment=alignment,
        race=get_race(race_id),
    )
    avatar.personas = []
    avatar.technique = None
    avatar.weapon = None
    avatar.auxiliary = None
    avatar.recalc_effects()
    tile = Tile(pos[0], pos[1], TileType.CITY)
    tile.region = region
    avatar.tile = tile
    world.avatar_manager.register_avatar(avatar)
    return avatar


async def _finish_public_predation(world, predator: Avatar):
    event = (await EatMortals(predator, world).finish())[0]
    ctx = SimulationStepContext(
        world=world,
        living_avatars=world.avatar_manager.get_living_avatars(),
        events=[event],
        month_stamp=world.month_stamp,
    )
    finalize_step(ctx)
    return event


async def test_public_predation_is_remembered_by_same_city_witness(base_world):
    city = _city_region()
    predator = _make_avatar(
        base_world,
        name="WolfYao",
        region=city,
        race_id="wolf",
        alignment=Alignment.EVIL,
        level=1,
    )
    witness = _make_avatar(
        base_world,
        name="RighteousWitness",
        region=city,
        alignment=Alignment.RIGHTEOUS,
        level=30,
        pos=(1, 0),
    )

    event = await _finish_public_predation(base_world, predator)

    assert event.event_type == "public_predation"
    memories = base_world.event_manager.get_major_events_by_avatar(witness.id)
    assert len(memories) == 1
    assert "WolfYao" in memories[0].content
    assert "TestCity" in memories[0].content
    assert witness.emotion is EmotionType.ANGRY


async def test_righteous_strong_witness_queues_limited_response(base_world):
    city = _city_region()
    predator = _make_avatar(
        base_world,
        name="WolfYao",
        region=city,
        race_id="wolf",
        alignment=Alignment.EVIL,
        level=1,
    )
    witness = _make_avatar(
        base_world,
        name="Guardian",
        region=city,
        alignment=Alignment.RIGHTEOUS,
        level=30,
        pos=(1, 0),
    )

    await _finish_public_predation(base_world, predator)

    assert [(plan.action_name, plan.params) for plan in witness.planned_actions] == [
        ("MoveToAvatar", {"avatar_name": predator.name}),
        ("Attack", {"avatar_name": predator.name}),
    ]


async def test_public_predation_limits_response_to_strongest_available_defender(base_world):
    city = _city_region()
    predator = _make_avatar(
        base_world,
        name="WolfYao",
        region=city,
        race_id="wolf",
        alignment=Alignment.EVIL,
        level=1,
    )
    first_guardian = _make_avatar(
        base_world,
        name="FirstGuardian",
        region=city,
        alignment=Alignment.RIGHTEOUS,
        level=30,
        pos=(1, 0),
    )
    strongest_guardian = _make_avatar(
        base_world,
        name="StrongestGuardian",
        region=city,
        alignment=Alignment.RIGHTEOUS,
        level=50,
        pos=(0, 1),
    )
    second_guardian = _make_avatar(
        base_world,
        name="SecondGuardian",
        region=city,
        alignment=Alignment.RIGHTEOUS,
        level=40,
        pos=(1, 1),
    )

    await _finish_public_predation(base_world, predator)

    responders = [
        avatar
        for avatar in (first_guardian, strongest_guardian, second_guardian)
        if avatar.planned_actions
    ]
    assert responders == [strongest_guardian]
    assert [(plan.action_name, plan.params) for plan in strongest_guardian.planned_actions] == [
        ("MoveToAvatar", {"avatar_name": predator.name}),
        ("Attack", {"avatar_name": predator.name}),
    ]


async def test_public_predation_does_not_force_weak_or_busy_witness_response(base_world):
    city = _city_region()
    predator = _make_avatar(
        base_world,
        name="StrongWolfYao",
        region=city,
        race_id="wolf",
        alignment=Alignment.EVIL,
        level=60,
    )
    weak_witness = _make_avatar(
        base_world,
        name="WeakWitness",
        region=city,
        alignment=Alignment.RIGHTEOUS,
        level=1,
        pos=(1, 0),
    )
    busy_witness = _make_avatar(
        base_world,
        name="BusyWitness",
        region=city,
        alignment=Alignment.RIGHTEOUS,
        level=90,
        pos=(0, 1),
    )
    busy_witness.load_decide_result_chain([("Rest", {})], "already busy", "recover")

    await _finish_public_predation(base_world, predator)

    assert weak_witness.planned_actions == []
    assert [(plan.action_name, plan.params) for plan in busy_witness.planned_actions] == [("Rest", {})]
    assert weak_witness.emotion is EmotionType.FEARFUL
    assert busy_witness.emotion is EmotionType.ANGRY


async def test_public_predation_does_not_trigger_evil_or_distant_response(base_world):
    city = _city_region()
    distant_city = CityRegion(id=1002, name="FarCity", desc="远城", cors=[(8, 8)])
    predator = _make_avatar(
        base_world,
        name="WolfYao",
        region=city,
        race_id="wolf",
        alignment=Alignment.EVIL,
        level=1,
    )
    evil_neighbor = _make_avatar(
        base_world,
        name="EvilNeighbor",
        region=city,
        alignment=Alignment.EVIL,
        level=60,
        pos=(1, 0),
    )
    distant_avatar = _make_avatar(
        base_world,
        name="DistantCultivator",
        region=distant_city,
        alignment=Alignment.RIGHTEOUS,
        level=60,
        pos=(8, 8),
    )

    await _finish_public_predation(base_world, predator)

    evil_memories = base_world.event_manager.get_major_events_by_avatar(evil_neighbor.id)
    assert len(evil_memories) == 1
    assert "WolfYao" in evil_memories[0].content
    assert evil_neighbor.planned_actions == []
    assert distant_avatar.planned_actions == []
    assert base_world.event_manager.get_major_events_by_avatar(distant_avatar.id) == []
