from typing import List, Optional, Tuple, Dict
from .rendering import map_pixel_size


def _wrap_text_by_pixels(font, text: str, max_width_px: int) -> List[str]:
    """
    按像素宽度对单行文本进行硬换行，适配中英文混排（逐字符测量）。
    """
    if not text:
        return [""]
    lines: List[str] = []
    current = ""
    for ch in str(text):
        test = current + ch
        w, _ = font.size(test)
        if w <= max_width_px:
            current = test
        else:
            if current:
                lines.append(current)
            # 新行从当前字符开始
            current = ch
    if current:
        lines.append(current)
    return lines


def draw_sidebar(
    pygame_mod,
    screen,
    colors,
    font,
    events: List[object],
    world_map,
    tile_size: int,
    margin: int,
    sidebar_width: int,
    status_bar_height: int,
    *,
    filter_selected_label: str,
    filter_is_open: bool,
    filter_options: List[Tuple[str, Optional[str]]],
    current_phenomenon = None,
    phenomenon_start_year: int = 0,
    current_year: int = 0,
) -> Dict[str, object]:
    map_px_w, _ = map_pixel_size(type("_W", (), {"map": world_map})(), tile_size)
    sidebar_x = map_px_w + margin * 2
    sidebar_y = margin + status_bar_height

    sidebar_rect = pygame_mod.Rect(
        sidebar_x,
        sidebar_y,
        sidebar_width,
        screen.get_height() - sidebar_y - margin,
    )
    pygame_mod.draw.rect(screen, colors["sidebar_bg"], sidebar_rect)
    pygame_mod.draw.rect(screen, colors["sidebar_border"], sidebar_rect, 2)

    # 天地灵机显示区域（放在最上方）
    content_start_y = sidebar_y + 10
    if current_phenomenon is not None:
        phenomenon_margin_x = 10
        phenomenon_width = sidebar_width - 20
        phenomenon_x = sidebar_x + phenomenon_margin_x
        phenomenon_y = content_start_y
        
        # 计算持续时间
        elapsed_years = current_year - phenomenon_start_year
        remaining_years = max(0, current_phenomenon.duration_years - elapsed_years)
        
        # 天象名称（使用稀有度颜色）
        rarity_color = current_phenomenon.rarity.color_rgb
        name_surf = font.render(f"天象：{current_phenomenon.name}", True, rarity_color)
        screen.blit(name_surf, (phenomenon_x, phenomenon_y))
        phenomenon_y += name_surf.get_height() + 4
        
        # 描述文字（自动换行）
        usable_width = phenomenon_width
        desc_lines = _wrap_text_by_pixels(font, current_phenomenon.desc, usable_width)
        for line in desc_lines:
            line_surf = font.render(line, True, colors["event_text"])
            screen.blit(line_surf, (phenomenon_x, phenomenon_y))
            phenomenon_y += line_surf.get_height() + 2
        
        # 剩余时间
        time_text = f"剩余：{remaining_years}年"
        time_surf = font.render(time_text, True, colors["event_text"])
        screen.blit(time_surf, (phenomenon_x, phenomenon_y))
        phenomenon_y += time_surf.get_height() + 8
        
        # 分隔线
        pygame_mod.draw.line(screen, colors["sidebar_border"],
                             (sidebar_x + 10, phenomenon_y),
                             (sidebar_x + sidebar_width - 10, phenomenon_y), 1)
        
        content_start_y = phenomenon_y + 10

    # 下拉选择器：显示"所有人/某人"，位于天地灵机下方
    dropdown_margin_x = 10
    dropdown_width = sidebar_width - 20
    # 先用一个基准高度，确保点击区域更易操作
    dropdown_height = 24
    dropdown_x = sidebar_x + dropdown_margin_x
    dropdown_y = content_start_y
    dropdown_rect = pygame_mod.Rect(dropdown_x, dropdown_y, dropdown_width, dropdown_height)
    # 填充底色并描边
    pygame_mod.draw.rect(screen, colors["sidebar_bg"], dropdown_rect)
    pygame_mod.draw.rect(screen, colors["sidebar_border"], dropdown_rect, 1)
    # 选中项文本
    sel_text = filter_selected_label or "所有"
    sel_surf = font.render(f"筛选：{sel_text}", True, colors["event_text"]) 
    screen.blit(sel_surf, (dropdown_x + 6, dropdown_y + (dropdown_height - sel_surf.get_height()) // 2))
    # 右侧箭头
    arrow_char = "▲" if filter_is_open else "▼"
    arrow_surf = font.render(arrow_char, True, colors["event_text"]) 
    screen.blit(arrow_surf, (dropdown_x + dropdown_width - arrow_surf.get_width() - 6, dropdown_y + (dropdown_height - arrow_surf.get_height()) // 2))

    option_rects: List[Tuple[Optional[str], object]] = []
    options_total_h = 0
    if filter_is_open and filter_options:
        # 整体下拉区域背景，避免与事件文字混在一起
        options_total_h = dropdown_height * len(filter_options)
        options_area_rect = pygame_mod.Rect(dropdown_x, dropdown_y + dropdown_height, dropdown_width, options_total_h)
        pygame_mod.draw.rect(screen, colors["sidebar_bg"], options_area_rect)
        pygame_mod.draw.rect(screen, colors["sidebar_border"], options_area_rect, 1)
        # 逐项绘制
        opt_y = dropdown_y + dropdown_height
        for label, oid in filter_options:
            opt_rect = pygame_mod.Rect(dropdown_x, opt_y, dropdown_width, dropdown_height)
            pygame_mod.draw.rect(screen, colors["sidebar_bg"], opt_rect)
            pygame_mod.draw.rect(screen, colors["sidebar_border"], opt_rect, 1)
            opt_surf = font.render(label, True, colors["event_text"]) 
            screen.blit(opt_surf, (dropdown_x + 6, opt_y + (dropdown_height - opt_surf.get_height()) // 2))
            option_rects.append((oid, opt_rect))
            opt_y += dropdown_height

    # 标题“事件历史”位于筛选下拉之下
    title_text = "事件历史"
    title_surf = font.render(title_text, True, colors["text"])
    title_x = sidebar_x + 10
    title_y = dropdown_y + dropdown_height + (options_total_h if filter_is_open else 0) + 10
    screen.blit(title_surf, (title_x, title_y))

    # 事件列表起始位置位于标题之后
    line_y = title_y + title_surf.get_height() + 6
    pygame_mod.draw.line(screen, colors["sidebar_border"],
                         (sidebar_x + 10, line_y),
                         (sidebar_x + sidebar_width - 10, line_y), 1)

    event_y = line_y + 15
    # 预留左右边距各10px
    usable_width = sidebar_width - 20
    # 从最新事件开始，逐条向下渲染，超出底部则停止
    for event in reversed(events):
        event_text = str(event)
        wrapped_lines = _wrap_text_by_pixels(font, event_text, usable_width)
        for line in wrapped_lines:
            event_surf = font.render(line, True, colors["event_text"])
            screen.blit(event_surf, (title_x, event_y))
            event_y += event_surf.get_height() + 2
            if event_y > screen.get_height() - margin:
                break
        if event_y > screen.get_height() - margin:
            break

    if not events:
        no_event_text = "暂无事件"
        no_event_surf = font.render(no_event_text, True, colors["event_text"])
        screen.blit(no_event_surf, (title_x, event_y))
    return {
        "filter_toggle_rect": dropdown_rect,
        "filter_option_rects": option_rects,
    }


__all__ = ["draw_sidebar"]


