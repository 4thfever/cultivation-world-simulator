"""
稀有度系统
定义角色特质、物品等的稀有度等级
"""
from enum import Enum
from dataclasses import dataclass
from src.classes.color import Color, RARITY_COLORS


class RarityLevel(Enum):
    """稀有度等级"""
    N = "N"      # Normal - 普通
    R = "R"      # Rare - 稀有
    SR = "SR"    # Super Rare - 超稀有
    SSR = "SSR"  # Super Super Rare - 传说


@dataclass
class Rarity:
    """
    稀有度配置
    包含等级、权重、颜色等信息
    """
    level: RarityLevel
    weight: float
    color_rgb: tuple[int, int, int]  # RGB颜色值
    color_hex: str  # 十六进制颜色值
    chinese_name: str
    
    def __str__(self) -> str:
        return self.chinese_name


# 稀有度配置表
RARITY_CONFIGS = {
    RarityLevel.N: Rarity(
        level=RarityLevel.N,
        weight=10.0,
        color_rgb=RARITY_COLORS["N"],
        color_hex="#FFFFFF",
        chinese_name="普通"
    ),
    RarityLevel.R: Rarity(
        level=RarityLevel.R,
        weight=5.0,
        color_rgb=RARITY_COLORS["R"],
        color_hex="#4A90E2",
        chinese_name="稀有"
    ),
    RarityLevel.SR: Rarity(
        level=RarityLevel.SR,
        weight=3.0,
        color_rgb=RARITY_COLORS["SR"],
        color_hex="#9370DB",
        chinese_name="超稀有"
    ),
    RarityLevel.SSR: Rarity(
        level=RarityLevel.SSR,
        weight=1.0,
        color_rgb=RARITY_COLORS["SSR"],
        color_hex="#FFD700",
        chinese_name="传说"
    ),
}


def get_rarity_from_str(rarity_str: str) -> Rarity:
    """
    从字符串获取稀有度配置
    
    Args:
        rarity_str: 稀有度字符串，如 "N", "R", "SR", "SSR"
    
    Returns:
        Rarity: 稀有度配置对象，若无法识别则返回N
    """
    rarity_str = str(rarity_str).strip().upper()
    try:
        level = RarityLevel(rarity_str)
        return RARITY_CONFIGS[level]
    except (ValueError, KeyError):
        # 默认返回普通稀有度
        return RARITY_CONFIGS[RarityLevel.N]


def get_weight_from_rarity(rarity_str: str) -> float:
    """
    根据稀有度字符串获取权重
    
    Args:
        rarity_str: 稀有度字符串
    
    Returns:
        float: 对应的权重值
    """
    rarity = get_rarity_from_str(rarity_str)
    return rarity.weight
