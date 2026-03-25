from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

from src.config import AppSettingsPatch, LLMSettingsUpdate, get_data_paths, get_settings_service
from src.i18n.locale_registry import get_default_locale, get_fallback_locale


def test_settings_service_creates_defaults_in_data_root():
    service = get_settings_service()
    settings = service.get_settings_view()
    paths = get_data_paths()

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

    old_local_config = Path("static/local_config.yml")
    before = old_local_config.read_text(encoding="utf-8") if old_local_config.exists() else None

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
    after = old_local_config.read_text(encoding="utf-8") if old_local_config.exists() else None
    assert before == after


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
