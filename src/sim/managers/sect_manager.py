import math
from hashlib import md5
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Iterable, List, Tuple

from src.classes.event import Event
from src.systems.battle import get_base_strength
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.core.sect import Sect
    from src.classes.core.world import World
    from src.classes.environment.map import Map


@dataclass
class SectTerritorySnapshot:
    """宗门势力范围快照，用于在多个系统之间复用计算结果。"""

    active_sects: List["Sect"]
    sect_centers: Dict[int, Tuple[int, int]]
    tile_owners: Dict[Tuple[int, int], List[int]]
    owned_tiles_by_sect: Dict[int, List[Tuple[int, int]]]
    border_contact_counts: Dict[Tuple[int, int], int]
    border_tiles_by_sect: Dict[int, int]
    boundary_edges_by_sect: Dict[int, List[dict[str, int | str]]]


class SectManager:
    """
    宗门管理器。
    负责宗门的战力计算、势力范围更新、灵石结算。
    """

    def __init__(self, world: "World"):
        self.world = world

    @staticmethod
    def _normalize_pair(sect_a_id: int, sect_b_id: int) -> Tuple[int, int]:
        a = int(sect_a_id)
        b = int(sect_b_id)
        return (a, b) if a <= b else (b, a)

    def _collect_active_sects(self) -> List["Sect"]:
        """获取当前仍然存续且激活的宗门列表。"""
        # 优先通过 World.sect_context 统一获取本局启用宗门
        sects: Iterable["Sect"] = []
        sect_context = getattr(self.world, "sect_context", None)
        if sect_context is not None:
            sects = sect_context.get_active_sects()
        else:
            sects = getattr(self.world, "existed_sects", []) or []

        # 兜底：若仍为空，则回退到全局 sects_by_id
        if not sects:
            from src.classes.core.sect import sects_by_id as _sects_by_id
            sects = list(_sects_by_id.values())

        return [s for s in sects if getattr(s, "is_active", True)]

    def _update_sect_strength_and_radius(self, sect: "Sect") -> None:
        """
        计算并更新宗门的总战力与势力半径。
        半径公式由配置驱动，默认等价于 int(total_strength) // 10 + 1。
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
        sect_conf = getattr(CONFIG, "sect", None)
        divisor = max(1, int(getattr(sect_conf, "influence_radius_divisor", 10))) if sect_conf else 10
        bias = int(getattr(sect_conf, "influence_radius_bias", 1)) if sect_conf else 1
        sect.influence_radius = int(sect.total_battle_strength) // divisor + bias

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

    def _get_claim_score(
        self,
        *,
        sect_id: int,
        tile_x: int,
        tile_y: int,
        center_x: int,
        center_y: int,
        radius: int,
        total_battle_strength: float,
    ) -> float:
        """
        计算宗门对某个格子的势力归属分数。

        规则：
        - 距离仍是主导项，保证势力范围整体围绕总部扩张。
        - 战力提供接壤区域的竞争优势，使强宗门更容易压缩边界。
        - 使用稳定的确定性噪声，让边界呈现锯齿感，但不会每年无故抖动。
        """
        distance = abs(tile_x - center_x) + abs(tile_y - center_y)
        if distance > radius:
            return float("-inf")

        sect_conf = getattr(CONFIG, "sect", None)
        distance_weight = float(getattr(sect_conf, "territory_distance_weight", 100.0)) if sect_conf else 100.0
        strength_weight = float(getattr(sect_conf, "territory_strength_weight", 12.0)) if sect_conf else 12.0
        noise_weight = float(getattr(sect_conf, "territory_noise_weight", 6.0)) if sect_conf else 6.0

        proximity_score = float(radius - distance + 1)
        strength_score = math.log1p(max(0.0, float(total_battle_strength)))

        digest = md5(f"{sect_id}:{tile_x}:{tile_y}".encode("utf-8")).digest()
        noise = (int.from_bytes(digest[:4], "big") / 0xFFFFFFFF) - 0.5

        return (
            proximity_score * distance_weight
            + strength_score * strength_weight
            + noise * noise_weight
        )

    def _build_boundary_and_contact_stats(
        self,
        tile_owners: Dict[Tuple[int, int], List[int]],
        active_sect_ids: set[int],
    ) -> tuple[
        Dict[Tuple[int, int], int],
        Dict[int, int],
        Dict[int, List[dict[str, int | str]]],
    ]:
        border_contact_counts: Dict[Tuple[int, int], int] = {}
        border_tile_sets: Dict[int, set[Tuple[int, int]]] = {sid: set() for sid in active_sect_ids}
        boundary_edges_by_sect: Dict[int, List[dict[str, int | str]]] = {
            sid: [] for sid in active_sect_ids
        }

        directions = (
            ("left", -1, 0),
            ("right", 1, 0),
            ("top", 0, -1),
            ("bottom", 0, 1),
        )

        for (x, y), owners in tile_owners.items():
            if not owners:
                continue
            owner_id = int(owners[0])
            for side, dx, dy in directions:
                neighbor_owner_list = tile_owners.get((x + dx, y + dy), [])
                neighbor_owner = int(neighbor_owner_list[0]) if neighbor_owner_list else None
                if neighbor_owner == owner_id:
                    continue

                boundary_edges_by_sect.setdefault(owner_id, []).append(
                    {"x": x, "y": y, "side": side}
                )
                if neighbor_owner is None:
                    continue

                border_tile_sets.setdefault(owner_id, set()).add((x, y))
                border_tile_sets.setdefault(neighbor_owner, set()).add((x + dx, y + dy))
                if neighbor_owner > owner_id or (neighbor_owner == owner_id and (dx > 0 or dy > 0)):
                    pair = self._normalize_pair(owner_id, neighbor_owner)
                    border_contact_counts[pair] = border_contact_counts.get(pair, 0) + 1

        border_tiles_by_sect = {
            sid: len(border_tile_sets.get(sid, set()))
            for sid in active_sect_ids
        }
        return border_contact_counts, border_tiles_by_sect, boundary_edges_by_sect

    def _compute_snapshot(self) -> SectTerritorySnapshot:
        """
        计算当前世界下宗门势力范围的快照。
        统一完成：
        - active_sects 收集
        - 战力与半径更新
        - 总部中心坐标
        - tile_owners 填充
        """
        active_sects = self._collect_active_sects()
        tile_owners: Dict[Tuple[int, int], List[int]] = {}
        owned_tiles_by_sect: Dict[int, List[Tuple[int, int]]] = {}
        sect_centers: Dict[int, Tuple[int, int]] = {}
        border_contact_counts: Dict[Tuple[int, int], int] = {}
        border_tiles_by_sect: Dict[int, int] = {}
        boundary_edges_by_sect: Dict[int, List[dict[str, int | str]]] = {}

        game_map: "Map" = getattr(self.world, "map", None)
        if not active_sects or not game_map:
            return SectTerritorySnapshot(
                active_sects=active_sects,
                sect_centers=sect_centers,
                tile_owners=tile_owners,
                owned_tiles_by_sect=owned_tiles_by_sect,
                border_contact_counts=border_contact_counts,
                border_tiles_by_sect=border_tiles_by_sect,
                boundary_edges_by_sect=boundary_edges_by_sect,
            )

        # 1. 更新战力与半径
        for sect in active_sects:
            self._update_sect_strength_and_radius(sect)

        # 2. 计算总部中心坐标
        sect_centers = self._compute_sect_centers(active_sects, game_map)
        if not sect_centers:
            # 与旧逻辑保持一致：若无法确定中心，则不再枚举 tile_owners
            return SectTerritorySnapshot(
                active_sects=active_sects,
                sect_centers=sect_centers,
                tile_owners=tile_owners,
                owned_tiles_by_sect=owned_tiles_by_sect,
                border_contact_counts=border_contact_counts,
                border_tiles_by_sect=border_tiles_by_sect,
                boundary_edges_by_sect=boundary_edges_by_sect,
            )

        # 3. 以“唯一归属”的方式为每个有效格子选出一个最强势力拥有者
        sect_candidates = []
        for sect in active_sects:
            center = sect_centers.get(sect.id)
            radius = int(getattr(sect, "influence_radius", 0) or 0)
            if center is None or radius <= 0:
                continue
            sect_candidates.append(
                (
                    int(sect.id),
                    center[0],
                    center[1],
                    radius,
                    float(getattr(sect, "total_battle_strength", 0.0)),
                )
            )

        for x, y in game_map.tiles.keys():
            best_owner: int | None = None
            best_score = float("-inf")
            for sect_id, center_x, center_y, radius, total_battle_strength in sect_candidates:
                score = self._get_claim_score(
                    sect_id=sect_id,
                    tile_x=x,
                    tile_y=y,
                    center_x=center_x,
                    center_y=center_y,
                    radius=radius,
                    total_battle_strength=total_battle_strength,
                )
                if score > best_score:
                    best_score = score
                    best_owner = sect_id
            if best_owner is None or best_score == float("-inf"):
                continue
            tile_owners[(x, y)] = [best_owner]
            owned_tiles_by_sect.setdefault(best_owner, []).append((x, y))

        border_contact_counts, border_tiles_by_sect, boundary_edges_by_sect = (
            self._build_boundary_and_contact_stats(
                tile_owners,
                {int(sect.id) for sect in active_sects},
            )
        )

        return SectTerritorySnapshot(
            active_sects=active_sects,
            sect_centers=sect_centers,
            tile_owners=tile_owners,
            owned_tiles_by_sect=owned_tiles_by_sect,
            border_contact_counts=border_contact_counts,
            border_tiles_by_sect=border_tiles_by_sect,
            boundary_edges_by_sect=boundary_edges_by_sect,
        )

    def get_snapshot(self) -> SectTerritorySnapshot:
        """
        返回当前世界下宗门势力范围的快照。

        - 统一封装 _compute_sect_centers / _iter_influence_tiles 等内部细节；
        - 供其他系统（关系计算、决策上下文等）复用，避免在多处重复实现相同逻辑。
        """
        return self._compute_snapshot()

    def get_tile_owners(self) -> Tuple[List["Sect"], Dict[Tuple[int, int], List[int]]]:
        """
        计算当前活跃宗门的势力范围分布。

        返回:
            (active_sects, tile_owners)
            - active_sects: 当前仍然存续且激活的宗门列表
            - tile_owners: (x, y) -> [sect_id, ...]
        """
        snapshot = self.get_snapshot()
        # 保持与旧行为一致：若无法确定中心，则返回空的 tile_owners，但 active_sects 仍返回
        return snapshot.active_sects, snapshot.tile_owners

    def calculate_income_by_sect(self, snapshot: SectTerritorySnapshot | None = None) -> Dict[int, float]:
        snapshot = snapshot or self._compute_snapshot()
        active_sects = snapshot.active_sects
        tile_owners = snapshot.tile_owners

        if not active_sects or not snapshot.sect_centers or not tile_owners:
            return {}

        income_by_sect_id: Dict[int, float] = {}
        sect_conf = getattr(CONFIG, "sect", None)
        base_income = float(getattr(sect_conf, "income_per_tile", 10)) if sect_conf else 10.0
        current_month = int(self.world.month_stamp)
        sect_by_id = {int(s.id): s for s in active_sects}

        for owners in tile_owners.values():
            if not owners:
                continue
            sid = int(owners[0])
            sect = sect_by_id.get(sid)
            if sect is None:
                continue
            extra_income = float(sect.get_extra_income_per_tile(current_month))
            effective_income_per_tile = max(0.0, base_income + extra_income)
            income_by_sect_id[sid] = income_by_sect_id.get(sid, 0.0) + effective_income_per_tile

        return income_by_sect_id

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

        snapshot = self._compute_snapshot()
        active_sects = snapshot.active_sects
        tile_owners = snapshot.tile_owners

        # 若无活跃宗门或无法确定中心，则与旧逻辑一样直接返回
        if not active_sects or not snapshot.sect_centers:
            return events

        if not tile_owners:
            # 即便没有任何格子，也仍然生成“战力更新”事件，只是收入为 0
            pass

        # 4. 第二遍：按冲突规则结算各宗门的收入
        income_by_sect_id = self.calculate_income_by_sect(snapshot)

        # 5. 为每个宗门累加收入并生成事件
        from src.i18n import t

        for sect in active_sects:
            raw_income = income_by_sect_id.get(sect.id, 0.0)
            income = int(raw_income)
            stipend_total, _stipend_breakdown = sect.estimate_yearly_member_upkeep()
            net_change = income - stipend_total
            active_war_count = sum(
                1
                for other in active_sects
                if int(getattr(other, "id", 0)) != int(sect.id)
                and self.world.are_sects_at_war(int(sect.id), int(other.id))
            )

            for avatar in getattr(sect, "members", {}).values():
                if getattr(avatar, "is_dead", False):
                    continue
                avatar.magic_stone = avatar.magic_stone + sect.get_member_upkeep_for_avatar(avatar)

            sect.magic_stone += net_change
            weariness_before = int(getattr(sect, "war_weariness", 0) or 0)
            sect.change_war_weariness(active_war_count - 3)
            weariness_after = int(getattr(sect, "war_weariness", 0) or 0)
            content = t(
                "game.sect_update_event",
                sect_name=sect.name,
                income=income,
                upkeep=stipend_total,
                net_change=net_change,
            )
            weariness_text = t(
                "War weariness adjusted to {weariness_after} (active wars: {active_war_count}, yearly recovery: 3, previous: {weariness_before}).",
                weariness_after=weariness_after,
                active_war_count=active_war_count,
                weariness_before=weariness_before,
            )
            content = f"{content} {weariness_text}"

            event = Event(
                month_stamp=self.world.month_stamp,
                content=content,
                related_sects=[sect.id],
            )
            events.append(event)

        return events
