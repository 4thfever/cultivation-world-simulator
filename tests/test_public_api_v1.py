from unittest.mock import AsyncMock, MagicMock, patch
import json

from fastapi.testclient import TestClient

from src.server import main
from src.classes.age import Age
from src.classes.alignment import Alignment
from src.classes.core.avatar import Avatar, Gender
from src.classes.root import Root
from src.systems.cultivation import Realm
from src.systems.time import Month, Year, create_month_stamp
from src.utils.id_generator import get_avatar_id
from src.classes.core.world import World
from src.classes.environment.map import Map
import pytest


def _reset_state():
    original = dict(main.game_instance)
    main.game_instance.clear()
    main.game_instance.update(
        {
            "world": None,
            "sim": None,
            "is_paused": True,
            "init_status": "idle",
            "init_phase": 0,
            "init_phase_name": "",
            "init_progress": 0,
            "init_start_time": None,
            "init_error": None,
            "run_config": None,
            "current_save_path": None,
            "llm_check_failed": False,
            "llm_error_message": "",
        }
    )
    return original


@pytest.fixture
def temp_save_dir(tmp_path):
    path = tmp_path / "saves"
    path.mkdir()
    return path


def _make_avatar(base_world) -> Avatar:
    avatar = Avatar(
        world=base_world,
        name="V1Target",
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


def _create_test_map():
    return Map(width=5, height=5)


def test_v1_runtime_status_uses_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/runtime/status")

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["data"]["status"] == "idle"
        assert data["data"]["is_paused"] is True
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_world_state_returns_structured_error_when_world_missing():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/world/state")

        assert response.status_code == 503
        detail = response.json()["detail"]
        assert detail["code"] == "WORLD_NOT_READY"
        assert detail["message"] == "World not initialized"
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_world_state_uses_ok_envelope_with_world():
    original = _reset_state()
    try:
        mock_world = MagicMock()
        mock_world.month_stamp.get_year.return_value = 100
        mock_world.month_stamp.get_month.return_value = MagicMock(value=2)
        mock_world.avatar_manager.avatars = {}
        mock_world.event_manager = None
        mock_world.current_phenomenon = None
        main.game_instance["world"] = mock_world

        client = TestClient(main.app)
        response = client.get("/api/v1/query/world/state")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["year"] == 100
        assert payload["data"]["month"] == 2
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_game_pause_and_resume_use_ok_envelope():
    original = _reset_state()
    try:
        main.game_instance["is_paused"] = False
        client = TestClient(main.app)

        pause_response = client.post("/api/v1/command/game/pause")
        assert pause_response.status_code == 200
        assert pause_response.json()["ok"] is True
        assert main.game_instance["is_paused"] is True

        resume_response = client.post("/api/v1/command/game/resume")
        assert resume_response.status_code == 200
        assert resume_response.json()["ok"] is True
        assert main.game_instance["is_paused"] is False
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_game_start_uses_lifecycle_service_and_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        with patch.object(main, "init_game_async", new_callable=AsyncMock):
            response = client.post(
                "/api/v1/command/game/start",
                json={
                    "init_npc_num": 10,
                    "sect_num": 2,
                    "npc_awakening_rate_per_month": 0.01,
                    "world_lore": "Some worldview and history",
                },
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert main.game_instance["init_status"] == "pending"
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_rankings_uses_ok_envelope():
    original = _reset_state()
    try:
        mock_ranking_manager = MagicMock()
        mock_ranking_manager.heaven_ranking = []
        mock_ranking_manager.earth_ranking = []
        mock_ranking_manager.human_ranking = []
        mock_ranking_manager.sect_ranking = []
        mock_ranking_manager.get_rankings_data.return_value = {
            "heaven": [],
            "earth": [],
            "human": [],
            "sect": [],
        }
        mock_world = MagicMock()
        mock_world.ranking_manager = mock_ranking_manager
        mock_world.avatar_manager.get_living_avatars.return_value = []
        main.game_instance["world"] = mock_world

        client = TestClient(main.app)
        response = client.get("/api/v1/query/rankings")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"] == {"heaven": [], "earth": [], "human": [], "sect": []}
        mock_ranking_manager.update_rankings_with_world.assert_called_once()
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_meta_game_data_uses_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/meta/game-data")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert "sects" in payload["data"]
        assert "personas" in payload["data"]
        assert "realms" in payload["data"]
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_avatar_adjust_options_uses_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/meta/avatar-adjust-options")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert "techniques" in payload["data"]
        assert "weapons" in payload["data"]
        assert "goldfingers" in payload["data"]
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_avatar_meta_uses_ok_envelope():
    original = _reset_state()
    try:
        main.AVATAR_ASSETS["males"] = [1, 2]
        main.AVATAR_ASSETS["females"] = [3, 4]
        client = TestClient(main.app)
        response = client.get("/api/v1/query/meta/avatars")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"] == {"males": [1, 2], "females": [3, 4]}
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_phenomena_list_uses_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/meta/phenomena")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert "phenomena" in payload["data"]
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_sect_territories_returns_empty_ok_envelope_when_world_missing():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/sects/territories")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"] == {"sects": []}
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_mortal_overview_uses_ok_envelope_when_world_missing():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        response = client.get("/api/v1/query/mortals/overview")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["summary"]["tracked_mortal_count"] == 0
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_dynasty_queries_use_ok_envelope_when_world_missing():
    original = _reset_state()
    try:
        client = TestClient(main.app)

        overview = client.get("/api/v1/query/dynasty/overview")
        assert overview.status_code == 200
        assert overview.json()["ok"] is True
        assert overview.json()["data"]["name"] == ""

        detail = client.get("/api/v1/query/dynasty/detail")
        assert detail.status_code == 200
        assert detail.json()["ok"] is True
        assert detail.json()["data"]["overview"]["name"] == ""
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_saves_query_uses_ok_envelope(temp_save_dir):
    original = _reset_state()
    try:
        game_map = _create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))
        sim = main.Simulator(world)
        save_path = temp_save_dir / "v1_list.json"
        main.save_game(world, sim, [], save_path, custom_name="v1列表")

        with patch.object(main.CONFIG.paths, "saves", temp_save_dir):
            client = TestClient(main.app)
            response = client.get("/api/v1/query/saves")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["saves"]
        assert payload["data"]["saves"][0]["filename"].endswith(".json")
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_save_command_uses_ok_envelope(temp_save_dir):
    original = _reset_state()
    try:
        game_map = _create_test_map()
        world = World(map=game_map, month_stamp=create_month_stamp(Year(100), Month.JANUARY))
        sim = main.Simulator(world)
        main.game_instance["world"] = world
        main.game_instance["sim"] = sim

        with patch.object(main.CONFIG.paths, "saves", temp_save_dir):
            client = TestClient(main.app)
            response = client.post("/api/v1/command/game/save", json={"custom_name": "v1存档"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert "v1存档" in payload["data"]["filename"]
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_delete_save_command_uses_ok_envelope(temp_save_dir):
    original = _reset_state()
    try:
        save_path = temp_save_dir / "delete_me.json"
        save_path.write_text(json.dumps({"meta": {}}), encoding="utf-8")
        db_path = main.get_events_db_path(save_path)
        db_path.write_text("", encoding="utf-8")

        with patch.object(main.CONFIG.paths, "saves", temp_save_dir):
            client = TestClient(main.app)
            response = client.post("/api/v1/command/game/delete-save", json={"filename": "delete_me.json"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert not save_path.exists()
        assert not db_path.exists()
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_load_command_uses_ok_envelope():
    original = _reset_state()
    try:
        client = TestClient(main.app)
        with patch("src.server.main.load_game_into_runtime", new_callable=AsyncMock) as mock_load:
            mock_load.return_value = {"status": "ok", "message": "Game loaded"}
            response = client.post("/api/v1/command/game/load", json={"filename": "demo.json"})

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        mock_load.assert_awaited_once()
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_create_avatar_returns_ok_envelope(base_world):
    original = _reset_state()
    try:
        main.game_instance["world"] = base_world
        client = TestClient(main.app)
        response = client.post(
            "/api/v1/command/avatar/create",
            json={"given_name": "云舟", "gender": "男", "age": 18, "level": 1},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert payload["data"]["avatar_id"]
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_update_avatar_adjustment_returns_ok_envelope(base_world):
    original = _reset_state()
    try:
        avatar = _make_avatar(base_world)
        main.game_instance["world"] = base_world
        weapon_id = next(iter(main.weapons_by_id.keys()))

        client = TestClient(main.app)
        response = client.post(
            "/api/v1/command/avatar/update-adjustment",
            json={
                "avatar_id": avatar.id,
                "category": "weapon",
                "target_id": weapon_id,
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert avatar.weapon is not None
        assert avatar.weapon.id == weapon_id
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_delete_avatar_returns_ok_envelope(base_world):
    original = _reset_state()
    try:
        avatar = _make_avatar(base_world)
        main.game_instance["world"] = base_world
        client = TestClient(main.app)
        response = client.post(
            "/api/v1/command/avatar/delete",
            json={"avatar_id": avatar.id},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert avatar.id not in base_world.avatar_manager.avatars
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_cleanup_events_returns_ok_envelope(tmp_path):
    original = _reset_state()
    try:
        world = World.create_with_db(
            map=_create_test_map(),
            month_stamp=create_month_stamp(Year(100), Month.JANUARY),
            events_db_path=tmp_path / "events.db",
        )
        world.event_manager.add_event(
            main.Event(
                month_stamp=create_month_stamp(Year(100), Month.JANUARY),
                content="minor",
            )
        )
        world.event_manager.add_event(
            main.Event(
                month_stamp=create_month_stamp(Year(100), Month.FEBRUARY),
                content="major",
                is_major=True,
            )
        )
        main.game_instance["world"] = world

        client = TestClient(main.app)
        response = client.delete("/api/v1/command/events/cleanup")

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["deleted"] == 1
        assert world.event_manager.count() == 1
    finally:
        world = main.game_instance.get("world")
        if world is not None and getattr(world, "event_manager", None) is not None:
            world.event_manager.close()
        main.game_instance.clear()
        main.game_instance.update(original)


def test_v1_generate_custom_content_uses_ok_envelope():
    client = TestClient(main.app)

    with patch(
        "src.server.main.generate_custom_content_draft",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = {
            "category": "weapon",
            "realm": "CORE_FORMATION",
            "name": "曜火巡天剑",
            "is_custom": True,
        }

        response = client.post(
            "/api/v1/command/avatar/generate-custom-content",
            json={
                "category": "weapon",
                "realm": "CORE_FORMATION",
                "user_prompt": "我想要一把偏爆发的金丹剑",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["draft"]["name"] == "曜火巡天剑"
    assert mock_generate.await_count == 1


def test_v1_create_custom_content_uses_ok_envelope():
    from src.classes.custom_content import CustomContentRegistry

    original = _reset_state()
    CustomContentRegistry.reset()
    try:
        client = TestClient(main.app)
        response = client.post(
            "/api/v1/command/avatar/create-custom-content",
            json={
                "category": "technique",
                "draft": {
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
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["ok"] is True
        assert payload["data"]["status"] == "ok"
        assert payload["data"]["item"]["is_custom"] is True
    finally:
        main.game_instance.clear()
        main.game_instance.update(original)
