import math
from typing import List, Optional, Tuple, Callable
from src.classes.avatar import Avatar
from src.utils.text_wrap import wrap_text


def wrap_lines_for_tooltip(lines: List[str], max_chars_per_line: int = 28) -> List[str]:
    """
    将一组 tooltip 行进行字符级换行：
    - 对形如 "前缀: 内容" 的行，仅对内容部分换行，并在续行添加两个空格缩进
    - 其他行超过宽度则直接按宽度切分
    """
    wrapped: List[str] = []
    for line in lines:
        # 仅处理简单前缀（到第一个": "为界）
        split_idx = line.find(": ")
        if split_idx != -1:
            prefix = line[: split_idx + 2]
            content = line[split_idx + 2 :]
            segs = wrap_text(content, max_chars_per_line)
            if segs:
                wrapped.append(prefix + segs[0])
                for seg in segs[1:]:
                    wrapped.append("  " + seg)
            else:
                wrapped.append(line)
            continue
        # 无前缀情形：必要时整行切分
        if len(line) > max_chars_per_line:
            wrapped.extend(wrap_text(line, max_chars_per_line))
        else:
            wrapped.append(line)
    return wrapped



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


def draw_sect_headquarters(pygame_mod, screen, world, sect_images: dict, ts: int, m: int, top_offset: int = 0):
    """
    在底图绘制完成后叠加绘制宗门总部（2x2 tile）。
    以区域左上角（north_west_cor）为锚点绘制。
    """
    for region in world.map.regions.values():
        if getattr(region, "get_region_type", lambda: "")() != "sect":
            continue
        img_path: str | None = getattr(region, "image_path", None)
        if not img_path:
            # 可回退到按名称找图：期望 assets/sects/{region.name}.png
            key = str(getattr(region, "name", ""))
            image = sect_images.get(key)
        else:
            key = str(pygame_mod.Path(img_path).stem) if hasattr(pygame_mod, "Path") else img_path.split("/")[-1].split("\\")[-1].split(".")[0]
            image = sect_images.get(key)
        if not image:
            # 未加载到图片则跳过
            continue
        try:
            nw = tuple(map(int, str(getattr(region, "north_west_cor", "0,0")).split(",")))
        except Exception:
            continue
        x_px = m + nw[0] * ts
        y_px = m + top_offset + nw[1] * ts
        screen.blit(image, (x_px, y_px))


def _is_small_square_region(region) -> int:
    """
    若为 2x2 或 3x3 的矩形/正方形区域，返回边长（2或3）；否则返回0。
    """
    try:
        nw = tuple(map(int, str(getattr(region, "north_west_cor", "0,0")).split(",")))
        se = tuple(map(int, str(getattr(region, "south_east_cor", "0,0")).split(",")))
    except Exception:
        return 0
    if getattr(region, "shape", None) is None:
        return 0
    shape_name = getattr(region.shape, "name", "")
    if shape_name not in ("RECTANGLE", "SQUARE"):
        return 0
    width = se[0] - nw[0] + 1
    height = se[1] - nw[1] + 1
    if width == height and width in (2, 3):
        return width
    return 0


