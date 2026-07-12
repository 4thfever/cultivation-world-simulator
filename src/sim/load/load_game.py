"""
读档功能模块。

顶层函数只负责路径解析、文件 IO、section registry 编排和错误处理。具体恢复
顺序集中在 save/load section registry 中维护。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

import src.utils.config as app_config
from src.sim.save.sections.base import LoadContext
from src.sim.save.sections.registry import restore_loaded_game

if TYPE_CHECKING:
    from src.classes.core.sect import Sect
    from src.classes.core.world import World
    from src.sim.simulator import Simulator


def get_events_db_path(save_path: Path) -> Path:
    """
    根据存档路径计算事件数据库路径。

    例如：save_20260105_1423.json -> save_20260105_1423_events.db
    """
    return save_path.with_suffix("").with_name(save_path.stem + "_events.db")


def _get_current_saves_dir() -> Path:
    return Path(app_config.CONFIG.paths.saves)


def _resolve_load_path(save_path: Optional[Path]) -> Path:
    if save_path is None:
        return _get_current_saves_dir() / "save.json"
    return Path(save_path)


def load_game(save_path: Optional[Path] = None) -> Tuple["World", "Simulator", List["Sect"]]:
    """从文件加载游戏状态。"""
    resolved_save_path = _resolve_load_path(save_path)
    if not resolved_save_path.exists():
        raise FileNotFoundError(f"存档文件不存在: {resolved_save_path}")

    try:
        with open(resolved_save_path, "r", encoding="utf-8") as f:
            save_data = json.load(f)

        meta = save_data.get("meta", {})
        print(
            f"Loading save (Version: {meta.get('version', 'unknown')}, "
            f"游戏时间: {meta.get('game_time', 'unknown')})"
        )

        context = LoadContext(save_path=resolved_save_path, save_data=save_data)
        world, simulator, existed_sects = restore_loaded_game(context)
        loaded_count = len(context.all_avatars or {})
        print(f"Save loaded successfully! Loaded {loaded_count} avatars")
        return world, simulator, existed_sects
    except Exception as exc:
        print(f"Failed to load game: {exc}")
        import traceback

        traceback.print_exc()
        raise


def check_save_compatibility(save_path: Path) -> Tuple[bool, str]:
    """检查存档兼容性。当前开发阶段不做严格版本阻断。"""
    try:
        with open(save_path, "r", encoding="utf-8") as f:
            json.load(f)
        return True, ""
    except Exception as exc:
        return False, f"无法读取存档文件: {exc}"
