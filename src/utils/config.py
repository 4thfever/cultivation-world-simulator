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
