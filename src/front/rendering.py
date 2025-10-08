import math
from typing import List, Optional, Tuple, Callable
from src.classes.avatar import Avatar, Gender
from src.classes.tile import TileType
from src.utils.text_wrap import wrap_text
from src.classes.relation import Relation
from src.classes.root import format_root_cn

# 顶部状态栏高度（像素）
STATUS_BAR_HEIGHT = 32


def draw_grid(pygame_mod, screen, colors, map_obj, ts: int, m: int, top_offset: int = 0):
    grid_color = colors["grid"]
    for gx in range(map_obj.width + 1):
        start_pos = (m + gx * ts, m + top_offset)
        end_pos = (m + gx * ts, m + top_offset + map_obj.height * ts)
        pygame_mod.draw.line(screen, grid_color, start_pos, end_pos, 1)
    for gy in range(map_obj.height + 1):
        start_pos = (m, m + top_offset + gy * ts)
        end_pos = (m + map_obj.width * ts, m + top_offset + gy * ts)
        pygame_mod.draw.line(screen, grid_color, start_pos, end_pos, 1)


def draw_map(pygame_mod, screen, colors, world, tile_images, ts: int, m: int, top_offset: int = 0):
    map_obj = world.map
    for y in range(map_obj.height):
        for x in range(map_obj.width):
            tile = map_obj.get_tile(x, y)
            tile_image = tile_images.get(tile.type)
            if tile_image:
                pos = (m + x * ts, m + top_offset + y * ts)
                screen.blit(tile_image, pos)
            else:
                color = (80, 80, 80)
                rect = pygame_mod.Rect(m + x * ts, m + top_offset + y * ts, ts, ts)
                pygame_mod.draw.rect(screen, color, rect)
    draw_grid(pygame_mod, screen, colors, map_obj, ts, m, top_offset)


def calculate_font_size_by_area(tile_size: int, area: int) -> int:
    base = int(tile_size * 1.1)
    growth = int(max(0, min(24, (area ** 0.5))))
    return max(16, min(40, base + growth))


def draw_region_labels(pygame_mod, screen, colors, world, get_region_font, tile_size: int, margin: int, top_offset: int = 0, outline_px: int = 2):
    ts = tile_size
    m = margin
    mouse_x, mouse_y = pygame_mod.mouse.get_pos()
    from src.classes.region import regions_by_id
    hovered_region = None

    # 以区域面积降序放置，优先保证大区域标签可读性
    regions = sorted(list(regions_by_id.values()), key=lambda r: getattr(r, "area", 0), reverse=True)

    placed_rects = []  # 已放置标签的矩形列表，用于碰撞检测

    # 可放置范围（地图区域）
    map_px_w = world.map.width * ts
    map_px_h = world.map.height * ts
    min_x_allowed = m
    max_x_allowed = m + map_px_w
    min_y_allowed = m + top_offset
    max_y_allowed = m + top_offset + map_px_h

    def _clamp_rect(x0: int, y0: int, w: int, h: int) -> Tuple[int, int]:
        # 将标签限制在地图区域内
        x = max(min_x_allowed, min(x0, max_x_allowed - w))
        y = max(min_y_allowed, min(y0, max_y_allowed - h))
        return x, y

    for region in regions:
        name = getattr(region, "name", None)
        if not name:
            continue
        center_x, center_y = region.center_loc
        screen_cx = m + center_x * ts + ts // 2
        screen_cy = m + top_offset + center_y * ts + ts // 2
        font_size = calculate_font_size_by_area(tile_size, region.area)
        region_font = get_region_font(font_size)
        text_surface = region_font.render(str(name), True, colors["text"])
        border_surface = region_font.render(str(name), True, colors.get("text_border", (24, 24, 24)))
        text_w = text_surface.get_width()
        text_h = text_surface.get_height()

        # 候选偏移（围绕中心），尽量保持靠近中心位置
        pad = 6
        dxw = max(8, int(0.6 * text_w)) + pad
        dyh = max(6, int(0.6 * text_h)) + pad
        candidates = [
            (0, 0),
            (0, -dyh),
            (0, dyh),
            (-dxw, 0),
            (dxw, 0),
            (-dxw, -dyh),
            (dxw, -dyh),
            (-dxw, dyh),
            (dxw, dyh),
        ]

        chosen_rect = None
        for (dx, dy) in candidates:
            x_try = int(screen_cx + dx - text_w / 2)
            y_try = int(screen_cy + dy - text_h / 2)
            x_try, y_try = _clamp_rect(x_try, y_try, text_w, text_h)
            rect_try = pygame_mod.Rect(x_try, y_try, text_w, text_h)
            if not any(rect_try.colliderect(r) for r in placed_rects):
                chosen_rect = rect_try
                break
        if chosen_rect is None:
            # 如果所有候选均冲突，就退回中心位置
            x0 = int(screen_cx - text_w / 2)
            y0 = int(screen_cy - text_h / 2)
            x0, y0 = _clamp_rect(x0, y0, text_w, text_h)
            chosen_rect = pygame_mod.Rect(x0, y0, text_w, text_h)

        # 悬停检测使用最终位置
        if chosen_rect.collidepoint(mouse_x, mouse_y):
            hovered_region = region

        # 多方向描边
        if outline_px > 0:
            for dx in (-outline_px, 0, outline_px):
                for dy in (-outline_px, 0, outline_px):
                    if dx == 0 and dy == 0:
                        continue
                    screen.blit(border_surface, (chosen_rect.x + dx, chosen_rect.y + dy))
        screen.blit(text_surface, (chosen_rect.x, chosen_rect.y))
        placed_rects.append(chosen_rect)
    return hovered_region


