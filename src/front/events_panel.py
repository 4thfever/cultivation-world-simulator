from typing import List


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
    max_events = (screen.get_height() - event_y - margin) // 20
    recent_events = events[-max_events:] if len(events) > max_events else events
    for event in reversed(recent_events):
        event_text = str(event)
        if len(event_text) > 35:
            event_text = event_text[:32] + "..."
        event_surf = font.render(event_text, True, colors["event_text"])
        screen.blit(event_surf, (title_x, event_y))
        event_y += 20
        if event_y > screen.get_height() - margin:
            break

    if not events:
        no_event_text = "暂无事件"
        no_event_surf = font.render(no_event_text, True, colors["event_text"])
        screen.blit(no_event_surf, (title_x, event_y))


__all__ = ["draw_sidebar"]


