"""
配置管理模块
使用OmegaConf读取config.yml和local_config.yml
"""
from pathlib import Path
from omegaconf import OmegaConf

def load_config():
    """
    加载配置文件
    
    Returns:
        DictConfig: 合并后的配置对象
    """
    static_path = Path("static")

    # 配置文件路径
    base_config_path = static_path / "config.yml"
    local_config_path = static_path / "local_config.yml"
    
    # 读取基础配置
    base_config = OmegaConf.create({})
    if base_config_path.exists():
        base_config = OmegaConf.load(base_config_path)
    
    # 读取本地配置
    local_config = OmegaConf.create({})
    if local_config_path.exists():
        local_config = OmegaConf.load(local_config_path)
    
    # 合并配置，local_config优先级更高
    config = OmegaConf.merge(base_config, local_config)

    # 把paths下的所有值pathlib化
    if hasattr(config, "paths"):
        for key, value in config.paths.items():
            config.paths[key] = Path(value)
    
    return config

# 导出配置对象
CONFIG = load_config()

def update_paths_for_language(lang_code: str = None):
    """根据语言更新 game_configs 和 templates 的路径"""
    from src.classes.language import language_manager
    
    if lang_code is None:
        # 尝试从配置中同步语言状态到 language_manager (针对 CLI/Test 等非 server 环境)
        if hasattr(CONFIG, "system") and hasattr(CONFIG.system, "language"):
            saved_lang = CONFIG.system.language
            
            # Avoid triggering set_language -> df import loop during initialization
            try:
                from src.classes.language import LanguageType
                language_manager._current = LanguageType(saved_lang)
            except (ValueError, ImportError):
                pass
            
            # Reload translations only (safe)
            from src.i18n import reload_translations
            reload_translations()
            
            lang_code = saved_lang
    
    if lang_code is None:
        lang_code = "zh-CN"
        
    # Normalize lang_code (e.g. zh_CN -> zh-CN) to match folder structure in static/locales
    lang_code = lang_code.replace("_", "-")
    
    # 默认 locales 目录
    locales_dir = CONFIG.paths.get("locales", Path("static/locales"))
    
    # 构建特定语言的目录
    target_dir = locales_dir / lang_code
    
    # 更新配置路径
    # 语言无关的配置目录
    CONFIG.paths.shared_game_configs = Path("static/game_configs")
    # 语言相关的配置目录
    CONFIG.paths.localized_game_configs = target_dir / "game_configs"
    
    # CONFIG.paths.game_configs 指向统一的数据源，不再区分语言目录
    # 这里我们保留 CONFIG.paths.game_configs 作为"逻辑概念上的"配置集合根目录（虽然物理上分开了）
    # 但实际上加载逻辑会在 df.py 中处理合并
    CONFIG.paths.game_configs = Path("static/game_configs")
    CONFIG.paths.templates = target_dir / "templates"
    
    # 简单的存在性检查日志
    if not CONFIG.paths.game_configs.exists():
        print(f"[Config] Warning: Game configs dir not found at {CONFIG.paths.game_configs}")
    else:
        print(f"[Config] Switched language context to {lang_code} (Configs using Single Source)")

# 模块加载时自动初始化默认路径，确保 CONFIG.paths.game_configs 存在，避免 import 时 KeyError
update_paths_for_language()

