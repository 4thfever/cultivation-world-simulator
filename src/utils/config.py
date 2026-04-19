"""
静态配置管理模块。

只读取版本内置的 `static/config.yml`，并负责按语言解析静态资源路径。
用户设置、敏感信息和本局运行参数不在这里维护。
"""
from pathlib import Path

from omegaconf import OmegaConf

from src.config.data_paths import get_data_paths
from src.i18n.locale_registry import (
    get_default_locale,
    get_project_root,
    normalize_locale_code,
)


def get_static_config_path() -> Path:
    """Return the built-in static config path under the project root."""
    return get_project_root() / "static" / "config.yml"


def _resolve_resource_path(value: str | Path, project_root: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return project_root / path

def load_config():
    """
    加载配置文件
    
    Returns:
        DictConfig: 合并后的配置对象
    """
    project_root = get_project_root()
    base_config_path = get_static_config_path()
    # 读取基础配置
    base_config = OmegaConf.create({})
    if base_config_path.exists():
        base_config = OmegaConf.load(base_config_path)

    config = base_config

    if not hasattr(config, "resources"):
        config.resources = OmegaConf.create({})
    else:
        for key, value in config.resources.items():
            config.resources[key] = _resolve_resource_path(value, project_root)

    # 运行时用户数据目录由 data_paths 注入，不再写在静态配置里。
    config.paths = OmegaConf.create({})
    config.paths.saves = get_data_paths().saves_dir
    
    return config

# 导出配置对象
CONFIG = load_config()

def update_paths_for_language(lang_code: str | None = None):
    """根据显式语言更新静态资源路径。"""
    if lang_code is None:
        lang_code = get_default_locale()

    lang_code = normalize_locale_code(lang_code)

    resources = getattr(CONFIG, "resources", OmegaConf.create({}))
    project_root = get_project_root()

    locales_dir = Path(resources.get("locales_dir", project_root / "static" / "locales"))
    target_dir = locales_dir / lang_code

    CONFIG.paths.locales = locales_dir
    CONFIG.paths.shared_game_configs = Path(
        resources.get("shared_game_configs_dir", project_root / "static" / "game_configs")
    )
    CONFIG.paths.localized_game_configs = target_dir / "game_configs"
    CONFIG.paths.game_configs = CONFIG.paths.shared_game_configs
    CONFIG.paths.templates = target_dir / "templates"

    if not CONFIG.paths.game_configs.exists():
        print(f"[Config] Warning: Game configs dir not found at {CONFIG.paths.game_configs}")
    else:
        print(f"[Config] Switched language context to {lang_code}")

# 模块加载时初始化默认语言下的路径，避免 import 时 KeyError。
update_paths_for_language()

