from unittest.mock import AsyncMock, patch

import pytest
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
            "/api/v1/command/avatar/generate-custom-content",
            json={
                "category": "weapon",
                "realm": "CORE_FORMATION",
                "user_prompt": "我想要一把偏爆发的金丹剑",
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "ok"
    assert payload["draft"]["name"] == "曜火巡天剑"
    assert payload["draft"]["is_custom"] is True
    assert mock_generate.await_count == 1


def test_generate_custom_goldfinger_api_uses_generation_service():
    client = TestClient(main.app)

    with patch(
        "src.server.main.generate_custom_goldfinger_draft",
        new_callable=AsyncMock,
    ) as mock_generate:
        mock_generate.return_value = {
            "category": "goldfinger",
            "name": "天命签到簿",
            "desc": "一本只会在你心底翻页的天命簿册。",
            "story_prompt": "请围绕签到感与命数回报展开。",
            "effects": {"extra_luck": 12},
            "effect_desc": "气运 +12",
            "mechanism_type": "effect_only",
            "is_custom": True,
        }

        response = client.post(
            "/api/v1/command/avatar/generate-custom-content",
            json={
                "category": "goldfinger",
                "user_prompt": "想要一个偏签到流、数值稍强的外挂",
            },
        )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "ok"
    assert payload["draft"]["category"] == "goldfinger"
    assert payload["draft"]["is_custom"] is True
    assert mock_generate.await_count == 1


def test_create_custom_content_api_registers_new_item():
    from src.classes.custom_content import CustomContentRegistry

    CustomContentRegistry.reset()
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
    payload = response.json()["data"]
    assert payload["status"] == "ok"
    assert payload["item"]["is_custom"] is True
    assert payload["item"]["id"] >= 900001


def test_create_custom_goldfinger_api_registers_new_item():
    from src.classes.custom_content import CustomContentRegistry

    CustomContentRegistry.reset()
    client = TestClient(main.app)
    response = client.post(
        "/api/v1/command/avatar/create-custom-content",
        json={
            "category": "goldfinger",
            "draft": {
                "category": "goldfinger",
                "name": "万劫翻盘令",
                "desc": "你像被一枚无形令牌庇护，越是倒霉越容易翻盘。",
                "story_prompt": "若出现险境，请强调翻盘感。",
                "effects": {
                    "extra_luck": 10,
                    "extra_breakthrough_success_rate": 0.1,
                },
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "ok"
    assert payload["item"]["is_custom"] is True
    assert payload["item"]["id"] >= 930001


def test_create_custom_goldfinger_api_accepts_numeric_string_effect_values():
    from src.classes.custom_content import CustomContentRegistry

    CustomContentRegistry.reset()
    client = TestClient(main.app)
    response = client.post(
        "/api/v1/command/avatar/create-custom-content",
        json={
            "category": "goldfinger",
            "draft": {
                "category": "goldfinger",
                "name": "天运回响",
                "desc": "你总能从命运回响里捞到一点额外好处。",
                "effects": {
                    "extra_luck": "14",
                    "extra_breakthrough_success_rate": "0.12",
                },
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["status"] == "ok"
    assert payload["item"]["is_custom"] is True
    assert payload["item"]["effect_desc"]


def test_create_custom_goldfinger_api_rejects_noncanonical_effect_keys():
    client = TestClient(main.app)
    response = client.post(
        "/api/v1/command/avatar/create-custom-content",
        json={
            "category": "goldfinger",
            "draft": {
                "category": "goldfinger",
                "name": "命数偏爱",
                "desc": "你总能从命数的缝隙里捞到一点好处。",
                "effects": {
                    "luck_boost": 15,
                },
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported custom effect: luck_boost."


@pytest.mark.asyncio
async def test_generate_custom_goldfinger_draft_passes_allowed_effects_to_llm():
    from src.server.services.custom_goldfinger_service import generate_custom_goldfinger_draft

    with patch(
        "src.server.services.custom_goldfinger_service.call_llm_with_task_name",
        new_callable=AsyncMock,
    ) as mock_call:
        mock_call.return_value = {
            "name": "天命签到簿",
            "desc": "一本只会在你心底翻页的天命簿册。",
            "story_prompt": "请围绕签到感与命数回报展开。",
            "effects": {"extra_luck": 12},
            "rarity": "SSR",
        }

        draft = await generate_custom_goldfinger_draft("想要一个偏签到流、数值稍强的外挂")

    assert draft["category"] == "goldfinger"
    assert mock_call.await_count == 1
    infos = mock_call.await_args.kwargs["infos"]
    assert "allowed_effects" in infos
    assert "extra_luck" in infos["allowed_effects"]
