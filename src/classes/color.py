"""
颜色系统
统一管理游戏中各种等级、稀有度的颜色方案
"""
from __future__ import annotations

import re
from typing import Protocol


class ColorGradable(Protocol):
    """支持颜色分级的协议"""

    @property
    def color_rgb(self) -> tuple[int, int, int]:
        """返回RGB颜色值"""
        ...


# ==================== 通用颜色定义 ====================


class Color:
    """预定义的颜色常量"""

    # 基础颜色
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)

    # 品质颜色 - 从低到高
    COMMON_WHITE = (255, 255, 255)  # 普通/白色
    UNCOMMON_GREEN = (50, 205, 50)  # 不凡/绿色
    RARE_BLUE = (74, 144, 226)  # 稀有/蓝色
    EPIC_PURPLE = (147, 112, 219)  # 史诗/紫色
    LEGENDARY_GOLD = (255, 215, 0)  # 传说/金色


# ==================== 辅助函数 ====================


COLOR_TAG_PATTERN = re.compile(
    r"<color:(\d{1,3}),(\d{1,3}),(\d{1,3})>(.*?)</color>", re.DOTALL
)


def get_color_from_mapping(
    grade_value: object,
    color_mapping: dict,
    default_color: tuple[int, int, int] = Color.COMMON_WHITE,
) -> tuple[int, int, int]:
    """
    从映射字典中获取颜色

    Args:
        grade_value: 等级对象
        color_mapping: 等级到颜色的映射字典
        default_color: 默认颜色

    Returns:
        RGB颜色元组
    """
    return color_mapping.get(grade_value, default_color)


def format_colored_text(text: str, color_rgb: tuple[int, int, int]) -> str:
    """
    将文本格式化为带颜色标记的字符串，供前端渲染使用
    格式：<color:R,G,B>text</color>

    Args:
        text: 要着色的文本
        color_rgb: RGB颜色元组

    Returns:
        带颜色标记的文本字符串
    """
    r, g, b = color_rgb
    return f"<color:{r},{g},{b}>{text}</color>"


def rgb_to_hex(color_rgb: tuple[int, int, int]) -> str:
    """RGB 整数元组转 16 进制字符串（#rrggbb）"""
    r, g, b = color_rgb
    return f"#{r:02x}{g:02x}{b:02x}"


def split_colored_segments(text: str) -> list[dict[str, str]]:
    """
    将包含 <color> 标签的文本拆分为 segments，
    每个 segment 结构：{"text": "...", "color": "#rrggbb"}（color 可选）。
    """
    segments: list[dict[str, str]] = []
    last_index = 0

    for match in COLOR_TAG_PATTERN.finditer(text):
        start, end = match.span()
        if start > last_index:
            plain = text[last_index:start]
            if plain:
                segments.append({"text": plain})

        r, g, b, content = match.groups()
        color_hex = rgb_to_hex((int(r), int(g), int(b)))
        segments.append({"text": content, "color": color_hex})
        last_index = end

    if last_index < len(text):
        trailing = text[last_index:]
        if trailing:
            segments.append({"text": trailing})

    if not segments:
        segments.append({"text": text})

    return segments


# ==================== 颜色方案映射 ====================

# 装备等级颜色方案（普通-宝物-法宝）
EQUIPMENT_GRADE_COLORS = {
    "COMMON": Color.COMMON_WHITE,
    "TREASURE": Color.EPIC_PURPLE,
    "ARTIFACT": Color.LEGENDARY_GOLD,
}

# 稀有度颜色方案（N-R-SR-SSR）
RARITY_COLORS = {
    "N": Color.COMMON_WHITE,
    "R": Color.RARE_BLUE,
    "SR": Color.EPIC_PURPLE,
    "SSR": Color.LEGENDARY_GOLD,
}

# 功法品阶颜色方案（下品-中品-上品）
TECHNIQUE_GRADE_COLORS = {
    "LOWER": Color.COMMON_WHITE,
    "MIDDLE": Color.UNCOMMON_GREEN,
    "UPPER": Color.EPIC_PURPLE,
}

