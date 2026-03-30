from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.server import main


def test_generate_custom_content_api_uses_generation_service():
    client = TestClient(main.app)

    with patch(
        "src.server.main.generate_custom_content_draft",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = {
            "category": "weapon",
            "realm": "CORE_FORMATION",
            "name": "曜火巡天剑",
            "desc": "测试描述",
            "effects": {"extra_battle_strength_points": 3},
            "effect_desc": "额外战斗力 +3",
            "weapon_type": "SWORD",
            "is_custom": True,
        }

        response = client.post(
            "/api/action/generate_custom_content",
            json={
                "category": "weapon",
                "realm": "CORE_FORMATION",
                "user_prompt": "我想要一把偏爆发的金丹剑",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["draft"]["name"] == "曜火巡天剑"
    assert payload["draft"]["is_custom"] is True
    assert mock_generate.await_count == 1


def test_create_custom_content_api_registers_new_item():
    from src.classes.custom_content import CustomContentRegistry

    CustomContentRegistry.reset()
    client = TestClient(main.app)
    response = client.post(
        "/api/action/create_custom_content",
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
    assert payload["status"] == "ok"
    assert payload["item"]["is_custom"] is True
    assert payload["item"]["id"] >= 900001
