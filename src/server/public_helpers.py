from __future__ import annotations

import hashlib
import os
import re

from src.config import RunConfig, get_settings_service
from src.classes.custom_content import CustomContentRegistry
from src.run.data_loader import reload_all_static_data


def model_to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def get_runtime_run_config(runtime) -> RunConfig:
    run_config = runtime.get("run_config")
    if run_config:
        return RunConfig(**run_config)
    return get_settings_service().get_default_run_config()


def reset_runtime_custom_content() -> None:
    CustomContentRegistry.reset()


def apply_runtime_content_locale(*, game_instance: dict, language_manager, lang_code: str) -> None:
    from src.utils.config import update_paths_for_language
    from src.utils.df import reload_game_configs

    language_manager.set_language(lang_code)
    update_paths_for_language(lang_code)
    reload_game_configs()
    reload_all_static_data()

    world = game_instance.get("world")
    if world:
        from src.run.data_loader import fix_runtime_references

        fix_runtime_references(world)


def scan_avatar_assets(*, assets_path: str) -> dict[str, list[int]]:
    def get_ids(subdir: str) -> list[int]:
        directory = os.path.join(assets_path, subdir)
        if not os.path.exists(directory):
            return []
        ids: list[int] = []
        for filename in os.listdir(directory):
            if not filename.lower().endswith(".png"):
                continue
            try:
                ids.append(int(os.path.splitext(filename)[0]))
            except ValueError:
                pass
        return sorted(ids)

    avatar_assets = {
        "males": get_ids("males"),
        "females": get_ids("females"),
    }
    print(
        f"Loaded avatar assets: {len(avatar_assets['males'])} males, "
        f"{len(avatar_assets['females'])} females"
    )
    return avatar_assets


def resolve_avatar_pic_id(*, avatar_assets: dict[str, list[int]], avatar) -> int:
    if avatar is None:
        return 1
    custom_pic_id = getattr(avatar, "custom_pic_id", None)
    if custom_pic_id is not None:
        return custom_pic_id

    gender_val = getattr(getattr(avatar, "gender", None), "value", "male")
    key = "females" if gender_val == "female" else "males"
    available = avatar_assets.get(key, [])
    if not available:
        return 1

    hash_bytes = hashlib.md5(str(getattr(avatar, "id", "")).encode("utf-8")).digest()
    hash_int = int.from_bytes(hash_bytes[:4], byteorder="little")
    idx = hash_int % len(available)
    return available[idx]


def resolve_avatar_action_emoji(avatar) -> str:
    if not avatar:
        return ""
    curr = getattr(avatar, "current_action", None)
    if not curr:
        return ""
    act_instance = getattr(curr, "action", None)
    if not act_instance:
        return ""
    return getattr(act_instance, "EMOJI", "")


def validate_save_name(name: str) -> bool:
    if not name or len(name) > 50:
        return False
    return bool(re.match(r"^[\w\u4e00-\u9fff]+$", name))
