from fastapi.testclient import TestClient

from src.classes.core.dynasty import Dynasty, Emperor
from src.server import main


def test_get_dynasty_overview_empty_when_world_missing():
    original_instance = main.game_instance.copy()
    try:
        main.game_instance["world"] = None
        client = TestClient(main.app)
        resp = client.get("/api/dynasty/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == ""
        assert data["royal_surname"] == ""
        assert data["style_tag"] == ""
        assert data["official_preference_label"] == ""
        assert data["is_low_magic"] is True
    finally:
        main.game_instance.update(original_instance)


def test_get_dynasty_overview_returns_world_dynasty(base_world):
    original_instance = main.game_instance.copy()
    try:
        base_world.dynasty = Dynasty(
            id=1,
            name="晋",
            desc="门第森然，士族清谈，朝野重礼而尚名教。",
            royal_surname="司马",
            effect_desc="",
            effects={},
            style_tag="清谈名教",
            official_preference_type="orthodoxy",
            official_preference_value="confucianism",
            current_emperor=Emperor(
                surname="司马",
                given_name="承安",
                birth_month_stamp=int(base_world.month_stamp) - 34 * 12,
                max_age=80,
            ),
        )
        main.game_instance["world"] = base_world
        main.game_instance["sim"] = None

        client = TestClient(main.app)
        resp = client.get("/api/dynasty/overview")

        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "晋"
        assert data["title"] == "晋朝"
        assert data["royal_surname"] == "司马"
        assert data["royal_house_name"] == "司马氏"
        assert data["desc"] == "门第森然，士族清谈，朝野重礼而尚名教。"
        assert data["effect_desc"] == ""
        assert data["style_tag"] == "清谈名教"
        assert data["official_preference_label"] == "偏好儒家修士"
        assert data["is_low_magic"] is True
        assert data["current_emperor"]["name"] == "司马承安"
        assert data["current_emperor"]["age"] == 34
        assert data["current_emperor"]["max_age"] == 80
        assert data["current_emperor"]["is_mortal"] is True
    finally:
        main.game_instance.update(original_instance)
