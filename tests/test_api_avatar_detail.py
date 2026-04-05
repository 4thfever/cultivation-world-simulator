from fastapi.testclient import TestClient

from src.classes.age import Age
from src.classes.alignment import Alignment
from src.classes.core.avatar import Avatar, Gender
from src.classes.goldfinger import goldfingers_by_id
from src.classes.root import Root
from src.server import main
from src.sim.avatar_init import make_avatars
from src.systems.cultivation import Realm
from src.systems.time import Month, Year, create_month_stamp
from src.utils.id_generator import get_avatar_id


def _find_goldfinger_by_key(key: str):
    for goldfinger in goldfingers_by_id.values():
        if goldfinger.key == key:
            return goldfinger
    raise AssertionError(f"Goldfinger not found: {key}")


def _make_avatar(base_world) -> Avatar:
    avatar = Avatar(
        world=base_world,
        name="DetailTarget",
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


def test_avatar_detail_api_exposes_goldfinger_fields(base_world):
    original_instance = main.game_instance.copy()
    try:
        avatar = _make_avatar(base_world)
        avatar.goldfinger = _find_goldfinger_by_key("TRANSMIGRATOR")
        avatar.goldfinger_state = {"story_focus": "modern_mindset"}
        avatar.recalc_effects()
        main.game_instance["world"] = base_world

        client = TestClient(main.app)
        response = client.get("/api/detail", params={"type": "avatar", "id": avatar.id})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == avatar.id
        assert data["goldfinger"] is not None
        assert data["goldfinger"]["name"] == "穿越者"
        assert data["goldfinger"]["mechanism_type"] == "story_driven"
        assert "现代思维" in data["goldfinger"]["story_prompt"]
        assert "另一个世界" in data["goldfinger"]["display_text"]
        assert data["goldfinger"]["state"] == {"story_focus": "modern_mindset"}
        assert "外挂 [穿越者]" in data["current_effects"]
        assert "pic_id" in data
    finally:
        main.game_instance.update(original_instance)


def test_avatar_detail_api_surfaces_randomly_initialized_goldfinger(base_world, monkeypatch):
    original_instance = main.game_instance.copy()
    try:
        target_goldfinger = _find_goldfinger_by_key("CHILD_OF_FORTUNE")
        monkeypatch.setattr("src.sim.avatar_init.INITIAL_GOLDFINGER_PROBABILITY", 1.0)
        monkeypatch.setattr(
            "src.sim.avatar_init.get_random_compatible_goldfinger",
            lambda avatar: target_goldfinger,
        )

        avatars = make_avatars(base_world, count=1, current_month_stamp=base_world.month_stamp)
        avatar = next(iter(avatars.values()))
        base_world.avatar_manager.register_avatar(avatar)
        main.game_instance["world"] = base_world

        client = TestClient(main.app)
        response = client.get("/api/detail", params={"type": "avatar", "id": avatar.id})

        assert response.status_code == 200
        data = response.json()
        assert data["goldfinger"] is not None
        assert data["goldfinger"]["key"] == "CHILD_OF_FORTUNE"
        assert data["goldfinger"]["name"] == "气运之子"
        assert "天地眷顾" in data["goldfinger"]["display_text"]
    finally:
        main.game_instance.update(original_instance)


def test_avatar_detail_api_returns_404_for_missing_avatar(base_world):
    original_instance = main.game_instance.copy()
    try:
        main.game_instance["world"] = base_world
        client = TestClient(main.app)

        response = client.get("/api/detail", params={"type": "avatar", "id": "missing-avatar"})

        assert response.status_code == 404
        assert response.json()["detail"] == "Target not found"
    finally:
        main.game_instance.update(original_instance)
