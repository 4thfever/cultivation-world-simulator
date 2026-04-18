from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.config import AppSettingsPatch, LLMSettingsUpdate, get_data_paths, get_settings_service
from src.i18n.locale_registry import get_default_locale, get_fallback_locale


def test_settings_service_creates_defaults_in_data_root():
    service = get_settings_service()
    settings = service.get_settings_view()
    paths = get_data_paths()

    assert settings.schema_version == 2
    assert settings.ui.locale == get_default_locale()
    assert paths.settings_file.exists()
    assert paths.secrets_file.exists()
    assert paths.saves_dir.exists()


def test_settings_service_updates_llm_secret_without_exposing_key():
    service = get_settings_service()
    updated = service.update_llm(
        LLMSettingsUpdate(
            base_url="https://api.example.com/v1",
            api_key="secret-key",
            model_name="model-a",
            fast_model_name="model-b",
            mode="default",
            max_concurrent_requests=12,
            clear_api_key=False,
        )
    )

    profile, api_key = service.get_llm_runtime_config()

    assert updated.has_api_key is True
    assert profile.base_url == "https://api.example.com/v1"
    assert api_key == "secret-key"
    assert "secret-key" not in get_data_paths().settings_file.read_text(encoding="utf-8")
    assert "secret-key" in get_data_paths().secrets_file.read_text(encoding="utf-8")


def test_patch_settings_updates_audio_and_new_game_defaults():
    service = get_settings_service()
    fallback_locale = get_fallback_locale()
    updated = service.patch_settings(
        AppSettingsPatch(
            ui={"audio": {"bgm_volume": 0.7}},
            new_game_defaults={"init_npc_num": 20, "content_locale": fallback_locale},
        )
    )

    assert updated.ui.audio.bgm_volume == 0.7
    assert updated.new_game_defaults.init_npc_num == 20
    assert updated.new_game_defaults.content_locale == fallback_locale


def test_patch_settings_syncs_content_locale_with_ui_locale():
    service = get_settings_service()
    fallback_locale = get_fallback_locale()

    updated = service.patch_settings(
        AppSettingsPatch(
            ui={"locale": fallback_locale},
        )
    )

    assert updated.ui.locale == fallback_locale
    assert updated.new_game_defaults.content_locale == fallback_locale


def test_settings_api_and_start_game(monkeypatch):
    from src.server import main
    default_locale = get_default_locale()
    fallback_locale = get_fallback_locale()

    monkeypatch.setattr(main, "init_game_async", AsyncMock())

    def fake_create_task(coro):
        coro.close()
        return None

    monkeypatch.setattr(main.asyncio, "create_task", fake_create_task)

    settings_res = main.get_settings()
    assert settings_res["ui"]["locale"] == default_locale

    patch_res = main.patch_settings(
        AppSettingsPatch(
            simulation={"auto_save_enabled": True},
            new_game_defaults={"content_locale": fallback_locale},
        )
    )
    assert patch_res["simulation"]["auto_save_enabled"] is True

    start_res = asyncio.run(
        main.start_game(
            main.GameStartRequest(
                content_locale=fallback_locale,
                init_npc_num=18,
                sect_num=4,
                npc_awakening_rate_per_month=0.02,
                world_lore="A fractured world",
            )
        )
    )
    assert start_res["status"] == "ok"
    assert main.game_instance["run_config"]["content_locale"] == fallback_locale
    assert main.game_instance["run_config"]["init_npc_num"] == 18


def test_runtime_run_config_comes_only_from_settings_defaults(monkeypatch):
    from src.server import main

    service = get_settings_service()
    service.patch_settings(
        AppSettingsPatch(
            new_game_defaults={
                "content_locale": get_fallback_locale(),
                "init_npc_num": 22,
                "sect_num": 5,
                "npc_awakening_rate_per_month": 0.03,
                "world_lore": "Fresh defaults",
            }
        )
    )

    monkeypatch.setitem(main.game_instance, "run_config", None)
    runtime = main.get_runtime_run_config()

    assert runtime.content_locale == get_fallback_locale()
    assert runtime.init_npc_num == 22
    assert runtime.sect_num == 5
    assert runtime.npc_awakening_rate_per_month == 0.03
    assert runtime.world_lore == "Fresh defaults"


def test_main_patch_settings_syncs_runtime_locale_and_run_config(monkeypatch):
    from src.server import main

    applied_locales: list[str] = []

    monkeypatch.setattr(main, "apply_runtime_content_locale", lambda lang_code: applied_locales.append(lang_code))
    monkeypatch.setattr(main, "language_manager", "zh-CN")
    monkeypatch.setitem(main.game_instance, "run_config", {"content_locale": "zh-CN"})

    res = main.patch_settings(
        AppSettingsPatch(
            ui={"locale": get_fallback_locale()},
        )
    )

    assert res["ui"]["locale"] == get_fallback_locale()
    assert res["new_game_defaults"]["content_locale"] == get_fallback_locale()
    assert applied_locales == [get_fallback_locale()]
    assert main.game_instance["run_config"]["content_locale"] == get_fallback_locale()


def test_settings_patch_api_returns_200_when_router_serializes_model(monkeypatch):
    from src.server import main

    applied_locales: list[str] = []

    monkeypatch.setattr(main, "apply_runtime_content_locale", lambda lang_code: applied_locales.append(lang_code))
    monkeypatch.setattr(main, "language_manager", "zh-CN")
    monkeypatch.setitem(main.game_instance, "run_config", {"content_locale": "zh-CN"})

    client = TestClient(main.app)
    response = client.patch(
        "/api/settings",
        json={
            "ui": {
                "locale": get_fallback_locale(),
            }
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ui"]["locale"] == get_fallback_locale()
    assert payload["new_game_defaults"]["content_locale"] == get_fallback_locale()
    assert applied_locales == [get_fallback_locale()]


def test_settings_reset_api_returns_200_when_router_serializes_model(monkeypatch):
    from src.server import main

    applied_locales: list[str] = []

    monkeypatch.setattr(main, "apply_runtime_content_locale", lambda lang_code: applied_locales.append(lang_code))
    monkeypatch.setattr(main, "language_manager", "en-US")
    monkeypatch.setitem(main.game_instance, "run_config", {"content_locale": "en-US"})

    client = TestClient(main.app)
    response = client.post("/api/settings/reset")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ui"]["locale"] == get_default_locale()
    assert payload["new_game_defaults"]["content_locale"] == get_default_locale()
    assert applied_locales == [get_default_locale()]


def test_llm_api_uses_saved_secret_when_testing(monkeypatch):
    from src.server import main

    service = get_settings_service()
    service.update_llm(
        LLMSettingsUpdate(
            base_url="https://api.example.com/v1",
            api_key="stored-secret",
            model_name="model-a",
            fast_model_name="model-b",
            mode="default",
            max_concurrent_requests=10,
            clear_api_key=False,
        )
    )

    captured = {}

    def fake_test_connectivity(config):
        captured["api_key"] = config.api_key
        return True, ""

    monkeypatch.setattr(main, "test_connectivity", fake_test_connectivity)
    res = main.test_llm_connection(
        LLMSettingsUpdate(
            base_url="https://api.example.com/v1",
            api_key="",
            model_name="model-a",
            fast_model_name="model-b",
            mode="default",
            max_concurrent_requests=10,
            clear_api_key=False,
        )
    )

    assert res["status"] == "ok"
    assert captured["api_key"] == "stored-secret"
