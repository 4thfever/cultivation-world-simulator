import math
from typing import TYPE_CHECKING, Dict, Iterable, Iterator, List, Tuple

from src.classes.event import Event
from src.systems.battle import get_base_strength
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.core.sect import Sect
    from src.classes.core.world import World
    from src.classes.environment.map import Map


class SectManager:
    """
    宗门管理器。
    负责宗门的战力计算、势力范围更新、灵石结算。
    """

    def __init__(self, world: "World"):
        self.world = world

    def _collect_active_sects(self) -> List["Sect"]:
        """获取当前仍然存续且激活的宗门列表。"""
        sects: Iterable["Sect"] = getattr(self.world, "existed_sects", []) or []
        return [s for s in sects if getattr(s, "is_active", True)]

    def _update_sect_strength_and_radius(self, sect: "Sect") -> None:
        """
        计算并更新宗门的总战力与势力半径。
        半径公式：int(total_strength) // 10 + 1
        """
        # 直接通过宗门的 members 属性获取存活的成员
        members = [m for m in sect.members.values() if not getattr(m, "is_dead", False)]

        # 计算总战力: log(sum(exp(成员战力)))，使用 max trick 保持数值稳定
        total_strength = 0.0
        if members:
            strengths = [float(get_base_strength(m)) for m in members]
            if strengths:
                max_str = max(strengths)
                # 防止 exp 溢出，限制上限
                sum_exp = sum(
                    math.exp(max(-500.0, min(s - max_str, 500.0)))
                    for s in strengths
                )
                total_strength = max_str + math.log(sum_exp)

        sect.total_battle_strength = max(0.0, total_strength)
        sect.influence_radius = int(sect.total_battle_strength) // 10 + 1

    def _compute_sect_centers(
        self, sects: List["Sect"], game_map: "Map"
    ) -> Dict[int, Tuple[int, int]]:
        """
        基于地图上的 SectRegion，计算每个宗门总部的中心坐标。
        返回 dict: sect_id -> (x, y)
        """
        centers: Dict[int, Tuple[int, int]] = {}

        # 构建 sect_id -> 对应 SectRegion 的所有坐标
        region_cors = getattr(game_map, "region_cors", {}) or {}
        for region in getattr(game_map, "sect_regions", {}).values():
            sect_id = getattr(region, "sect_id", -1)
            if sect_id <= 0 or sect_id in centers:
                continue

            cors = region_cors.get(region.id)
            if not cors:
                continue

            centers[sect_id] = game_map.get_center_locs(cors)

        # 只保留当前实际存在的宗门
        return {sect.id: centers[sect.id] for sect in sects if sect.id in centers}

    def _iter_influence_tiles(
        self, center_x: int, center_y: int, radius: int, game_map: "Map"
    ) -> Iterator[Tuple[int, int]]:
        """
        枚举以 (center_x, center_y) 为中心、曼哈顿半径为 radius 的菱形范围内所有有效格子。
        """
        if radius <= 0:
            return

        for dx in range(-radius, radius + 1):
            max_dy = radius - abs(dx)
            for dy in range(-max_dy, max_dy + 1):
                x = center_x + dx
                y = center_y + dy
                if game_map.is_in_bounds(x, y) and (x, y) in game_map.tiles:
                    yield (x, y)

    def update_sects(self) -> List[Event]:
        """
        每年底（或初）结算一次。
        流程：
        1. 计算活跃宗门的总战力与势力半径。
        2. 确定每个宗门总部中心坐标。
        3. 第一遍遍历：按宗门半径枚举势力菱形范围，为每个格子记录所有占据宗门。
        4. 第二遍遍历：根据“冲突平均分”规则，把每个格子的基础灵石产出分配给相关宗门。
        5. 为每个宗门累加收入并生成年度事件。
        """
        events: List[Event] = []

        active_sects = self._collect_active_sects()
        if not active_sects or not getattr(self.world, "map", None):
            return events

        game_map: "Map" = self.world.map

        # 1. 更新战力与半径
        for sect in active_sects:
            self._update_sect_strength_and_radius(sect)

        # 2. 计算总部中心坐标
        sect_centers = self._compute_sect_centers(active_sects, game_map)
        if not sect_centers:
            return events

        # 3. 第一遍：记录每个格子被哪些宗门占据
        tile_owners: Dict[Tuple[int, int], List[int]] = {}
        for sect in active_sects:
            center = sect_centers.get(sect.id)
            radius = getattr(sect, "influence_radius", 0)
            if center is None or radius <= 0:
                continue

            cx, cy = center
            for x, y in self._iter_influence_tiles(cx, cy, radius, game_map):
                owners = tile_owners.setdefault((x, y), [])
                owners.append(sect.id)

        if not tile_owners:
            # 即便没有任何格子，也仍然生成“战力更新”事件，只是收入为 0
            pass

        # 4. 第二遍：按冲突规则结算各宗门的收入
        income_by_sect_id: Dict[int, float] = {}

        sect_conf = getattr(CONFIG, "sect", None)
        base_income = getattr(sect_conf, "income_per_tile", 10) if sect_conf else 10

        for owners in tile_owners.values():
            n = len(owners)
            if n == 0:
                continue
            share = base_income / n
            for sid in owners:
                income_by_sect_id[sid] = income_by_sect_id.get(sid, 0.0) + share

        # 5. 为每个宗门累加收入并生成事件
        from src.i18n import t

        for sect in active_sects:
            raw_income = income_by_sect_id.get(sect.id, 0.0)
            income = int(raw_income)
            sect.magic_stone += income

            content = t(
                "game.sect_update_event",
                sect_name=sect.name,
                strength=int(sect.total_battle_strength),
                radius=sect.influence_radius,
                income=income,
            )

            # 兼容：如果未找到配置则回退到默认英文字符串形式
            if content == "game.sect_update_event":
                content = (
                    f"[{sect.name}] this year's total battle strength reached "
                    f"{int(sect.total_battle_strength)}, territory radius became "
                    f"{sect.influence_radius}, gaining {income} magic stones from the territory."
                )

            event = Event(
                month_stamp=self.world.month_stamp,
                content=content,
                related_sects=[sect.id],
            )
            events.append(event)

        return events
