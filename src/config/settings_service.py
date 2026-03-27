from __future__ import annotations

import json
import shutil
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .data_paths import get_data_paths
from .settings_schema import (
    AppSettings,
    AppSettingsPatch,
    AppSettingsView,
    AudioSettings,
    LLMConfigView,
    LLMProfile,
    LLMSecrets,
    LLMSettingsUpdate,
    NewGameDefaults,
    RunConfig,
)


def _model_to_dict(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    tmp_path.replace(path)


class SettingsService:
    def __init__(self) -> None:
        self.paths = get_data_paths()

    def _load_model(self, path: Path, model_cls, default_model):
        if not path.exists():
            return default_model

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return model_cls(**data)
        except (OSError, json.JSONDecodeError, ValidationError):
            backup = self.paths.incompatible_dir / f"{path.stem}.corrupt{path.suffix}"
            try:
                shutil.copy2(path, backup)
            except OSError:
                pass
            return default_model

    def _save_settings(self, settings: AppSettings) -> None:
        _atomic_write_json(self.paths.settings_file, _model_to_dict(settings))

    def _save_secrets(self, secrets: LLMSecrets) -> None:
        _atomic_write_json(self.paths.secrets_file, _model_to_dict(secrets))

    def get_settings(self) -> AppSettings:
        settings = self._load_model(self.paths.settings_file, AppSettings, AppSettings())
        self._save_settings(settings)
        return settings

    def get_secrets(self) -> LLMSecrets:
        secrets = self._load_model(self.paths.secrets_file, LLMSecrets, LLMSecrets())
        if self.paths.secrets_file.exists():
            return secrets
        self._save_secrets(secrets)
        return secrets

    def get_settings_view(self) -> AppSettingsView:
        settings = self.get_settings()
        secrets = self.get_secrets()
        payload = _model_to_dict(settings)
        payload["llm"]["profile"]["has_api_key"] = bool(secrets.api_key)
        return AppSettingsView(**payload)

    def patch_settings(self, patch: AppSettingsPatch) -> AppSettingsView:
        settings = self.get_settings()
        payload = _model_to_dict(settings)
        patch_payload = {
            key: value
            for key, value in _model_to_dict(patch).items()
            if value is not None
        }

        if patch_payload.get("ui"):
            ui_patch = patch_payload["ui"]
            if ui_patch.get("locale") is not None:
                payload["ui"]["locale"] = ui_patch["locale"]
            if ui_patch.get("audio"):
                audio_patch = ui_patch["audio"]
                if audio_patch.get("bgm_volume") is not None:
                    payload["ui"]["audio"]["bgm_volume"] = audio_patch["bgm_volume"]
                if audio_patch.get("sfx_volume") is not None:
                    payload["ui"]["audio"]["sfx_volume"] = audio_patch["sfx_volume"]

        if patch_payload.get("simulation"):
            sim_patch = patch_payload["simulation"]
            if sim_patch.get("auto_save_enabled") is not None:
                payload["simulation"]["auto_save_enabled"] = sim_patch["auto_save_enabled"]
            if sim_patch.get("max_auto_saves") is not None:
                payload["simulation"]["max_auto_saves"] = sim_patch["max_auto_saves"]

        if patch_payload.get("new_game_defaults"):
            draft_patch = patch_payload["new_game_defaults"]
            for key, value in draft_patch.items():
                if value is not None:
                    payload["new_game_defaults"][key] = value

        updated = AppSettings(**payload)
        self._save_settings(updated)
        return self.get_settings_view()

    def reset_settings(self) -> AppSettingsView:
        defaults = AppSettings()
        self._save_settings(defaults)
        self._save_secrets(LLMSecrets())
        return self.get_settings_view()

    def get_llm_view(self) -> LLMConfigView:
        return LLMConfigView(**_model_to_dict(self.get_settings_view().llm.profile))

    def update_llm(self, update: LLMSettingsUpdate) -> LLMConfigView:
        settings = self.get_settings()
        secrets = self.get_secrets()

        profile = LLMProfile(
            base_url=update.base_url,
            model_name=update.model_name,
            fast_model_name=update.fast_model_name,
            mode=update.mode,
            max_concurrent_requests=update.max_concurrent_requests,
            has_api_key=settings.llm.profile.has_api_key,
            api_format=update.api_format,
        )

        if update.clear_api_key:
            secrets.api_key = ""
        elif update.api_key is not None and update.api_key != "":
            secrets.api_key = update.api_key

        profile.has_api_key = bool(secrets.api_key)
        settings.llm.profile = profile

        self._save_settings(settings)
        self._save_secrets(secrets)
        return self.get_llm_view()

    def get_llm_runtime_config(self) -> tuple[LLMProfile, str]:
        settings = self.get_settings()
        secrets = self.get_secrets()
        return settings.llm.profile, secrets.api_key

    def get_llm_test_payload(self, update: LLMSettingsUpdate) -> tuple[LLMProfile, str]:
        settings = self.get_settings()
        secrets = self.get_secrets()
        candidate_key = update.api_key if update.api_key not in (None, "") else secrets.api_key
        if update.clear_api_key:
            candidate_key = ""
        profile = LLMProfile(
            base_url=update.base_url,
            model_name=update.model_name,
            fast_model_name=update.fast_model_name,
            mode=update.mode,
            max_concurrent_requests=update.max_concurrent_requests,
            has_api_key=bool(candidate_key),
            api_format=update.api_format,
        )
        return profile, candidate_key

    def get_new_game_defaults(self) -> NewGameDefaults:
        return deepcopy(self.get_settings().new_game_defaults)

    def get_default_run_config(self) -> RunConfig:
        return RunConfig(**_model_to_dict(self.get_new_game_defaults()))


@lru_cache(maxsize=1)
def get_settings_service() -> SettingsService:
    return SettingsService()


def reset_settings_service_cache() -> None:
    get_settings_service.cache_clear()
