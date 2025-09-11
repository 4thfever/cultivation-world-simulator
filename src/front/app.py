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

    def add_events(self, new_events: List[Event]):
        self.events.extend(new_events)
        if len(self.events) > 1000:
            self.events = self.events[-1000:]

    async def _step_once_async(self):
        events = await self.simulator.step()
        if events:
            self.add_events(events)
        self._last_step_ms = 0

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
            pygame, self.screen, self.colors, self.simulator, self.avatar_images, self.tile_size, self.margin
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
        for avatar_id, avatar in self.simulator.avatars.items():
            if avatar_id not in self.avatar_images:
                if avatar.gender == Gender.MALE and self.male_avatars:
                    self.avatar_images[avatar_id] = random.choice(self.male_avatars)
                elif avatar.gender == Gender.FEMALE and self.female_avatars:
                    self.avatar_images[avatar_id] = random.choice(self.female_avatars)


__all__ = ["Front"]


