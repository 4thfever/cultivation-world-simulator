import asyncio
import random
from typing import Dict, List, Optional

from src.sim.simulator import Simulator
from src.classes.event import Event
from src.classes.avatar import Avatar, Gender

from .theme import COLORS
from .fonts import create_font, get_region_font as _get_region_font_cached
from .assets import load_tile_images, load_tile_originals, load_avatar_images, load_sect_images, load_region_images
from .rendering import (
    draw_map,
    draw_region_labels,
    draw_avatars_and_pick_hover,
    draw_tooltip_for_avatar,
    draw_tooltip_for_region,
    draw_status_bar,
    STATUS_BAR_HEIGHT,
    draw_small_regions,
    draw_sect_headquarters,
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
        height_px = self.world.map.height * tile_size + margin * 2 + STATUS_BAR_HEIGHT
        self.screen = pygame.display.set_mode((width_px, height_px))
        pygame.display.set_caption(window_title)

        self.font = create_font(self.pygame, 16, self.font_path)
        self.tooltip_font = create_font(self.pygame, 14, self.font_path)
        self.sidebar_font = create_font(self.pygame, 14, self.font_path)
        self.status_font = create_font(self.pygame, 18, self.font_path)
        self.name_font = create_font(self.pygame, 16, self.font_path)
        self._region_font_cache: Dict[int, object] = {}

        self.colors = COLORS

        self.tile_images = load_tile_images(self.pygame, self.tile_size)
        self.tile_originals = load_tile_originals(self.pygame)
        self.sect_images = load_sect_images(self.pygame, self.tile_size)
        self.region_images = load_region_images(self.pygame, self.tile_size)
        self.male_avatars, self.female_avatars = load_avatar_images(self.pygame, self.tile_size)
        self.avatar_images: Dict[str, object] = {}
        self._assign_avatar_images()

        self.clock = pygame.time.Clock()

        # 渲染插值状态：avatar_id -> {start_px, start_py, target_px, target_py, start_ms, duration_ms}
        self._avatar_display_states: Dict[str, Dict[str, float]] = {}
        self._init_avatar_display_states()

        # 侧栏筛选状态：None 表示所有人；否则为 avatar_id
        self._sidebar_filter_avatar_id: Optional[str] = None
        self._sidebar_filter_open: bool = False

        # 侧栏筛选选项缓存（列表）与脏标记
        self._sidebar_options_cache: Optional[List[tuple[str, Optional[str]]]] = None
        self._sidebar_options_dirty: bool = True

        # hover 轮换状态（滚轮切换）
        self._hover_anchor_pos: Optional[tuple[int, int]] = None
        self._hover_candidates: List[str] = []  # avatar_id 列表（当前锚点下）
        self._hover_index: int = 0
        self._hover_last_build_ms: int = 0

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
        # 世界推进后，角色增减或名称改变的可能性上升，置脏侧栏选项
        self._sidebar_options_dirty = True

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
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_mouse_click()
                # 兼容旧版滚轮为 MOUSEBUTTON 4/5
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (4, 5):
                    delta = 1 if event.button == 4 else -1
                    self._on_mouse_wheel(delta)
                # pygame 2 的标准滚轮事件
                elif getattr(pygame, "MOUSEWHEEL", None) is not None and event.type == pygame.MOUSEWHEEL:
                    # event.y: 上滚为正，下滚为负
                    self._on_mouse_wheel(int(getattr(event, "y", 0)))
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
        draw_map(
            pygame,
            self.screen,
            self.colors,
            self.world,
            self.tile_images,
            self.tile_size,
            self.margin,
            STATUS_BAR_HEIGHT,
        )
        # 底图后叠加小区域整图（2x2/3x3），再绘制宗门总部，避免被覆盖
        draw_small_regions(pygame, self.screen, self.world, self.region_images, self.tile_images, self.tile_size, self.margin, STATUS_BAR_HEIGHT, self.tile_originals)
        draw_sect_headquarters(pygame, self.screen, self.world, self.sect_images, self.tile_size, self.margin, STATUS_BAR_HEIGHT)
        hovered_region = draw_region_labels(
            pygame,
            self.screen,
            self.colors,
            self.world,
            self._get_region_font,
            self.tile_size,
            self.margin,
            STATUS_BAR_HEIGHT,
        )
        self._assign_avatar_images()
        hovered_default, hover_candidates = draw_avatars_and_pick_hover(
            pygame,
            self.screen,
            self.colors,
            self.simulator,
            self.avatar_images,
            self.tile_size,
            self.margin,
            self._get_display_center,
            STATUS_BAR_HEIGHT,
            self.name_font,
            self._sidebar_filter_avatar_id,
        )
        hovered_avatar = self._pick_hover_with_scroll(hovered_default, hover_candidates)
        # 先绘制状态栏和侧边栏，再绘制 tooltip 保证 tooltip 在最上层
        draw_status_bar(pygame, self.screen, self.colors, self.status_font, self.margin, self.world, self._auto_step)

        # 计算筛选后的事件
        if self._sidebar_filter_avatar_id is None:
            events_to_draw: List[Event] = self.events
        else:
            aid = self._sidebar_filter_avatar_id
            events_to_draw = [e for e in self.events if getattr(e, "related_avatars", None) and (aid in e.related_avatars)]

        # 构造下拉选项（第一个是所有人；其余为当前世界中的角色）- 带缓存
        options = self._get_sidebar_options_cached()
        sel_label = "所有人"
        if self._sidebar_filter_avatar_id is not None:
            sel_avatar = self.world.avatar_manager.avatars.get(self._sidebar_filter_avatar_id)
            if sel_avatar is not None:
                sel_label = sel_avatar.name

        sidebar_ui = draw_sidebar(
            pygame, self.screen, self.colors, self.sidebar_font, events_to_draw,
            self.world.map, self.tile_size, self.margin, self.sidebar_width,
            filter_selected_label=sel_label,
            filter_is_open=self._sidebar_filter_open,
            filter_options=options,
        )
        # 保存供点击检测
        self._sidebar_ui = sidebar_ui
        if hovered_avatar is not None:
            draw_tooltip_for_avatar(pygame, self.screen, self.colors, self.tooltip_font, hovered_avatar)
            # 绘制候选徽标（仅当存在多个候选）
            if len(hover_candidates) >= 2:
                from .rendering import draw_hover_badge
                # 取当前 hover 对象的显示中心
                cx_f, cy_f = self._get_display_center(hovered_avatar, self.tile_size, self.margin)
                cx, cy = int(cx_f), int(cy_f)
                # 计算当前索引（1-based）
                try:
                    idx = self._hover_candidates.index(hovered_avatar.id)
                except ValueError:
                    idx = 0
                draw_hover_badge(pygame, self.screen, self.colors, self.tooltip_font, cx, cy, idx + 1, len(hover_candidates), STATUS_BAR_HEIGHT)
        elif hovered_region is not None:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            draw_tooltip_for_region(pygame, self.screen, self.colors, self.tooltip_font, hovered_region, mouse_x, mouse_y)
        pygame.display.flip()

    def _handle_mouse_click(self) -> None:
        # 仅处理侧栏筛选点击
        pygame = self.pygame
        mouse_pos = pygame.mouse.get_pos()
        ui = getattr(self, "_sidebar_ui", {}) or {}
        toggle_rect = ui.get("filter_toggle_rect")
        option_rects = ui.get("filter_option_rects") or []
        if toggle_rect and toggle_rect.collidepoint(mouse_pos):
            self._sidebar_filter_open = not self._sidebar_filter_open
            return
        if self._sidebar_filter_open:
            for oid, rect in option_rects:
                if rect.collidepoint(mouse_pos):
                    self._sidebar_filter_avatar_id = oid if oid is not None else None
                    self._sidebar_filter_open = False
                    return

    def _get_region_font(self, size: int):
        return _get_region_font_cached(self.pygame, self._region_font_cache, size, self.font_path)

    # --- Hover 轮换逻辑 ---
    def _is_mouse_near_anchor(self, radius_px: int = 20) -> bool:
        if self._hover_anchor_pos is None:
            return False
        mx, my = self.pygame.mouse.get_pos()
        ax, ay = self._hover_anchor_pos
        dx = mx - ax
        dy = my - ay
        return (dx * dx + dy * dy) <= (radius_px * radius_px)

    def _rebuild_hover_candidates(self, hovered_default: Optional[Avatar], candidates: List[Avatar]) -> None:
        self._hover_anchor_pos = self.pygame.mouse.get_pos()
        self._hover_candidates = [a.id for a in candidates]
        if hovered_default is not None and hovered_default.id in self._hover_candidates:
            self._hover_index = self._hover_candidates.index(hovered_default.id)
        else:
            self._hover_index = 0
        self._hover_last_build_ms = self._now_ms()

    def _pick_hover_with_scroll(self, hovered_default: Optional[Avatar], candidates: List[Avatar]) -> Optional[Avatar]:
        # 无候选时清空状态
        if not candidates:
            self._hover_anchor_pos = None
            self._hover_candidates = []
            self._hover_index = 0
            return None
        # 当前候选ID列表
        current_ids = [a.id for a in candidates]
        # 需要重建的情形：
        # 1) 没有锚点；2) 鼠标离锚点太远；3) 候选集合变化；4) 距上次构建时间过久
        need_rebuild = False
        if self._hover_anchor_pos is None:
            need_rebuild = True
        elif not self._is_mouse_near_anchor():
            need_rebuild = True
        elif current_ids != self._hover_candidates:
            need_rebuild = True
        elif (self._now_ms() - self._hover_last_build_ms) > 800:
            need_rebuild = True
        if need_rebuild:
            self._rebuild_hover_candidates(hovered_default, candidates)
        # 选出当前下标对应的 avatar
        if not self._hover_candidates:
            return hovered_default
        self._hover_index %= max(1, len(self._hover_candidates))
        aid = self._hover_candidates[self._hover_index]
        return self.world.avatar_manager.avatars.get(aid, hovered_default)

    def _on_mouse_wheel(self, delta: int) -> None:
        # 仅当有至少两个候选且鼠标仍在锚点附近时进行轮换
        if len(self._hover_candidates) >= 2 and self._is_mouse_near_anchor():
            if delta > 0:
                self._hover_index = (self._hover_index - 1) % len(self._hover_candidates)
            elif delta < 0:
                self._hover_index = (self._hover_index + 1) % len(self._hover_candidates)
            # 轻微刷新锚点时间，避免过快过期
            self._hover_last_build_ms = self._now_ms()

    def _assign_avatar_images(self):
        # 若在上一次分配后头像集合未发生变化，且数量相等，则跳过
        if not getattr(self, "_avatar_assign_dirty", True) and len(self.avatar_images) == len(self.world.avatar_manager.avatars):
            return
        assigned_new = False
        for avatar_id, avatar in self.world.avatar_manager.avatars.items():
            if avatar_id not in self.avatar_images:
                if avatar.gender == Gender.MALE and self.male_avatars:
                    self.avatar_images[avatar_id] = random.choice(self.male_avatars)
                elif avatar.gender == Gender.FEMALE and self.female_avatars:
                    self.avatar_images[avatar_id] = random.choice(self.female_avatars)
                assigned_new = True
        # 分配完成，标记为干净；在后续状态更新时会被置脏
        if assigned_new or len(self.avatar_images) == len(self.world.avatar_manager.avatars):
            self._avatar_assign_dirty = False

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
        # 任何插值初始化/同步都可能意味着角色集合发生变化，置脏以便头像图像分配在下一帧检查
        self._avatar_assign_dirty = True
        # 角色集合变动也会影响侧栏选项
        self._sidebar_options_dirty = True

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

    def _get_sidebar_options_cached(self) -> List[tuple[str, Optional[str]]]:
        if (not self._sidebar_options_dirty) and self._sidebar_options_cache is not None:
            return self._sidebar_options_cache
        options: List[tuple[str, Optional[str]]] = [("所有人", None)]
        for avatar_id, avatar in self.world.avatar_manager.avatars.items():
            options.append((avatar.name, avatar_id))
        self._sidebar_options_cache = options
        self._sidebar_options_dirty = False
        return options


__all__ = ["Front"]