def draw_small_regions(pygame_mod, screen, world, region_images: dict, tile_images: dict, ts: int, m: int, top_offset: int = 0, tile_originals: Optional[dict] = None):
    """
    使用整图绘制 2x2 / 3x3 的小区域：
    - 优先按名称从 region_images 中取 n×n 的整图（n 为 2 或 3）
    - 若没有整图，则将现有 tile 图裁切/合成为一张，避免重复边框
    """
    for region in world.map.regions.values():
        n = _is_small_square_region(region)
        if n == 0:
            continue
        # 仅对 2x2 生效；3x3 不覆盖（保持每格一张图）
        if n != 2:
            continue
        try:
            nw = tuple(map(int, str(getattr(region, "north_west_cor", "0,0")).split(",")))
        except Exception:
            continue
        x_px = m + nw[0] * ts
        y_px = m + top_offset + nw[1] * ts
        name_key = str(getattr(region, "name", ""))
        variants = region_images.get(name_key)
        if variants and variants.get(n):
            screen.blit(variants[n], (x_px, y_px))
            continue
        # 回退：从原始 tile 贴图一次性缩放到 n×n，避免“先缩1×1再放大”的二次缩放
        try:
            tile = world.map.get_tile(nw[0], nw[1])
            base_image = None
            if tile_originals is not None:
                base_image = tile_originals.get(tile.type)
            if base_image is None:
                base_image = tile_images.get(tile.type)
        except Exception:
            base_image = None
        if base_image is not None:
            scaled = pygame_mod.transform.scale(base_image, (ts * n, ts * n))
            screen.blit(scaled, (x_px, y_px))
        else:
            # 最后兜底：淡色块
            tmp = pygame_mod.Surface((ts * n, ts * n), pygame_mod.SRCALPHA)
            tmp.fill((255, 255, 255, 24))
            screen.blit(tmp, (x_px, y_px))


def calculate_font_size_by_area(tile_size: int, area: int) -> int:
    base = int(tile_size * 1.1)
    growth = int(max(0, min(24, (area ** 0.5))))
    size = base + growth - 7  # 再降低2个字号
    return max(16, min(40, size))


