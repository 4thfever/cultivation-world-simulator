from typing import List


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


def draw_sidebar(pygame_mod, screen, colors, font, events: List[object],
                 world_map, tile_size: int, margin: int, sidebar_width: int):
    sidebar_x = world_map.width * tile_size + margin * 2
    sidebar_y = margin

    sidebar_rect = pygame_mod.Rect(sidebar_x, sidebar_y, sidebar_width,
                                   screen.get_height() - margin * 2)
    pygame_mod.draw.rect(screen, colors["sidebar_bg"], sidebar_rect)
    pygame_mod.draw.rect(screen, colors["sidebar_border"], sidebar_rect, 2)

    title_text = "事件历史"
    title_surf = font.render(title_text, True, colors["text"])
    title_x = sidebar_x + 10
    title_y = sidebar_y + 10
    screen.blit(title_surf, (title_x, title_y))

    line_y = title_y + title_surf.get_height() + 10
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


__all__ = ["draw_sidebar"]


