from fastapi.testclient import TestClient

from src.classes.age import Age
from src.classes.alignment import Alignment
from src.classes.core.avatar import Avatar, Gender
from src.classes.root import Root
from src.server import main
from src.systems.cultivation import Realm
from src.systems.time import Month, Year, create_month_stamp
from src.utils.id_generator import get_avatar_id


def _make_avatar(base_world) -> Avatar:
    avatar = Avatar(
        world=base_world,
        name="AdjustTarget",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement, innate_max_lifespan=80),
        gender=Gender.MALE,
        pos_x=0,
        pos_y=0,
        root=Root.GOLD,
        personas=[],
        alignment=Alignment.RIGHTEOUS,
    )
    avatar.personas = []
    avatar.technique = None
    avatar.weapon = None
    avatar.auxiliary = None
    avatar.recalc_effects()
    base_world.avatar_manager.register_avatar(avatar)
    return avatar


def test_get_avatar_adjust_options_contains_rich_structured_entries():
    client = TestClient(main.app)
    response = client.get("/api/v1/query/meta/avatar-adjust-options")

    assert response.status_code == 200
    data = response.json()["data"]

    assert data["techniques"]
    assert data["weapons"]
    assert data["auxiliaries"]
    assert data["personas"]
    assert data["goldfingers"]

    first_technique = data["techniques"][0]
    assert "id" in first_technique
    assert "desc" in first_technique
    assert "effect_desc" in first_technique

    first_persona = data["personas"][0]
    assert "id" in first_persona
    assert "rarity" in first_persona

    first_goldfinger = data["goldfingers"][0]
    assert "id" in first_goldfinger
    assert "mechanism_type" in first_goldfinger


def test_update_weapon_adjustment_resets_proficiency(base_world):
    original_instance = main.game_instance.copy()
    try:
        avatar = _make_avatar(base_world)
        weapon = next(iter(main.weapons_by_id.values())).instantiate()
        avatar.change_weapon(weapon)
        avatar.weapon_proficiency = 88.0

        replacement_id = next(iter(main.weapons_by_id.keys()))
        main.game_instance["world"] = base_world

        client = TestClient(main.app)
        response = client.post(
            "/api/v1/command/avatar/update-adjustment",
            json={
                "avatar_id": avatar.id,
                "category": "weapon",
                "target_id": replacement_id,
            },
        )

        assert response.status_code == 200
        assert avatar.weapon is not None
        assert avatar.weapon.id == replacement_id
        assert avatar.weapon is not main.weapons_by_id[replacement_id]
        assert avatar.weapon_proficiency == 0.0
    finally:
        main.game_instance.update(original_instance)


def test_update_weapon_adjustment_allows_clearing(base_world):
    original_instance = main.game_instance.copy()
    try:
        avatar = _make_avatar(base_world)
        avatar.change_weapon(next(iter(main.weapons_by_id.values())).instantiate())
        avatar.weapon_proficiency = 66.0
        main.game_instance["world"] = base_world

        client = TestClient(main.app)
        response = client.post(
            "/api/v1/command/avatar/update-adjustment",
            json={
                "avatar_id": avatar.id,
                "category": "weapon",
                "target_id": None,
            },
        )

        assert response.status_code == 200
        assert avatar.weapon is None
        assert avatar.weapon_proficiency == 0.0
    finally:
        main.game_instance.update(original_instance)


def test_update_personas_replaces_whole_set(base_world):
    original_instance = main.game_instance.copy()
    try:
        avatar = _make_avatar(base_world)
        persona_ids = list(main.personas_by_id.keys())[:3]
        assert len(persona_ids) == 3
        main.game_instance["world"] = base_world

        client = TestClient(main.app)
        response = client.post(
            "/api/v1/command/avatar/update-adjustment",
            json={
                "avatar_id": avatar.id,
                "category": "personas",
                "persona_ids": persona_ids,
            },
        )

        assert response.status_code == 200
        assert [persona.id for persona in avatar.personas] == persona_ids
    finally:
        main.game_instance.update(original_instance)


def test_update_personas_rejects_duplicates(base_world):
    original_instance = main.game_instance.copy()
    try:
        avatar = _make_avatar(base_world)
        persona_id = next(iter(main.personas_by_id.keys()))
        main.game_instance["world"] = base_world

        client = TestClient(main.app)
        response = client.post(
            "/api/v1/command/avatar/update-adjustment",
            json={
                "avatar_id": avatar.id,
                "category": "personas",
                "persona_ids": [persona_id, persona_id],
            },
        )

        assert response.status_code == 400
        assert "duplicate" in response.json()["detail"]
    finally:
        main.game_instance.update(original_instance)


def test_update_technique_and_auxiliary_allow_clearing(base_world):
    original_instance = main.game_instance.copy()
    try:
        avatar = _make_avatar(base_world)
        technique_id = next(iter(main.techniques_by_id.keys()))
        auxiliary_id = next(iter(main.auxiliaries_by_id.keys()))
        main.game_instance["world"] = base_world

        client = TestClient(main.app)
        response_technique = client.post(
            "/api/v1/command/avatar/update-adjustment",
            json={
                "avatar_id": avatar.id,
                "category": "technique",
                "target_id": technique_id,
            },
        )
        response_aux = client.post(
            "/api/v1/command/avatar/update-adjustment",
            json={
                "avatar_id": avatar.id,
                "category": "auxiliary",
                "target_id": auxiliary_id,
            },
        )

        assert response_technique.status_code == 200
        assert response_aux.status_code == 200
        assert avatar.technique is main.techniques_by_id[technique_id]
        assert avatar.auxiliary is not None
        assert avatar.auxiliary.id == auxiliary_id
        assert avatar.auxiliary is not main.auxiliaries_by_id[auxiliary_id]

        clear_technique = client.post(
            "/api/v1/command/avatar/update-adjustment",
            json={
                "avatar_id": avatar.id,
                "category": "technique",
                "target_id": None,
            },
        )
        clear_aux = client.post(
            "/api/v1/command/avatar/update-adjustment",
            json={
                "avatar_id": avatar.id,
                "category": "auxiliary",
                "target_id": None,
            },
        )

        assert clear_technique.status_code == 200
        assert clear_aux.status_code == 200
        assert avatar.technique is None
        assert avatar.auxiliary is None
    finally:
        main.game_instance.update(original_instance)


def test_update_goldfinger_adjustment_allows_setting_and_clearing(base_world):
    original_instance = main.game_instance.copy()
    try:
        avatar = _make_avatar(base_world)
        goldfinger_id = next(iter(main.goldfingers_by_id.keys()))
        main.game_instance["world"] = base_world

        client = TestClient(main.app)
        set_response = client.post(
            "/api/v1/command/avatar/update-adjustment",
            json={
                "avatar_id": avatar.id,
                "category": "goldfinger",
                "target_id": goldfinger_id,
            },
        )

        assert set_response.status_code == 200
        assert avatar.goldfinger is not None
        assert avatar.goldfinger.id == goldfinger_id

        clear_response = client.post(
            "/api/v1/command/avatar/update-adjustment",
            json={
                "avatar_id": avatar.id,
                "category": "goldfinger",
                "target_id": None,
            },
        )

        assert clear_response.status_code == 200
        assert avatar.goldfinger is None
        assert avatar.goldfinger_state == {}
    finally:
        main.game_instance.update(original_instance)