def draw_region_labels(pygame_mod, screen, colors, world, get_region_font, tile_size: int, margin: int, top_offset: int = 0, outline_px: int = 2):
    ts = tile_size
    m = margin
    mouse_x, mouse_y = pygame_mod.mouse.get_pos()
    hovered_region = None

    # 以区域面积降序放置，优先保证大区域标签可读性
    regions = sorted(list(world.map.regions.values()), key=lambda r: getattr(r, "area", 0), reverse=True)

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
        # 小区域（面积<=9，例如2x2/3x3）标签放在底部；大区域放在中心
        use_bottom = getattr(region, "area", 0) <= 9
        if use_bottom and getattr(region, "cors", None):
            bottom_y = max(y for _, y in region.cors)
            xs_on_bottom = [x for x, y in region.cors if y == bottom_y]
            if xs_on_bottom:
                left_x = min(xs_on_bottom)
                right_x = max(xs_on_bottom)
                anchor_cx_tile = (left_x + right_x) / 2.0
            else:
                anchor_cx_tile = float(region.center_loc[0])
            screen_cx = int(m + anchor_cx_tile * ts + ts // 2)
            screen_cy = int(m + top_offset + (bottom_y + 1) * ts + 2)
        else:
            # 居中放置
            screen_cx = int(m + float(region.center_loc[0]) * ts + ts // 2)
            screen_cy = int(m + top_offset + float(region.center_loc[1]) * ts)
        font_size = calculate_font_size_by_area(tile_size, region.area)
        region_font = get_region_font(font_size)
        text_surface = region_font.render(str(name), True, colors["text"])
        border_surface = region_font.render(str(name), True, colors.get("text_border", (24, 24, 24)))
        text_w = text_surface.get_width()
        text_h = text_surface.get_height()

        # 候选偏移：优先“区域下方”，若越界或冲突，再尝试左右位移、其上方
        pad = 6
        dxw = max(8, int(0.6 * text_w)) + pad
        dyh = text_h + pad
        candidates = [
            (0, 0),              # 正下方（期望位置）
            (-dxw, 0), (dxw, 0), # 下方左右
            (0, -dyh),           # 底边上方一行
            (-dxw, -dyh), (dxw, -dyh),
            (0, -2 * dyh),       # 再上方，尽量避免覆盖区域
        ]

        chosen_rect = None
        for (dx, dy) in candidates:
            # 以锚点为基准，文本顶部左上角坐标
            x_try = int(screen_cx + dx - text_w / 2)
            y_try = int(screen_cy + dy)
            x_try, y_try = _clamp_rect(x_try, y_try, text_w, text_h)
            rect_try = pygame_mod.Rect(x_try, y_try, text_w, text_h)
            if not any(rect_try.colliderect(r) for r in placed_rects):
                chosen_rect = rect_try
                break
        if chosen_rect is None:
            # 如果所有候选均冲突，就退回锚点正下方
            x0 = int(screen_cx - text_w / 2)
            y0 = int(screen_cy)
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
    name_font: Optional[object] = None,
    highlight_avatar_id: Optional[str] = None,
) -> Tuple[Optional[Avatar], List[Avatar]]:
    mouse_x, mouse_y = pygame_mod.mouse.get_pos()
    candidates_with_dist: List[Tuple[float, Avatar]] = []
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
            # 名字（置于头像下方居中）
            if name_font is not None:
                _draw_avatar_name_label(
                    pygame_mod,
                    screen,
                    colors,
                    name_font,
                    str(getattr(avatar, "name", "")),
                    is_highlight=bool(highlight_avatar_id and avatar.id == highlight_avatar_id),
                    anchor_x=image_x + image_rect.width // 2,
                    anchor_y=image_y + image_rect.height + 2,
                )
            if image_rect.collidepoint(mouse_x - image_x, mouse_y - image_y):
                dist = math.hypot(mouse_x - cx, mouse_y - cy)
                candidates_with_dist.append((dist, avatar))
        else:
            radius = max(8, tile_size // 3)
            pygame_mod.draw.circle(screen, colors["avatar"], (cx, cy), radius)
            # 名字（置于圆形下方居中）
            if name_font is not None:
                _draw_avatar_name_label(
                    pygame_mod,
                    screen,
                    colors,
                    name_font,
                    str(getattr(avatar, "name", "")),
                    is_highlight=bool(highlight_avatar_id and avatar.id == highlight_avatar_id),
                    anchor_x=cx,
                    anchor_y=int(cy + radius + 2),
                )
            dist = math.hypot(mouse_x - cx, mouse_y - cy)
            if dist <= radius:
                candidates_with_dist.append((dist, avatar))
    candidates_with_dist.sort(key=lambda t: t[0])
    hovered = candidates_with_dist[0][1] if candidates_with_dist else None
    candidate_avatars: List[Avatar] = [a for _, a in candidates_with_dist]
    return hovered, candidate_avatars


def draw_tooltip(pygame_mod, screen, colors, lines: List[str], mouse_x: int, mouse_y: int, font, min_width: int = 260, top_limit: int = 0):
    padding = 6
    spacing = 2
    surf_lines = [font.render(t, True, colors["text"]) for t in lines]
    width = max(s.get_width() for s in surf_lines) + padding * 2
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
    y = max(top_limit, min(y, screen_h - height))
    bg_rect = pygame_mod.Rect(x, y, width, height)
    pygame_mod.draw.rect(screen, colors["tooltip_bg"], bg_rect, border_radius=6)
    pygame_mod.draw.rect(screen, colors["tooltip_bd"], bg_rect, 1, border_radius=6)
    cursor_y = y + padding
    for s in surf_lines:
        screen.blit(s, (x + padding, cursor_y))
        cursor_y += s.get_height() + spacing


def draw_tooltip_for_avatar(pygame_mod, screen, colors, font, avatar: Avatar, tooltip_min_width: int = 260, status_bar_height: int = 32):
    # 改为从 Avatar.get_hover_info 获取信息行，避免前端重复拼接
    lines = avatar.get_hover_info()
    draw_tooltip(pygame_mod, screen, colors, lines, *pygame_mod.mouse.get_pos(), font, min_width=tooltip_min_width, top_limit=status_bar_height)


def draw_tooltip_for_region(pygame_mod, screen, colors, font, region, mouse_x: int, mouse_y: int, tooltip_min_width: int = 260, status_bar_height: int = 32):
    if region is None:
        return
    # 改为调用 region.get_hover_info()，并统一用 wrap_lines_for_tooltip 进行换行
    lines = region.get_hover_info()
    wrapped_lines = wrap_lines_for_tooltip(lines, 28)
    draw_tooltip(pygame_mod, screen, colors, wrapped_lines, mouse_x, mouse_y, font, min_width=tooltip_min_width, top_limit=status_bar_height)


def draw_operation_guide(pygame_mod, screen, colors, font, margin: int):
    guide_text = "ESC: 呼出菜单"
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


def draw_status_bar(pygame_mod, screen, colors, font, margin: int, world, status_bar_height: int = 32):
    status_y = 8
    status_rect = pygame_mod.Rect(0, 0, screen.get_width(), status_bar_height)
    pygame_mod.draw.rect(screen, colors["status_bg"], status_rect)
    pygame_mod.draw.line(screen, colors["status_border"],
                        (0, status_bar_height), (screen.get_width(), status_bar_height), 2)
    guide_w = draw_operation_guide(pygame_mod, screen, colors, font, margin)
    draw_year_month_info(pygame_mod, screen, colors, font, margin, guide_w, world)


__all__ = [
    "draw_map",
    "draw_region_labels",
    "draw_avatars_and_pick_hover",
    "draw_tooltip_for_avatar",
    "draw_tooltip_for_region",
    "draw_status_bar",
    "map_pixel_size",
    "draw_hover_badge",
    "draw_small_regions",
    "draw_sect_headquarters",
]


def draw_hover_badge(pygame_mod, screen, colors, font, center_x: int, center_y: int, index: int, total: int, top_offset: int = 0):
    """
    在给定中心附近绘制一个小徽标，显示 index/total（索引从1开始）。
    徽标默认放在头像上方偏右位置。
    """
    label = f"{index}/{total}"
    surf = font.render(label, True, colors["text"])
    pad_x = 6
    pad_y = 2
    w = surf.get_width() + pad_x * 2
    h = surf.get_height() + pad_y * 2
    # 徽标位置：头像中心的右上角
    x = int(center_x + 10)
    y = int(center_y + top_offset - 24 - h)
    rect = pygame_mod.Rect(x, y, w, h)
    # 半透明背景与描边
    bg = pygame_mod.Surface((w, h), pygame_mod.SRCALPHA)
    bg.fill((20, 20, 20, 180))
    screen.blit(bg, (rect.x, rect.y))
    pygame_mod.draw.rect(screen, colors.get("tooltip_bd", (90, 90, 90)), rect, 1, border_radius=6)
    # 文本
    screen.blit(surf, (rect.x + pad_x, rect.y + pad_y))


def _draw_avatar_name_label(pygame_mod, screen, colors, font, name_text: str, *, is_highlight: bool, anchor_x: int, anchor_y: int) -> None:
    if not name_text:
        return
    text_color = (236, 236, 236) if is_highlight else colors["text"]
    text_surf = font.render(name_text, True, text_color)
    tx = int(anchor_x - text_surf.get_width() / 2)
    ty = int(anchor_y)
    if is_highlight:
        pad_x = 6
        pad_y = 2
        w = text_surf.get_width() + pad_x * 2
        h = text_surf.get_height() + pad_y * 2
        bg = pygame_mod.Surface((w, h), pygame_mod.SRCALPHA)
        bg.fill((0, 0, 0, 210))
        screen.blit(bg, (tx - pad_x, ty - pad_y))
        rect = pygame_mod.Rect(tx - pad_x, ty - pad_y, w, h)
        pygame_mod.draw.rect(screen, colors.get("tooltip_bd", (90, 90, 90)), rect, 1, border_radius=6)
        # 高亮时直接白字绘制（背景已提供对比）
        screen.blit(text_surf, (tx, ty))
        return
    # 非高亮：加1px 阴影提升可读性（不加底板）
    shadow = font.render(name_text, True, colors.get("text_border", (24, 24, 24)))
    screen.blit(shadow, (tx + 1, ty + 1))
    screen.blit(text_surf, (tx, ty))


def map_pixel_size(world_or_map, tile_size: int) -> Tuple[int, int]:
    """
    计算地图像素宽高（不含 margin 与顶部偏移）。
    支持传入 world（含 .map）或 map 对象（含 .width/.height）。
    """
    map_obj = getattr(world_or_map, "map", world_or_map)
    return map_obj.width * tile_size, map_obj.height * tile_size
