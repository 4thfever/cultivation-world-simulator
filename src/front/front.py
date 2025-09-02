import math
from typing import Dict, List, Optional, Tuple
import asyncio # 新增：导入asyncio

# Front 只依赖项目内部类型定义与 pygame
from src.sim.simulator import Simulator
from src.classes.world import World
from src.classes.tile import TileType
from src.classes.avatar import Avatar, Gender
from src.classes.event import Event


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
        simulator: Simulator,
        *,
        tile_size: int = 32,
        margin: int = 8,
        step_interval_ms: int = 400,
        window_title: str = "Cultivation World Simulator",
        font_path: Optional[str] = None,
        sidebar_width: int = 300,  # 新增：侧边栏宽度
    ):
        self.world = simulator.world
        self.simulator = simulator
        self.tile_size = tile_size
        self.margin = margin
        self.step_interval_ms = step_interval_ms
        self.window_title = window_title
        self.font_path = font_path
        self.sidebar_width = sidebar_width  # 新增：侧边栏宽度

        # 运行时状态
        self._auto_step = True
        self._last_step_ms = 0
        self.events: List[Event] = []  # 新增：存储事件历史

        # 初始化pygame
        import pygame
        self.pygame = pygame
        pygame.init()
        pygame.font.init()

        # 计算窗口大小（包含侧边栏）
        width_px = self.world.map.width * tile_size + margin * 2 + sidebar_width
        height_px = self.world.map.height * tile_size + margin * 2
        self.screen = pygame.display.set_mode((width_px, height_px))
        pygame.display.set_caption(window_title)

        # 字体和缓存
        self.font = self._create_font(16)
        self.tooltip_font = self._create_font(14)
        self.sidebar_font = self._create_font(12)  # 新增：侧边栏字体
        self.status_font = self._create_font(18)  # 新增：状态栏字体（更大更清晰）
        self._region_font_cache: Dict[int, object] = {}

        # 配色方案
        self.colors = {
            "bg": (18, 18, 18),
            "grid": (40, 40, 40),
            "text": (230, 230, 230),
            "tooltip_bg": (32, 32, 32),
            "tooltip_bd": (90, 90, 90),
            "avatar": (240, 220, 90),
            "sidebar_bg": (25, 25, 25),  # 新增：侧边栏背景色
            "sidebar_border": (60, 60, 60),  # 新增：侧边栏边框色
            "event_text": (200, 200, 200),  # 新增：事件文字色
            "status_bg": (15, 15, 15),  # 新增：状态栏背景色（深色）
            "status_border": (50, 50, 50),  # 新增：状态栏边框色
            "status_text": (220, 220, 220),  # 新增：状态栏文字色（亮色）
        }

        # 加载tile图像
        self.tile_images = {}
        self._load_tile_images()

        # 加载avatar头像图像
        self.male_avatars = []
        self.female_avatars = []
        self.avatar_images = {}  # avatar_id -> 图像surface
        self._load_avatar_images()

        self.clock = pygame.time.Clock()

    def add_events(self, new_events: List[Event]):
        """新增：添加新事件到事件历史"""
        self.events.extend(new_events)
        # 保持最多1000个事件，避免内存占用过大
        if len(self.events) > 1000:
            self.events = self.events[-1000:]

    async def _step_once_async(self):
        """异步执行一步模拟"""
        events = await self.simulator.step()  # 获取返回的事件
        if events:  # 新增：将事件添加到事件历史
            self.add_events(events)
        self._last_step_ms = 0

    async def run_async(self):
        """异步主循环"""
        pygame = self.pygame
        running = True
        
        # 用于存储正在进行的step任务
        current_step_task = None
        
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
                        # 手动步进：创建新任务
                        if current_step_task is None or current_step_task.done():
                            current_step_task = asyncio.create_task(self._step_once_async())

            # 自动步进
            if self._auto_step and self._last_step_ms >= self.step_interval_ms:
                # 自动步进：创建新任务
                if current_step_task is None or current_step_task.done():
                    current_step_task = asyncio.create_task(self._step_once_async())
                self._last_step_ms = 0

            # 检查step任务是否完成
            if current_step_task and current_step_task.done():
                try:
                    await current_step_task  # 获取结果（如果有异常会抛出）
                except Exception as e:
                    print(f"Step执行出错: {e}")
                current_step_task = None

            self._render()
            # 使用asyncio.sleep而不是pygame的时钟，避免阻塞
            await asyncio.sleep(0.016)  # 约60fps

        pygame.quit()

    def _step_once(self):
        """执行一步模拟（同步版本，已弃用）"""
        print("警告：_step_once已弃用，请使用异步版本")
        pass

    def _render(self):
        """渲染主画面"""
        pygame = self.pygame
        
        # 清屏
        self.screen.fill(self.colors["bg"])

        # 绘制地图和标签
        self._draw_map()
        hovered_region = self._draw_region_labels()
        hovered_avatar = self._draw_avatars_and_pick_hover()
        
        # 显示tooltip (人物优先级高于region)
        if hovered_avatar is not None:
            self._draw_tooltip_for_avatar(hovered_avatar)
        elif hovered_region is not None:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            self._draw_tooltip_for_region(hovered_region, mouse_x, mouse_y)

        # 状态信息
        self._draw_status_bar()

        # 新增：绘制侧边栏
        self._draw_sidebar()

        pygame.display.flip()

    def _draw_status_bar(self):
        """绘制状态栏 - 包含操作指南和年月信息"""
        pygame = self.pygame
        
        # 状态栏配置
        status_y = 8
        status_height = 32
        padding = 8
        
        # 绘制状态栏背景
        status_rect = pygame.Rect(0, 0, self.screen.get_width(), status_height)
        pygame.draw.rect(self.screen, self.colors["status_bg"], status_rect)
        pygame.draw.line(self.screen, self.colors["status_border"], 
                        (0, status_height), (self.screen.get_width(), status_height), 2)
        
        # 1. 绘制操作指南
        self._draw_operation_guide(status_y, padding)
        
        # 2. 绘制年月信息
        self._draw_year_month_info(status_y, padding)
    
    def _draw_operation_guide(self, y_pos: int, padding: int):
        """绘制操作指南"""
        # 构建操作指南文本
        auto_status = "开" if self._auto_step else "关"
        guide_text = f"A:自动步进({auto_status})  SPACE:单步  ESC:退出"
        
        # 渲染文本
        guide_surf = self.status_font.render(guide_text, True, self.colors["status_text"])
        
        # 绘制文本
        x_pos = self.margin + padding
        self.screen.blit(guide_surf, (x_pos, y_pos))
        
        # 保存操作指南的宽度，供年月信息定位使用
        self._guide_width = guide_surf.get_width()
    
    def _draw_year_month_info(self, y_pos: int, padding: int):
        """绘制年月信息"""
        # 获取年月数据
        year = int(self.simulator.world.month_stamp.get_year())
        month_num = self.simulator.world.month_stamp.get_month().value
        
        # 构建年月文本
        ym_text = f"{year}年{month_num:02d}月"
        
        # 渲染文本
        ym_surf = self.status_font.render(ym_text, True, self.colors["status_text"])
        
        # 计算位置：放在操作指南右边，留适当间距
        x_pos = self.margin + self._guide_width + padding * 3
        self.screen.blit(ym_surf, (x_pos, y_pos))
    
    def _get_month_number(self) -> int:
        """获取月份数字（已弃用，保留向后兼容）"""
        return self.simulator.world.month_stamp.get_month().value



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

        # 绘制每个region的标签
        hovered_region = None
        for region in map_obj.regions.values():
            name = getattr(region, "name", None)
            if not name:
                continue

            # 使用region的center_loc计算屏幕位置
            center_x, center_y = region.center_loc
            screen_x = m + center_x * ts + ts // 2
            screen_y = m + center_y * ts + ts // 2

            # 计算字体大小（基于region面积）
            font_size = self._calculate_font_size_by_area(region.area)
            region_font = self._get_region_font(font_size)

            # 渲染文字
            text_surface = region_font.render(str(name), True, self.colors["text"])
            shadow_surface = region_font.render(str(name), True, (0, 0, 0))

            # 计算位置（居中显示）
            text_w = text_surface.get_width()
            text_h = text_surface.get_height()
            x = int(screen_x - text_w / 2)
            y = int(screen_y - text_h / 2)

            # 检测鼠标悬停
            if (x <= mouse_x <= x + text_w and y <= mouse_y <= y + text_h):
                hovered_region = region

            # 绘制文字（先阴影后主文字）
            self.screen.blit(shadow_surface, (x + 1, y + 1))
            self.screen.blit(text_surface, (x, y))

        return hovered_region



    def _calculate_font_size_by_area(self, area):
        """根据区域面积计算字体大小"""
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

        # 确保新的avatar也有头像分配
        self._assign_avatar_images()

        for avatar_id, avatar in self.simulator.avatars.items():
            cx, cy = self._avatar_center_pixel(avatar)
            
            # 尝试使用头像图片
            avatar_image = self.avatar_images.get(avatar_id)
            if avatar_image:
                # 计算头像图片的位置（居中显示）
                image_rect = avatar_image.get_rect()
                image_x = cx - image_rect.width // 2
                image_y = cy - image_rect.height // 2
                
                # 绘制头像图片
                self.screen.blit(avatar_image, (image_x, image_y))
                
                # 检测悬停（使用图片的矩形区域）
                if image_rect.collidepoint(mouse_x - image_x, mouse_y - image_y):
                    hovered = avatar
                    min_dist = 0  # 如果鼠标在图片内，设为最优先
            else:
                # 回退到圆点显示
                radius = max(8, self.tile_size // 3)
                pygame.draw.circle(self.screen, self.colors["avatar"], (cx, cy), radius)
                
                # 检测悬停（使用圆形区域）
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
            f"{avatar.name}",
            f"性别: {avatar.gender}",
            f"年龄: {avatar.age}",
            f"境界: {str(avatar.cultivation_progress)}",
            f"灵根: {avatar.root.value}",
            f"个性: {avatar.persona.name}",
            f"位置: ({avatar.pos_x}, {avatar.pos_y})",
        ]
        
        # 添加历史动作信息
        lines.append("")  # 空行分隔
        lines.append("历史动作:")
        lines.extend(avatar.get_history_action_pairs_str().split("\n"))
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
                image = pygame.image.load(image_path)
                scaled_image = pygame.transform.scale(image, (self.tile_size, self.tile_size))
                self.tile_images[tile_type] = scaled_image

    def _load_avatar_images(self):
        """加载avatar头像图像"""
        import os
        import random
        pygame = self.pygame
        
        # 加载男性头像
        male_dir = "assets/males"
        if os.path.exists(male_dir):
            for filename in os.listdir(male_dir):
                # 只加载数字序号的png文件，跳过original.png
                if filename.endswith('.png') and filename != 'original.png' and filename.replace('.png', '').isdigit():
                    image_path = os.path.join(male_dir, filename)
                    try:
                        image = pygame.image.load(image_path)
                        # 调整头像大小，减小20%后再放大1.2倍
                        avatar_size = max(26, int(self.tile_size * 4 // 3))
                        scaled_image = pygame.transform.scale(image, (avatar_size, avatar_size))
                        self.male_avatars.append(scaled_image)
                    except pygame.error:
                        continue  # 跳过无法加载的图片
        
        # 加载女性头像
        female_dir = "assets/females"
        if os.path.exists(female_dir):
            for filename in os.listdir(female_dir):
                # 只加载数字序号的png文件，跳过original.png
                if filename.endswith('.png') and filename != 'original.png' and filename.replace('.png', '').isdigit():
                    image_path = os.path.join(female_dir, filename)
                    try:
                        image = pygame.image.load(image_path)
                        # 调整头像大小，减小20%后再放大1.2倍
                        avatar_size = max(26, int(self.tile_size * 4 // 3 * 0.8 * 1.2))
                        scaled_image = pygame.transform.scale(image, (avatar_size, avatar_size))
                        self.female_avatars.append(scaled_image)
                    except pygame.error:
                        continue  # 跳过无法加载的图片
        
        # 为每个现有的avatar分配头像
        self._assign_avatar_images()
    
    def _assign_avatar_images(self):
        """为每个avatar分配头像图片"""
        import random
        
        for avatar_id, avatar in self.simulator.avatars.items():
            if avatar_id not in self.avatar_images:
                if avatar.gender == Gender.MALE and self.male_avatars:
                    self.avatar_images[avatar_id] = random.choice(self.male_avatars)
                elif avatar.gender == Gender.FEMALE and self.female_avatars:
                    self.avatar_images[avatar_id] = random.choice(self.female_avatars)
                # 如果没有可用的头像，则使用None，后续会画圆点作为fallback

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

    def _draw_sidebar(self):
        """新增：绘制侧边栏"""
        pygame = self.pygame
        
        # 计算侧边栏位置
        sidebar_x = self.world.map.width * self.tile_size + self.margin * 2
        sidebar_y = self.margin
        
        # 绘制侧边栏背景
        sidebar_rect = pygame.Rect(sidebar_x, sidebar_y, self.sidebar_width, 
                                 self.screen.get_height() - self.margin * 2)
        pygame.draw.rect(self.screen, self.colors["sidebar_bg"], sidebar_rect)
        pygame.draw.rect(self.screen, self.colors["sidebar_border"], sidebar_rect, 2)
        
        # 绘制标题
        title_text = "事件历史"
        title_surf = self.sidebar_font.render(title_text, True, self.colors["text"])
        title_x = sidebar_x + 10
        title_y = sidebar_y + 10
        self.screen.blit(title_surf, (title_x, title_y))
        
        # 绘制分隔线
        line_y = title_y + title_surf.get_height() + 10
        pygame.draw.line(self.screen, self.colors["sidebar_border"], 
                        (sidebar_x + 10, line_y), 
                        (sidebar_x + self.sidebar_width - 10, line_y), 1)
        
        # 绘制事件列表
        event_y = line_y + 15
        max_events = (self.screen.get_height() - event_y - self.margin) // 20  # 每行20像素
        
        # 显示最近的事件（从最新开始）
        recent_events = self.events[-max_events:] if len(self.events) > max_events else self.events
        
        for event in reversed(recent_events):  # 最新的在顶部
            event_text = str(event)
            
            # 如果文本太长，截断它
            if len(event_text) > 35:  # 大约35个字符
                event_text = event_text[:32] + "..."
            
            event_surf = self.sidebar_font.render(event_text, True, self.colors["event_text"])
            self.screen.blit(event_surf, (title_x, event_y))
            event_y += 20
            
            # 如果超出显示区域，停止绘制
            if event_y > self.screen.get_height() - self.margin:
                break
        
        # 如果没有事件，显示提示信息
        if not self.events:
            no_event_text = "暂无事件"
            no_event_surf = self.sidebar_font.render(no_event_text, True, self.colors["event_text"])
            self.screen.blit(no_event_surf, (title_x, event_y))


__all__ = ["Front"]


