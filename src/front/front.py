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
    
    功能：
    - 渲染地图与Avatar
    - 自动/手动步进模拟
    - 鼠标悬停显示信息
    
    按键：
    - A：切换自动步进
    - 空格：手动执行一步
    - ESC：退出
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

        # 初始化pygame
        import pygame
        self.pygame = pygame
        pygame.init()
        pygame.font.init()

        # 计算窗口大小
        width_px = world.map.width * tile_size + margin * 2
        height_px = world.map.height * tile_size + margin * 2
        self.screen = pygame.display.set_mode((width_px, height_px))
        pygame.display.set_caption(window_title)

        # 字体和缓存
        self.font = self._create_font(16)
        self.tooltip_font = self._create_font(14)
        self._region_font_cache: Dict[int, object] = {}

        # 配色方案
        self.colors = {
            "bg": (18, 18, 18),
            "grid": (40, 40, 40),
            "text": (230, 230, 230),
            "tooltip_bg": (32, 32, 32),
            "tooltip_bd": (90, 90, 90),
            "avatar": (240, 220, 90),
        }

        # 加载tile图像
        self.tile_images = {}
        self._load_tile_images()

        self.clock = pygame.time.Clock()

    def run(self):
        """主循环"""
        pygame = self.pygame
        running = True
        
        while running:
            dt_ms = self.clock.tick(60)
            self._last_step_ms += dt_ms

            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_a:
                        self._auto_step = not self._auto_step
                    elif event.key == pygame.K_SPACE:
                        self._step_once()

            # 自动步进
            if self._auto_step and self._last_step_ms >= self.step_interval_ms:
                self._step_once()

            self._render()

        pygame.quit()

    def _step_once(self):
        """执行一步模拟"""
        self.simulator.step()
        self._last_step_ms = 0

    def _render(self):
        """渲染主画面"""
        pygame = self.pygame
        
        # 清屏
        self.screen.fill(self.colors["bg"])

        # 绘制地图和标签
        self._draw_map()
        hovered_region = self._draw_region_labels()
        hovered_avatar = self._draw_avatars_and_pick_hover()
        
        # 显示tooltip
        if hovered_region is not None:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self._draw_tooltip_for_region(hovered_region, mouse_x, mouse_y)
        elif hovered_avatar is not None:
            self._draw_tooltip_for_avatar(hovered_avatar)

        # 状态信息
        self._draw_status_bar()
        self._draw_date_info()

        pygame.display.flip()

    def _draw_status_bar(self):
        """绘制状态栏"""
        hint = f"A:自动步进({'开' if self._auto_step else '关'})  SPACE:单步  ESC:退出"
        text_surf = self.font.render(hint, True, self.colors["text"])
        self.screen.blit(text_surf, (self.margin, 4))

    def _draw_date_info(self):
        """绘制日期信息"""
        try:
            month_num = list(type(self.simulator.month)).index(self.simulator.month) + 1
        except Exception:
            month_num = 1
            
        ym_text = f"{int(self.simulator.year)}年{month_num:02d}月"
        ym_surf = self.font.render(ym_text, True, self.colors["text"])
        screen_w, _ = self.screen.get_size()
        self.screen.blit(ym_surf, (screen_w - self.margin - ym_surf.get_width(), 4))

    def _draw_map(self):
        """绘制地图"""
        pygame = self.pygame
        map_obj = self.world.map
        ts = self.tile_size
        m = self.margin

        # 绘制tile图像
        for y in range(map_obj.height):
            for x in range(map_obj.width):
                tile = map_obj.get_tile(x, y)
                tile_image = self.tile_images.get(tile.type)
                
                if tile_image:
                    pos = (m + x * ts, m + y * ts)
                    self.screen.blit(tile_image, pos)
                else:
                    # 默认颜色块
                    color = (80, 80, 80)
                    rect = pygame.Rect(m + x * ts, m + y * ts, ts, ts)
                    pygame.draw.rect(self.screen, color, rect)

        # 绘制网格线
        self._draw_grid(map_obj, ts, m)

    def _draw_grid(self, map_obj, ts, m):
        """绘制网格线"""
        pygame = self.pygame
        grid_color = self.colors["grid"]
        
        # 垂直线
        for gx in range(map_obj.width + 1):
            start_pos = (m + gx * ts, m)
            end_pos = (m + gx * ts, m + map_obj.height * ts)
            pygame.draw.line(self.screen, grid_color, start_pos, end_pos, 1)
        
        # 水平线
        for gy in range(map_obj.height + 1):
            start_pos = (m, m + gy * ts)
            end_pos = (m + map_obj.width * ts, m + gy * ts)
            pygame.draw.line(self.screen, grid_color, start_pos, end_pos, 1)

    def _draw_region_labels(self):
        """绘制区域标签"""
        pygame = self.pygame
        map_obj = self.world.map
        ts = self.tile_size
        m = self.margin
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # 收集每个region的所有地块中心点
        region_to_points = self._collect_region_points(map_obj, ts, m)
        
        if not region_to_points:
            return None

        # 绘制每个region的标签
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

            # 计算字体大小
            font_size = self._calculate_font_size(len(points))
            region_font = self._get_region_font(font_size)

            # 渲染文字
            text_surface = region_font.render(str(name), True, self.colors["text"])
            shadow_surface = region_font.render(str(name), True, (0, 0, 0))

            # 计算位置
            text_w = text_surface.get_width()
            text_h = text_surface.get_height()
            x = int(avg_x - text_w / 2)
            y = int(avg_y - text_h / 2)

            # 检测鼠标悬停
            if (x <= mouse_x <= x + text_w and y <= mouse_y <= y + text_h):
                hovered_region = region

            # 绘制文字（先阴影后主文字）
            self.screen.blit(shadow_surface, (x + 1, y + 1))
            self.screen.blit(text_surface, (x, y))

        return hovered_region

    def _collect_region_points(self, map_obj, ts, m):
        """收集region的点位信息"""
        region_to_points = {}
        
        for (x, y), tile in getattr(map_obj, "tiles", {}).items():
            if getattr(tile, "region", None) is None:
                continue
                
            region_obj = tile.region
            cx = m + x * ts + ts // 2
            cy = m + y * ts + ts // 2
            region_to_points.setdefault(region_obj, []).append((cx, cy))
            
        return region_to_points

    def _calculate_font_size(self, area):
        """根据区域大小计算字体大小"""
        base = int(self.tile_size * 1.1)
        growth = int(max(0, min(24, (area ** 0.5))))
        return max(16, min(40, base + growth))

    def _get_region_font(self, size: int):
        """获取指定大小的字体（带缓存）"""
        if size not in self._region_font_cache:
            self._region_font_cache[size] = self._create_font(size)
        return self._region_font_cache[size]

    def _draw_avatars_and_pick_hover(self) -> Optional[Avatar]:
        """绘制Avatar并检测悬停"""
        pygame = self.pygame
        mouse_x, mouse_y = pygame.mouse.get_pos()

        hovered = None
        min_dist = float("inf")

        for avatar in self.simulator.avatars:
            cx, cy = self._avatar_center_pixel(avatar)
            radius = max(8, self.tile_size // 3)
            
            # 绘制Avatar
            pygame.draw.circle(self.screen, self.colors["avatar"], (cx, cy), radius)

            # 检测悬停
            dist = math.hypot(mouse_x - cx, mouse_y - cy)
            if dist <= radius and dist < min_dist:
                hovered = avatar
                min_dist = dist

        return hovered

    def _avatar_center_pixel(self, avatar: Avatar) -> Tuple[int, int]:
        """计算Avatar的像素中心位置"""
        ts = self.tile_size
        m = self.margin
        px = m + avatar.pos_x * ts + ts // 2
        py = m + avatar.pos_y * ts + ts // 2
        return px, py

    def _draw_tooltip(self, lines: List[str], mouse_x: int, mouse_y: int, font):
        """绘制通用tooltip"""
        pygame = self.pygame
        
        # 计算尺寸
        padding = 6
        spacing = 2
        surf_lines = [font.render(t, True, self.colors["text"]) for t in lines]
        width = max(s.get_width() for s in surf_lines) + padding * 2
        height = sum(s.get_height() for s in surf_lines) + padding * 2 + spacing * (len(surf_lines) - 1)

        # 计算位置
        x = mouse_x + 12
        y = mouse_y + 12

        # 边界修正
        screen_w, screen_h = self.screen.get_size()
        if x + width > screen_w:
            x = mouse_x - width - 12
        if y + height > screen_h:
            y = mouse_y - height - 12

        # 绘制背景
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, self.colors["tooltip_bg"], bg_rect, border_radius=6)
        pygame.draw.rect(self.screen, self.colors["tooltip_bd"], bg_rect, 1, border_radius=6)

        # 绘制文字
        cursor_y = y + padding
        for s in surf_lines:
            self.screen.blit(s, (x + padding, cursor_y))
            cursor_y += s.get_height() + spacing

    def _draw_tooltip_for_avatar(self, avatar: Avatar):
        """绘制Avatar的tooltip"""
        lines = [
            f"{avatar.name}#{avatar.id}",
            f"性别: {avatar.gender}",
            f"年龄: {avatar.age}",
            f"境界: {str(avatar.cultivation_progress)}",
            f"灵根: {avatar.root.value}",
            f"位置: ({avatar.pos_x}, {avatar.pos_y})",
        ]
        self._draw_tooltip(lines, *self.pygame.mouse.get_pos(), self.tooltip_font)

    def _draw_tooltip_for_region(self, region, mouse_x: int, mouse_y: int):
        """绘制Region的tooltip"""
        lines = [
            f"区域: {region.name}",
            f"描述: {region.description}",
        ]
        
        # 添加灵气信息
        if hasattr(region, 'essence') and region.essence:
            essence_items = []
            for essence_type, density in region.essence.density.items():
                if density > 0:
                    essence_name = str(essence_type)
                    essence_items.append((density, essence_name))
            
            if essence_items:
                essence_items.sort(reverse=True)
                lines.append("灵气分布:")
                for density, name in essence_items:
                    stars = "★" * density + "☆" * (10 - density)
                    lines.append(f"  {name}: {stars}")
        
        self._draw_tooltip(lines, mouse_x, mouse_y, self.tooltip_font)

    def _load_tile_images(self):
        """加载所有tile类型的图像"""
        import os
        pygame = self.pygame
        
        # 定义所有tile类型
        tile_types = [
            TileType.PLAIN, TileType.WATER, TileType.SEA, TileType.MOUNTAIN,
            TileType.FOREST, TileType.CITY, TileType.DESERT, TileType.RAINFOREST,
            TileType.GLACIER, TileType.SNOW_MOUNTAIN, TileType.VOLCANO,
            TileType.GRASSLAND, TileType.SWAMP, TileType.CAVE, TileType.RUINS, TileType.FARM
        ]
        
        for tile_type in tile_types:
            image_path = f"assets/tiles/{tile_type.value}.png"
            
            if os.path.exists(image_path):
                try:
                    image = pygame.image.load(image_path)
                    scaled_image = pygame.transform.scale(image, (self.tile_size, self.tile_size))
                    self.tile_images[tile_type] = scaled_image
                    print(f"已加载tile图像: {image_path}")
                except Exception as e:
                    print(f"加载tile图像失败 {image_path}: {e}")
                    self._create_fallback_surface(tile_type)
            else:
                print(f"tile图像文件不存在: {image_path}")
                self._create_fallback_surface(tile_type)

    def _create_fallback_surface(self, tile_type):
        """创建默认的fallback surface"""
        fallback_surface = self.pygame.Surface((self.tile_size, self.tile_size))
        fallback_surface.fill((128, 128, 128))  # 灰色
        self.tile_images[tile_type] = fallback_surface

    def _create_font(self, size: int):
        """创建字体"""
        if self.font_path:
            try:
                return self.pygame.font.Font(self.font_path, size)
            except Exception:
                pass
        return self._load_font_with_fallback(size)

    def _load_font_with_fallback(self, size: int):
        """加载字体，带fallback机制"""
        pygame = self.pygame
        
        # 字体候选列表
        candidates = [
            "Microsoft YaHei UI", "Microsoft YaHei", "SimHei", "SimSun",
            "Consolas", "DejaVu Sans", "DejaVu Sans Mono", "Arial Unicode MS",
            "Noto Sans CJK SC", "Noto Sans CJK",
        ]

        for name in candidates:
            try:
                font = pygame.font.SysFont(name, size)
                # 验证字体是否能渲染中文
                test = font.render("测试中文AaBb123", True, (255, 255, 255))
                if test.get_width() > 0:
                    return font
            except Exception:
                continue

        # 退回默认字体
        return pygame.font.SysFont(None, size)


__all__ = ["Front"]


