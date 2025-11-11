"""动态布局计算模块

根据屏幕分辨率动态计算所有UI组件的尺寸，实现自适应布局。
"""
from typing import NamedTuple


class LayoutConfig(NamedTuple):
    """布局配置类，包含所有动态计算的尺寸参数"""
    
    # 屏幕尺寸
    screen_width: int
    screen_height: int
    
    # 地图相关
    tile_size: int
    margin: int
    
    # UI组件尺寸
    status_bar_height: int
    sidebar_width: int
    
    # 字体尺寸
    font_size_normal: int      # 普通文本（原14）
    font_size_medium: int      # 中等文本（原16）
    font_size_large: int       # 大文本（原18）
    font_size_tooltip: int     # tooltip文本（原14）
    
    # 其他动态参数
    avatar_size: int           # avatar图像大小
    tooltip_min_width: int     # tooltip最小宽度


def clamp(value: float, min_val: float, max_val: float) -> int:
    """将值限制在指定范围内并返回整数"""
    return int(max(min_val, min(max_val, value)))


def calculate_layout(screen_width: int, screen_height: int, map_width: int = 56, map_height: int = 40) -> LayoutConfig:
    """
    根据屏幕分辨率计算所有布局参数
    
    Args:
        screen_width: 屏幕宽度（像素）
        screen_height: 屏幕高度（像素）
        map_width: 地图宽度（格子数）
        map_height: 地图高度（格子数）
    
    Returns:
        LayoutConfig: 包含所有布局参数的配置对象
    """
    
    # 1. 计算固定UI组件尺寸（使用混合策略：百分比 + 最小最大值限制）
    
    # 状态栏高度：屏幕高度的2.5%，限制在24-48px
    status_bar_height = clamp(screen_height * 0.025, 24, 48)
    
    # 侧边栏宽度：屏幕宽度的18%，限制在280-420px
    sidebar_width = clamp(screen_width * 0.18, 280, 420)
    
    # 边距：屏幕较短边的0.8%，限制在6-16px
    margin = clamp(min(screen_width, screen_height) * 0.008, 6, 16)
    
    # 2. 计算地图区域可用空间
    available_width = screen_width - sidebar_width - margin * 2
    available_height = screen_height - status_bar_height - margin * 2
    
    # 3. 计算tile_size（保证完整显示地图）
    tile_size_by_width = available_width / map_width
    tile_size_by_height = available_height / map_height
    
    # 取较小值确保两个方向都能完整显示，并限制最大值为64px（防止超大屏幕显示异常）
    tile_size = clamp(min(tile_size_by_width, tile_size_by_height), 1, 64)
    
    # 4. 计算字体尺寸（根据tile_size动态缩放）
    # 基准：tile_size=32时，字体大小为 14/16/18
    font_scale = tile_size / 32.0
    
    font_size_normal = max(14, int(14 * font_scale))      # 最小14px保证可读性
    font_size_medium = max(16, int(16 * font_scale))
    font_size_large = max(18, int(18 * font_scale))
    font_size_tooltip = max(14, int(14 * font_scale))
    
    # 5. 计算avatar尺寸（与原来的公式保持一致，但基于动态tile_size）
    avatar_size = max(20, int((tile_size * 4 // 3) * 1.8))
    
    # 6. 计算tooltip最小宽度（原来是260px，按比例缩放）
    tooltip_min_width = max(200, int(260 * font_scale))
    
    return LayoutConfig(
        screen_width=screen_width,
        screen_height=screen_height,
        tile_size=tile_size,
        margin=margin,
        status_bar_height=status_bar_height,
        sidebar_width=sidebar_width,
        font_size_normal=font_size_normal,
        font_size_medium=font_size_medium,
        font_size_large=font_size_large,
        font_size_tooltip=font_size_tooltip,
        avatar_size=avatar_size,
        tooltip_min_width=tooltip_min_width,
    )


def get_fullscreen_resolution(pygame_mod) -> tuple[int, int]:
    """
    获取当前显示器的可用分辨率（排除任务栏）
    
    Args:
        pygame_mod: pygame模块
        
    Returns:
        (width, height): 可用屏幕分辨率
    """
    # 初始化video模块（如果还未初始化）
    if not pygame_mod.get_init():
        pygame_mod.init()
    
    # 获取显示器信息
    info = pygame_mod.display.Info()
    
    # 获取桌面可用区域（排除任务栏等）
    # 在Windows上，current_w/h 是全屏分辨率
    # 我们需要预留一些空间给任务栏（通常在底部约40-60像素）
    width = info.current_w
    height = info.current_h
    
    # 为任务栏预留空间（约40-50像素，取决于缩放比例）
    # 这是一个保守的估计，确保窗口不会覆盖任务栏
    taskbar_height = max(40, int(height * 0.04))  # 约4%的高度
    
    return width, height - taskbar_height


__all__ = ["LayoutConfig", "calculate_layout", "get_fullscreen_resolution"]

