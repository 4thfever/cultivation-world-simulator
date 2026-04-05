from src.classes.custom_content import CustomContentRegistry
from src.sim.save.save_game import save_game
from src.sim.load.load_game import load_game
from src.sim.simulator import Simulator
from src.utils.id_generator import get_avatar_id


def test_save_and_load_custom_technique_round_trip(base_world, tmp_path):
    from src.classes.core.avatar import Avatar, Gender
    from src.classes.age import Age
    from src.classes.root import Root
    from src.classes.alignment import Alignment
    from src.systems.cultivation import Realm
    from src.systems.time import Month, Year, create_month_stamp
    from src.server.services.custom_content_service import create_custom_content_from_draft

    CustomContentRegistry.reset()
    created = create_custom_content_from_draft(
        "technique",
        {
            "category": "technique",
            "name": "九曜焚息诀",
            "desc": "火行吐纳功法",
            "effects": {
                "extra_respire_exp_multiplier": 0.2,
                "extra_breakthrough_success_rate": 0.1,
            },
            "attribute": "FIRE",
            "grade": "UPPER",
        },
    )

    avatar = Avatar(
        world=base_world,
        name="CustomHolder",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement, innate_max_lifespan=80),
        gender=Gender.MALE,
        root=Root.FIRE,
        personas=[],
        alignment=Alignment.RIGHTEOUS,
    )
    avatar.personas = []
    avatar.technique = CustomContentRegistry.custom_techniques_by_id[int(created["id"])]
    avatar.recalc_effects()
    base_world.avatar_manager.register_avatar(avatar)

    simulator = Simulator(base_world)
    save_path = tmp_path / "custom_content_save.json"

    success, _ = save_game(base_world, simulator, existed_sects=[], save_path=save_path)
    assert success is True

    CustomContentRegistry.reset()
    loaded_world, _loaded_sim, _sects = load_game(save_path)
    loaded_avatar = loaded_world.avatar_manager.get_avatar(avatar.id)

    assert loaded_avatar is not None
    assert loaded_avatar.technique is not None
    assert loaded_avatar.technique.name == "九曜焚息诀"
    assert loaded_avatar.technique.id == int(created["id"])
    assert int(created["id"]) in CustomContentRegistry.custom_techniques_by_id


def test_save_and_load_custom_goldfinger_round_trip(base_world, tmp_path):
    from src.classes.core.avatar import Avatar, Gender
    from src.classes.age import Age
    from src.classes.root import Root
    from src.classes.alignment import Alignment
    from src.systems.cultivation import Realm
    from src.systems.time import Month, Year, create_month_stamp
    from src.server.services.custom_goldfinger_service import create_custom_goldfinger_from_draft

    CustomContentRegistry.reset()
    created = create_custom_goldfinger_from_draft(
        {
            "category": "goldfinger",
            "name": "逆命骰子",
            "desc": "你的命数总会在关键时刻再掷一次。",
            "story_prompt": "请强调命运被重新掷骰的感觉。",
            "effects": {
                "extra_luck": 11,
                "extra_breakthrough_success_rate": 0.08,
            },
        },
    )

    avatar = Avatar(
        world=base_world,
        name="GoldfingerHolder",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement, innate_max_lifespan=80),
        gender=Gender.MALE,
        root=Root.FIRE,
        personas=[],
        alignment=Alignment.RIGHTEOUS,
    )
    avatar.personas = []
    avatar.goldfinger = CustomContentRegistry.custom_goldfingers_by_id[int(created["id"])]
    avatar.goldfinger_state = {"trigger_count": 2}
    avatar.recalc_effects()
    base_world.avatar_manager.register_avatar(avatar)

    simulator = Simulator(base_world)
    save_path = tmp_path / "custom_goldfinger_save.json"

    success, _ = save_game(base_world, simulator, existed_sects=[], save_path=save_path)
    assert success is True

    CustomContentRegistry.reset()
    loaded_world, _loaded_sim, _sects = load_game(save_path)
    loaded_avatar = loaded_world.avatar_manager.get_avatar(avatar.id)

    assert loaded_avatar is not None
    assert loaded_avatar.goldfinger is not None
    assert loaded_avatar.goldfinger.name == "逆命骰子"
    assert loaded_avatar.goldfinger.id == int(created["id"])
    assert loaded_avatar.goldfinger_state == {"trigger_count": 2}
    assert int(created["id"]) in CustomContentRegistry.custom_goldfingers_by_id