def avatar_center_pixel(avatar: Avatar, tile_size: int, margin: int, top_offset: int = 0) -> Tuple[int, int]:
    px = margin + avatar.pos_x * tile_size + tile_size // 2
    py = margin + top_offset + avatar.pos_y * tile_size + tile_size // 2
    return px, py


def draw_avatars_and_pick_hover(
    pygame_mod,
    screen,
    colors,
    simulator,
    avatar_images,
    tile_size: int,
    margin: int,
    get_display_center: Optional[Callable[[Avatar, int, int], Tuple[float, float]]] = None,
    top_offset: int = 0,
) -> Optional[Avatar]:
    mouse_x, mouse_y = pygame_mod.mouse.get_pos()
    hovered = None
    min_dist = float("inf")
    for avatar_id, avatar in simulator.world.avatar_manager.avatars.items():
        if get_display_center is not None:
            cx_f, cy_f = get_display_center(avatar, tile_size, margin)
            cx, cy = int(cx_f), int(cy_f)
        else:
            cx, cy = avatar_center_pixel(avatar, tile_size, margin)
        cy += top_offset
        avatar_image = avatar_images.get(avatar_id)
        if avatar_image:
            image_rect = avatar_image.get_rect()
            image_x = cx - image_rect.width // 2
            image_y = cy - image_rect.height // 2
            screen.blit(avatar_image, (image_x, image_y))
            if image_rect.collidepoint(mouse_x - image_x, mouse_y - image_y):
                hovered = avatar
                min_dist = 0
        else:
            radius = max(8, tile_size // 3)
            pygame_mod.draw.circle(screen, colors["avatar"], (cx, cy), radius)
            dist = math.hypot(mouse_x - cx, mouse_y - cy)
            if dist <= radius and dist < min_dist:
                hovered = avatar
                min_dist = dist
    return hovered


def draw_tooltip(pygame_mod, screen, colors, lines: List[str], mouse_x: int, mouse_y: int, font, min_width: Optional[int] = None):
    padding = 6
    spacing = 2
    surf_lines = [font.render(t, True, colors["text"]) for t in lines]
    width = max(s.get_width() for s in surf_lines) + padding * 2
    if min_width is not None:
        width = max(width, min_width)
    height = sum(s.get_height() for s in surf_lines) + padding * 2 + spacing * (len(surf_lines) - 1)
    x = mouse_x + 12
    y = mouse_y + 12
    screen_w, screen_h = screen.get_size()
    if x + width > screen_w:
        x = mouse_x - width - 12
    if y + height > screen_h:
        y = mouse_y - height - 12
    # 进一步夹紧，避免位于窗口上边或左边之外
    x = max(0, min(x, screen_w - width))
    top_limit = 0  # 如需避免覆盖状态栏，可改为 STATUS_BAR_HEIGHT
    y = max(top_limit, min(y, screen_h - height))
    bg_rect = pygame_mod.Rect(x, y, width, height)
    pygame_mod.draw.rect(screen, colors["tooltip_bg"], bg_rect, border_radius=6)
    pygame_mod.draw.rect(screen, colors["tooltip_bd"], bg_rect, 1, border_radius=6)
    cursor_y = y + padding
    for s in surf_lines:
        screen.blit(s, (x + padding, cursor_y))
        cursor_y += s.get_height() + spacing


def draw_tooltip_for_avatar(pygame_mod, screen, colors, font, avatar: Avatar):
    lines = [
        f"{avatar.name}",
        f"性别: {avatar.gender}",
        f"年龄: {avatar.age}",
        f"阵营: {avatar.alignment}",
        f"境界: {str(avatar.cultivation_progress)}",
        f"HP: {avatar.hp}",
        f"MP: {avatar.mp}",
        f"灵根: {format_root_cn(avatar.root)}",
        f"功法: {avatar.technique.name}（{avatar.technique.attribute}·{avatar.technique.grade.value}）",
        f"个性: {', '.join([persona.name for persona in avatar.personas])}",
        f"位置: ({avatar.pos_x}, {avatar.pos_y})",
    ]

    lines.append(f"灵石: {str(avatar.magic_stone)}")
    if avatar.items:
        lines.append("物品:")
        for item, quantity in avatar.items.items():
            lines.append(f"  {item.name} x{quantity}")
    else:
        lines.append("")
        lines.append("物品: 无")
    if avatar.thinking:
        lines.append("")
        lines.append("思考:")
        thinking_lines = wrap_text(avatar.thinking, 28)
        lines.extend(thinking_lines)
    if getattr(avatar, "objective", None):
        lines.append("")
        lines.append("目标:")
        objective_lines = wrap_text(avatar.objective, 28)
        lines.extend(objective_lines)

    # 关系信息
    relations_list = [f"{other.name}({str(relation)})" for other, relation in getattr(avatar, "relations", {}).items()]
    lines.append("")
    if relations_list:
        lines.append("关系:")
        for s in relations_list[:6]:
            lines.append(f"  {s}")
    else:
        lines.append("关系: 无")
    draw_tooltip(pygame_mod, screen, colors, lines, *pygame_mod.mouse.get_pos(), font, min_width=260)


def draw_tooltip_for_region(pygame_mod, screen, colors, font, region, mouse_x: int, mouse_y: int):
    if region is None:
        return
    lines = [
        f"区域: {region.name}",
        f"描述: {region.desc}",
    ]
    from src.classes.region import CultivateRegion, NormalRegion
    if isinstance(region, CultivateRegion):
        stars = "★" * region.essence_density + "☆" * (10 - region.essence_density)
        lines.append(f"主要灵气: {region.essence_type} {stars}")
    elif isinstance(region, NormalRegion):
        species_info = region.get_species_info()
        if species_info and species_info != "暂无特色物种":
            lines.append("物种分布:")
            for species in species_info.split("; "):
                lines.append(f"  {species}")
        else:
            lines.append("物种分布: 暂无特色物种")
    draw_tooltip(pygame_mod, screen, colors, lines, mouse_x, mouse_y, font)


def draw_operation_guide(pygame_mod, screen, colors, font, margin: int, auto_step: bool):
    auto_status = "开" if auto_step else "关"
    guide_text = f"A:自动步进({auto_status})  SPACE:单步  ESC:退出"
    guide_surf = font.render(guide_text, True, colors["status_text"])
    x_pos = margin + 8
    screen.blit(guide_surf, (x_pos, 8))
    return guide_surf.get_width()


def draw_year_month_info(pygame_mod, screen, colors, font, margin: int, guide_width: int, world):
    year = int(world.month_stamp.get_year())
    month_num = world.month_stamp.get_month().value
    ym_text = f"{year}年{month_num:02d}月"
    ym_surf = font.render(ym_text, True, colors["status_text"])
    x_pos = margin + guide_width + 8 * 3
    screen.blit(ym_surf, (x_pos, 8))


def draw_status_bar(pygame_mod, screen, colors, font, margin: int, world, auto_step: bool):
    status_y = 8
    status_height = STATUS_BAR_HEIGHT
    status_rect = pygame_mod.Rect(0, 0, screen.get_width(), status_height)
    pygame_mod.draw.rect(screen, colors["status_bg"], status_rect)
    pygame_mod.draw.line(screen, colors["status_border"],
                        (0, status_height), (screen.get_width(), status_height), 2)
    guide_w = draw_operation_guide(pygame_mod, screen, colors, font, margin, auto_step)
    draw_year_month_info(pygame_mod, screen, colors, font, margin, guide_w, world)


__all__ = [
    "draw_map",
    "draw_region_labels",
    "draw_avatars_and_pick_hover",
    "draw_tooltip_for_avatar",
    "draw_tooltip_for_region",
    "draw_status_bar",
    "STATUS_BAR_HEIGHT",
]


