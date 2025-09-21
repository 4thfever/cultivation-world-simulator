import asyncio
from typing import Dict, List, Optional

from src.sim.simulator import Simulator
from src.classes.event import Event
from src.classes.avatar import Avatar, Gender

from .theme import COLORS
from .fonts import create_font, get_region_font as _get_region_font_cached
from .assets import load_tile_images, load_avatar_images
from .rendering import (
    draw_map,
    draw_region_labels,
    draw_avatars_and_pick_hover,
    draw_tooltip_for_avatar,
    draw_tooltip_for_region,
    draw_status_bar,
)
from .events_panel import draw_sidebar


class Front:
    def __init__(
        self,
        simulator: Simulator,
        *,
        tile_size: int = 32,
        margin: int = 8,
        step_interval_ms: int = 400,
        window_title: str = "Cultivation World Simulator",
        font_path: Optional[str] = None,
        sidebar_width: int = 300,
    ):
        self.world = simulator.world
        self.simulator = simulator
        self.tile_size = tile_size
        self.margin = margin
        self.step_interval_ms = step_interval_ms
        self.window_title = window_title
        self.font_path = font_path
        self.sidebar_width = sidebar_width

        self._auto_step = True
        self._last_step_ms = 0
        self.events: List[Event] = []

        import pygame
        self.pygame = pygame
        pygame.init()
        pygame.font.init()

        width_px = self.world.map.width * tile_size + margin * 2 + sidebar_width
        height_px = self.world.map.height * tile_size + margin * 2
        self.screen = pygame.display.set_mode((width_px, height_px))
        pygame.display.set_caption(window_title)

        self.font = create_font(self.pygame, 16, self.font_path)
        self.tooltip_font = create_font(self.pygame, 14, self.font_path)
        self.sidebar_font = create_font(self.pygame, 12, self.font_path)
        self.status_font = create_font(self.pygame, 18, self.font_path)
        self._region_font_cache: Dict[int, object] = {}

        self.colors = COLORS

        self.tile_images = load_tile_images(self.pygame, self.tile_size)
        self.male_avatars, self.female_avatars = load_avatar_images(self.pygame, self.tile_size)
        self.avatar_images: Dict[str, object] = {}
        self._assign_avatar_images()

        self.clock = pygame.time.Clock()

        # 渲染插值状态：avatar_id -> {start_px, start_py, target_px, target_py, start_ms, duration_ms}
        self._avatar_display_states: Dict[str, Dict[str, float]] = {}
        self._init_avatar_display_states()

    def add_events(self, new_events: List[Event]):
        self.events.extend(new_events)
        if len(self.events) > 1000:
            self.events = self.events[-1000:]

    async def _step_once_async(self):
        events = await self.simulator.step()
        if events:
            self.add_events(events)
        self._last_step_ms = 0
        # 步进完成后，更新插值目标
        self._update_avatar_display_targets()

    async def run_async(self):
        pygame = self.pygame
        running = True
        current_step_task = None
        while running:
            dt_ms = self.clock.tick(60)
            self._last_step_ms += dt_ms
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_a:
                        self._auto_step = not self._auto_step
                    elif event.key == pygame.K_SPACE:
                        if current_step_task is None or current_step_task.done():
                            current_step_task = asyncio.create_task(self._step_once_async())
            if self._auto_step and self._last_step_ms >= self.step_interval_ms:
                if current_step_task is None or current_step_task.done():
                    current_step_task = asyncio.create_task(self._step_once_async())
                self._last_step_ms = 0
            if current_step_task and current_step_task.done():
                await current_step_task
                current_step_task = None
                # 再次确保目标同步（防止外部触发的状态变更遗漏）
                self._update_avatar_display_targets()
            self._render()
            await asyncio.sleep(0.016)
        pygame.quit()

    def _render(self):
        pygame = self.pygame
        self.screen.fill(self.colors["bg"])
        draw_map(pygame, self.screen, self.colors, self.world, self.tile_images, self.tile_size, self.margin)
        hovered_region = draw_region_labels(
            pygame,
            self.screen,
            self.colors,
            self.world,
            self._get_region_font,
            self.tile_size,
            self.margin,
        )
        self._assign_avatar_images()
        hovered_avatar = draw_avatars_and_pick_hover(
            pygame,
            self.screen,
            self.colors,
            self.simulator,
            self.avatar_images,
            self.tile_size,
            self.margin,
            self._get_display_center,
        )
        # 先绘制状态栏和侧边栏，再绘制 tooltip 保证 tooltip 在最上层
        draw_status_bar(pygame, self.screen, self.colors, self.status_font, self.margin, self.world, self._auto_step)
        draw_sidebar(
            pygame, self.screen, self.colors, self.sidebar_font, self.events,
            self.world.map, self.tile_size, self.margin, self.sidebar_width,
        )
        if hovered_avatar is not None:
            draw_tooltip_for_avatar(pygame, self.screen, self.colors, self.tooltip_font, hovered_avatar)
        elif hovered_region is not None:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            draw_tooltip_for_region(pygame, self.screen, self.colors, self.tooltip_font, hovered_region, mouse_x, mouse_y)
        pygame.display.flip()

    def _get_region_font(self, size: int):
        return _get_region_font_cached(self.pygame, self._region_font_cache, size, self.font_path)

    def _assign_avatar_images(self):
        import random
        for avatar_id, avatar in self.world.avatar_manager.avatars.items():
            if avatar_id not in self.avatar_images:
                if avatar.gender == Gender.MALE and self.male_avatars:
                    self.avatar_images[avatar_id] = random.choice(self.male_avatars)
                elif avatar.gender == Gender.FEMALE and self.female_avatars:
                    self.avatar_images[avatar_id] = random.choice(self.female_avatars)

    # --- 插值辅助 ---
    def _now_ms(self) -> int:
        return self.pygame.time.get_ticks()

    def _init_avatar_display_states(self):
        now = self._now_ms()
        ts = self.tile_size
        m = self.margin
        # 清理已不存在的 avatar 状态
        to_del = [aid for aid in self._avatar_display_states.keys() if aid not in self.world.avatar_manager.avatars]
        for aid in to_del:
            self._avatar_display_states.pop(aid, None)
        # 初始化/补全
        for avatar_id, avatar in self.world.avatar_manager.avatars.items():
            if avatar_id not in self._avatar_display_states:
                cx = m + avatar.pos_x * ts + ts // 2
                cy = m + avatar.pos_y * ts + ts // 2
                self._avatar_display_states[avatar_id] = {
                    "start_px": float(cx),
                    "start_py": float(cy),
                    "target_px": float(cx),
                    "target_py": float(cy),
                    "start_ms": float(now),
                    "duration_ms": float(max(1, self.step_interval_ms)),
                }

    def _update_avatar_display_targets(self):
        now = self._now_ms()
        ts = self.tile_size
        m = self.margin
        self._init_avatar_display_states()
        for avatar_id, avatar in self.world.avatar_manager.avatars.items():
            state = self._avatar_display_states[avatar_id]
            # 当前目标像素
            cur_target_x = m + avatar.pos_x * ts + ts // 2
            cur_target_y = m + avatar.pos_y * ts + ts // 2
            if int(state["target_px"]) != cur_target_x or int(state["target_py"]) != cur_target_y:
                # 以当前插值位置为新起点，目标设为最新位置
                # 计算当前插值位置
                elapsed = max(0.0, float(now) - float(state["start_ms"]))
                duration = max(1.0, float(state["duration_ms"]))
                t = min(1.0, elapsed / duration)
                cur_x = float(state["start_px"]) + (float(state["target_px"]) - float(state["start_px"])) * t
                cur_y = float(state["start_py"]) + (float(state["target_py"]) - float(state["start_py"])) * t
                state["start_px"] = cur_x
                state["start_py"] = cur_y
                state["target_px"] = float(cur_target_x)
                state["target_py"] = float(cur_target_y)
                state["start_ms"] = float(now)
                state["duration_ms"] = float(max(1, self.step_interval_ms))

    def _get_display_center(self, avatar: Avatar, tile_size: int, margin: int):
        # 忽略传入的 tile_size/margin，优先使用 Front 的，以避免不一致
        state = self._avatar_display_states.get(avatar.id)
        if not state:
            # 回退：未初始化时直接返回逻辑中心
            cx = self.margin + avatar.pos_x * self.tile_size + self.tile_size // 2
            cy = self.margin + avatar.pos_y * self.tile_size + self.tile_size // 2
            return float(cx), float(cy)
        now = self._now_ms()
        elapsed = max(0.0, float(now) - float(state["start_ms"]))
        duration = max(1.0, float(state["duration_ms"]))
        t = min(1.0, elapsed / duration)
        # 使用轻微的 ease-in-out（近似）：t' = 3t^2 - 2t^3
        te = t * t * (3.0 - 2.0 * t)
        x = float(state["start_px"]) + (float(state["target_px"]) - float(state["start_px"])) * te
        y = float(state["start_py"]) + (float(state["target_py"]) - float(state["start_py"])) * te
        return x, y


__all__ = ["Front"]


