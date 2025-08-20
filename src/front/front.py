import math
from typing import Dict, List, Optional, Tuple

# Front 只依赖项目内部类型定义与 pygame
from src.sim.simulator import Simulator
from src.classes.world import World
from src.classes.tile import TileType
from src.classes.avatar import Avatar, Gender


class Front:
    """
    基于 pygame 的前端展示。

    - 渲染地图 `World.map` 与其中的 `Avatar`
    - 以固定节奏调用 `simulator.step()`，画面随之更新
    - 鼠标悬停在 avatar 上时显示信息

    按键：
    - A：切换自动步进（默认开启）
    - 空格：手动执行一步（在自动关闭时有用）
    - ESC / 关闭窗口：退出
    """

    def __init__(
        self,
        world: World,
        simulator: Simulator,
        *,
        tile_size: int = 32,
        margin: int = 8,
        step_interval_ms: int = 400,
        window_title: str = "Cultivation World Simulator",
        font_path: Optional[str] = None,
    ):
        self.world = world
        self.simulator = simulator
        self.tile_size = tile_size
        self.margin = margin
        self.step_interval_ms = step_interval_ms
        self.window_title = window_title
        self.font_path = font_path

        # 运行时状态
        self._auto_step = True
        self._last_step_ms = 0

        # 延迟导入 pygame：避免未安装 pygame 时影响非可视化运行/测试
        import pygame  # type: ignore

        self.pygame = pygame
        pygame.init()
        pygame.font.init()

        # 计算窗口大小
        width_px = world.map.width * tile_size + margin * 2
        height_px = world.map.height * tile_size + margin * 2
        self.screen = pygame.display.set_mode((width_px, height_px))
        pygame.display.set_caption(window_title)

        # 字体（优先中文友好字体；可显式传入 TTF 路径）
        self.font = self._create_font(16)
        self.tooltip_font = self._create_font(14)
        # 区域名字体缓存：按需动态放大（随区域面积和格子大小自适应）
        self._region_font_cache: Dict[int, object] = {}

        # 配色
        self.colors: Dict[str, Tuple[int, int, int]] = {
            "bg": (18, 18, 18),
            "grid": (40, 40, 40),
            "text": (230, 230, 230),
            "tooltip_bg": (32, 32, 32),
            "tooltip_bd": (90, 90, 90),
            "avatar": (240, 220, 90),
        }

        self.tile_colors: Dict[TileType, Tuple[int, int, int]] = {
            TileType.PLAIN: (64, 120, 64),
            TileType.FOREST: (24, 96, 48),
            TileType.MOUNTAIN: (108, 108, 108),
            TileType.WATER: (60, 120, 180),
            TileType.SEA: (30, 90, 150),
            TileType.CITY: (140, 120, 90),
            TileType.DESERT: (210, 180, 60),
            TileType.RAINFOREST: (12, 80, 36),
            TileType.GLACIER: (210, 230, 240),
            TileType.SNOW_MOUNTAIN: (200, 200, 200),
            TileType.VOLCANO: (180, 40, 40),  # 火山红色
        }

        self.clock = pygame.time.Clock()

    # --------------------------- 主循环 ---------------------------
    def run(self):
        pygame = self.pygame
        running = True
        while running:
            dt_ms = self.clock.tick(60)
            self._last_step_ms += dt_ms

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE,):
                        running = False
                    elif event.key == pygame.K_a:
                        self._auto_step = not self._auto_step
                    elif event.key == pygame.K_SPACE:
                        self._step_once()

            if self._auto_step and self._last_step_ms >= self.step_interval_ms:
                self._step_once()

            self._render()

        pygame.quit()

    def _step_once(self):
        self.simulator.step()
        self._last_step_ms = 0

    # --------------------------- 渲染 ---------------------------
    def _render(self):
        pygame = self.pygame
        self.screen.fill(self.colors["bg"])

        self._draw_map()
        hovered_region = self._draw_region_labels()
        hovered_avatar = self._draw_avatars_and_pick_hover()
        
        # 优先显示region tooltip，如果没有region tooltip才显示avatar tooltip
        if hovered_region is not None:
            mouse_x, mouse_y = self.pygame.mouse.get_pos()
            self._draw_tooltip_for_region(hovered_region, mouse_x, mouse_y)
        elif hovered_avatar is not None:
            self._draw_tooltip_for_avatar(hovered_avatar)

        # 状态条
        hint = f"A:自动步进({'开' if self._auto_step else '关'})  SPACE:单步  ESC:退出"
        text_surf = self.font.render(hint, True, self.colors["text"])
        self.screen.blit(text_surf, (self.margin, 4))

        # 年月（右上角显示：YYYY年MM月）
        try:
            month_num = list(type(self.simulator.month)).index(self.simulator.month) + 1
        except Exception:
            month_num = 1
        ym_text = f"{int(self.simulator.year)}年{month_num:02d}月"
        ym_surf = self.font.render(ym_text, True, self.colors["text"])
        screen_w, _ = self.screen.get_size()
        self.screen.blit(ym_surf, (screen_w - self.margin - ym_surf.get_width(), 4))

        pygame.display.flip()

    def _draw_map(self):
        pygame = self.pygame
        map_obj = self.world.map
        ts = self.tile_size
        m = self.margin

        # 先画网格背景块
        for y in range(map_obj.height):
            for x in range(map_obj.width):
                tile = map_obj.get_tile(x, y)
                color = self.tile_colors.get(tile.type, (80, 80, 80))
                rect = pygame.Rect(m + x * ts, m + y * ts, ts, ts)
                pygame.draw.rect(self.screen, color, rect)

        # 画网格线
        grid_color = self.colors["grid"]
        for gx in range(map_obj.width + 1):
            start_pos = (m + gx * ts, m)
            end_pos = (m + gx * ts, m + map_obj.height * ts)
            pygame.draw.line(self.screen, grid_color, start_pos, end_pos, 1)
        for gy in range(map_obj.height + 1):
            start_pos = (m, m + gy * ts)
            end_pos = (m + map_obj.width * ts, m + gy * ts)
            pygame.draw.line(self.screen, grid_color, start_pos, end_pos, 1)

    def _draw_region_labels(self):
        pygame = self.pygame
        map_obj = self.world.map
        ts = self.tile_size
        m = self.margin
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # 聚合每个 region 的所有地块中心点：Region 以自身 id 为哈希键
        region_to_points: Dict[object, List[Tuple[int, int]]] = {}
        # 直接遍历底层 tiles 字典更高效
        for (x, y), tile in getattr(map_obj, "tiles", {}).items():
            if getattr(tile, "region", None) is None:
                continue
            region_obj = tile.region
            cx = m + x * ts + ts // 2
            cy = m + y * ts + ts // 2
            region_to_points.setdefault(region_obj, []).append((cx, cy))

        if not region_to_points:
            return

        hovered_region = None
        for region, points in region_to_points.items():
            if not points:
                continue
            # 计算质心
            avg_x = sum(p[0] for p in points) // len(points)
            avg_y = sum(p[1] for p in points) // len(points)

            name = getattr(region, "name", None)
            if not name:
                continue

            # 按区域大小与格子尺寸决定字体大小
            area = len(points)
            base = int(self.tile_size * 1.1)
            growth = int(max(0, min(24, (area ** 0.5))))
            font_size = max(16, min(40, base + growth))
            region_font = self._get_region_font(font_size)

            # 渲染带轻微阴影的文字
            text_surface = region_font.render(str(name), True, self.colors["text"])  # 主文字
            shadow_surface = region_font.render(str(name), True, (0, 0, 0))  # 阴影

            text_w = text_surface.get_width()
            text_h = text_surface.get_height()
            x = int(avg_x - text_w / 2)
            y = int(avg_y - text_h / 2)

            # 检测鼠标悬停
            if (x <= mouse_x <= x + text_w and y <= mouse_y <= y + text_h):
                hovered_region = region

            # 先画阴影，略微偏移
            self.screen.blit(shadow_surface, (x + 1, y + 1))
            # 再画主文字
            self.screen.blit(text_surface, (x, y))

        # 返回悬停的region
        return hovered_region

    def _get_region_font(self, size: int):
        # 缓存不同大小的字体，避免每帧重复创建
        f = self._region_font_cache.get(size)
        if f is None:
            f = self._create_font(size)
            self._region_font_cache[size] = f
        return f

    def _draw_avatars_and_pick_hover(self) -> Optional[Avatar]:
        pygame = self.pygame
        mouse_x, mouse_y = pygame.mouse.get_pos()

        hovered: Optional[Avatar] = None
        min_dist = float("inf")

        for avatar in self.simulator.avatars:
            cx, cy = self._avatar_center_pixel(avatar)
            radius = max(8, self.tile_size // 3)
            pygame.draw.circle(self.screen, self.colors["avatar"], (cx, cy), radius)

            # 简单的 hover：鼠标与圆心距离
            dist = math.hypot(mouse_x - cx, mouse_y - cy)
            if dist <= radius and dist < min_dist:
                hovered = avatar
                min_dist = dist

        return hovered

    # --------------------------- 工具/辅助 ---------------------------
    def _avatar_center_pixel(self, avatar: Avatar) -> Tuple[int, int]:
        ts = self.tile_size
        m = self.margin
        px = m + avatar.pos_x * ts + ts // 2
        py = m + avatar.pos_y * ts + ts // 2
        return px, py

    def _avatar_tooltip_lines(self, avatar: Avatar) -> List[str]:
        gender = str(avatar.gender)

        pos = f"({avatar.pos_x}, {avatar.pos_y})"
        lines = [
            f"{avatar.name}#{avatar.id}",
            f"性别: {gender}",
            f"年龄: {avatar.age}",
            f"位置: {pos}",
        ]
        return lines

    def _region_tooltip_lines(self, region) -> List[str]:
        lines = [
            f"区域: {region.name}",
            f"描述: {region.description}",
        ]
        
        # 添加灵气信息
        if hasattr(region, 'essence') and region.essence:
            # 按密度排序，显示最重要的灵气
            essence_items = []
            for essence_type, density in region.essence.density.items():
                if density > 0:
                    essence_name = str(essence_type) 
                    essence_items.append((density, essence_name))
            
            if essence_items:
                # 按密度降序排序
                essence_items.sort(reverse=True)
                lines.append("灵气分布:")
                for density, name in essence_items:
                    # 用星号表示密度等级
                    stars = "★" * density + "☆" * (10 - density)
                    lines.append(f"  {name}: {stars}")
        
        return lines

    def _draw_tooltip_for_avatar(self, avatar: Avatar):
        pygame = self.pygame
        lines = self._avatar_tooltip_lines(avatar)

        # 计算尺寸
        padding = 6
        spacing = 2
        surf_lines = [self.tooltip_font.render(t, True, self.colors["text"]) for t in lines]
        width = max(s.get_width() for s in surf_lines) + padding * 2
        height = sum(s.get_height() for s in surf_lines) + padding * 2 + spacing * (len(surf_lines) - 1)

        mx, my = pygame.mouse.get_pos()
        x = mx + 12
        y = my + 12

        # 边界修正：尽量不出屏幕
        screen_w, screen_h = self.screen.get_size()
        if x + width > screen_w:
            x = mx - width - 12
        if y + height > screen_h:
            y = my - height - 12

        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, self.colors["tooltip_bg"], bg_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.colors["tooltip_bd"], bg_rect, 1, border_radius=6)

        # 绘制文字
        cursor_y = y + padding
        for s in surf_lines:
            self.screen.blit(s, (x + padding, cursor_y))
            cursor_y += s.get_height() + spacing

    def _draw_tooltip_for_region(self, region, mouse_x: int, mouse_y: int):
        pygame = self.pygame
        lines = self._region_tooltip_lines(region)

        # 计算尺寸
        padding = 6
        spacing = 2
        surf_lines = [self.tooltip_font.render(t, True, self.colors["text"]) for t in lines]
        width = max(s.get_width() for s in surf_lines) + padding * 2
        height = sum(s.get_height() for s in surf_lines) + padding * 2 + spacing * (len(surf_lines) - 1)

        x = mouse_x + 12
        y = mouse_y + 12

        # 边界修正：尽量不出屏幕
        screen_w, screen_h = self.screen.get_size()
        if x + width > screen_w:
            x = mouse_x - width - 12
        if y + height > screen_h:
            y = mouse_y - height - 12

        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, self.colors["tooltip_bg"], bg_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.colors["tooltip_bd"], bg_rect, 1, border_radius=6)

        # 绘制文字
        cursor_y = y + padding
        for s in surf_lines:
            self.screen.blit(s, (x + padding, cursor_y))
            cursor_y += s.get_height() + spacing


    def _create_font(self, size: int):
        pygame = self.pygame
        if self.font_path:
            try:
                return pygame.font.Font(self.font_path, size)
            except Exception:
                # 回退到自动匹配
                pass
        return self._load_font_with_fallback(size)

    def _load_font_with_fallback(self, size: int):
        """
        在不同平台上尝试加载常见等宽或中文字体，避免中文渲染为方块。
        """
        pygame = self.pygame
        candidates = [
            # Windows 常见中文字体
            "Microsoft YaHei UI",
            "Microsoft YaHei",
            "SimHei",
            "SimSun",
            # 常见等宽/通用字体
            "Consolas",
            "DejaVu Sans",
            "DejaVu Sans Mono",
            "Arial Unicode MS",
            "Noto Sans CJK SC",
            "Noto Sans CJK",
        ]

        for name in candidates:
            try:
                f = pygame.font.SysFont(name, size)
                # 简单验证一下是否能渲染中文（有些字体返回成功但渲染为空）
                test = f.render("测试中文AaBb123", True, (255, 255, 255))
                if test.get_width() > 0:
                    return f
            except Exception:
                pass

        # 退回默认字体
        return pygame.font.SysFont(None, size)


__all__ = ["Front"]


