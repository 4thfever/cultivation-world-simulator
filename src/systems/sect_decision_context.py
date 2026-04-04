from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.sim.managers.sect_manager import SectManager
from src.i18n import t
from src.systems.sect_relations import compute_sect_relations
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.core.sect import Sect
    from src.classes.core.world import World
    from src.classes.event_storage import EventStorage


@dataclass
class SectDecisionContext:
    """
    宗门决策上下文视图。

    面向“宗门自身决策 / AI / LLM”的只读快照，包含：
    - 当前静态与基础展示信息（与 UI/详情保持一致）
    - 当前战力与势力范围
    - 当前经济能力（基于当前势力格与效果推导的收入能力）
    - 当前宗门间关系（数值与理由拆解）
    - 与本宗相关的最近若干历史事件
    """

    # 基础静态 / 展示信息
    basic_structured: Dict[str, Any]
    basic_text: str

    # 战力与势力范围（当前快照）
    power: Dict[str, Any]
    territory: Dict[str, Any]
    self_assessment: Dict[str, Any]

    # 经济能力（当前快照）
    economy: Dict[str, Any]

    # 宗门关系（当前快照）
    relations: List[Dict[str, Any]]
    relations_summary: str

    # 历史事件（最近 N 条）
    history: Dict[str, Any]

    # 宗门身份与治理约束
    identity: Dict[str, Any] = field(default_factory=dict)

    # 门规与宗门决策候选
    diplomacy_targets: List[Dict[str, Any]] = field(default_factory=list)
    active_wars: List[Dict[str, Any]] = field(default_factory=list)
    rule: Dict[str, Any] = field(default_factory=dict)
    recruitment_candidates: List[Dict[str, Any]] = field(default_factory=list)
    member_candidates: List[Dict[str, Any]] = field(default_factory=list)


def build_sect_decision_context(
    sect: "Sect",
    world: "World",
    event_storage: "EventStorage",
    *,
    history_limit: int = 50,
) -> SectDecisionContext:
    """
    构建给“宗门自身决策”使用的只读上下文。

    - 所有数值（战力、势力、关系、收入能力）均基于“当前世界状态”的一次性快照；
    - 仅历史事件部分会回溯最近 N 条与本宗相关的事件。
    """
    # 1. 基础信息（与现有 UI/详情保持一致）
    basic_structured = sect.get_structured_info()
    basic_text = sect.get_detailed_info()

    # 2. 使用 SectManager 计算当前势力快照（战力 / 半径 / 势力格 / 冲突）
    sect_manager = SectManager(world)
    # 通过公共接口获取 snapshot，避免在多处重复势力范围逻辑
    snapshot = sect_manager.get_snapshot()
    active_sects = snapshot.active_sects
    tile_owners = snapshot.tile_owners
    sect_centers = snapshot.sect_centers

    # 统计当前本宗占据的格子数与冲突格子数
    tile_count = len(snapshot.owned_tiles_by_sect.get(int(sect.id), []))
    border_tile_count = int(snapshot.border_tiles_by_sect.get(int(sect.id), 0))

    headquarter_center: Optional[tuple[int, int]] = sect_centers.get(sect.id)

    power = {
        "total_battle_strength": float(getattr(sect, "total_battle_strength", 0.0)),
        "influence_radius": int(getattr(sect, "influence_radius", 0)),
    }

    territory = {
        "tile_count": tile_count,
        "border_tile_count": border_tile_count,
        "border_pressure_ratio": (float(border_tile_count) / float(tile_count)) if tile_count > 0 else 0.0,
        # 兼容旧字段，语义改为“与其他宗门接壤的边界压力”。
        "conflict_tile_count": border_tile_count,
        "conflict_ratio": (float(border_tile_count) / float(tile_count)) if tile_count > 0 else 0.0,
        "headquarter_center": headquarter_center,
    }

    # 3. 当前经济能力快照（不修改任何状态，仅基于当前势力格推导）
    sect_conf = getattr(CONFIG, "sect", None)
    base_income = float(getattr(sect_conf, "income_per_tile", 10)) if sect_conf else 10.0
    current_month = int(getattr(world, "month_stamp", 0))
    extra_income = float(sect.get_extra_income_per_tile(current_month))
    effective_income_per_tile = max(0.0, base_income + extra_income)
    controlled_tile_income = float(tile_count) * effective_income_per_tile
    estimated_income_by_sect = sect_manager.calculate_income_by_sect(snapshot)
    estimated_shared_income = int(estimated_income_by_sect.get(int(sect.id), 0.0))
    estimated_member_upkeep, upkeep_breakdown = sect.estimate_yearly_member_upkeep()
    estimated_net_annual_balance = estimated_shared_income - estimated_member_upkeep

    economy = {
        "current_magic_stone": int(getattr(sect, "magic_stone", 0)),
        "effective_income_per_tile": effective_income_per_tile,
        "controlled_tile_income": controlled_tile_income,
        "estimated_shared_income": estimated_shared_income,
        "estimated_member_upkeep": estimated_member_upkeep,
        "estimated_net_annual_balance": estimated_net_annual_balance,
        "member_upkeep_breakdown": list(upkeep_breakdown.values()),
    }

    living_members = [
        avatar
        for avatar in getattr(sect, "members", {}).values()
        if not getattr(avatar, "is_dead", False)
    ]
    recruit_cost = int(getattr(CONFIG.sect, "recruit_cost", 500))
    support_amount = int(getattr(CONFIG.sect, "support_amount", 300))
    current_stones = int(getattr(sect, "magic_stone", 0))
    treasury_pressure = "tight"
    if current_stones < 0 or estimated_net_annual_balance < 0:
        treasury_pressure = "critical"
    elif current_stones >= max(recruit_cost * 2, estimated_member_upkeep + support_amount) and estimated_net_annual_balance >= 0:
        treasury_pressure = "ample"
    elif current_stones >= support_amount and estimated_net_annual_balance >= 0:
        treasury_pressure = "stable"

    economy["treasury_pressure"] = treasury_pressure
    economy["action_cost_notes"] = [
        t(
            "Every successful recruit immediately costs {recruit_cost} spirit stones and increases future yearly member upkeep.",
            recruit_cost=recruit_cost,
        ),
        t(
            "Each support action always costs {support_amount} spirit stones.",
            support_amount=support_amount,
        ),
        t(
            "Granting techniques does not directly spend spirit stones, but it consumes sect inheritance resources; frequent rewards reduce the value and rarity of the sect's scripture collection."
        ),
    ]

    identity = sect.get_identity_summary()
    identity["economic_stance"] = {
        "treasury_pressure": treasury_pressure,
        "current_magic_stone": current_stones,
        "estimated_net_annual_balance": estimated_net_annual_balance,
    }

    peak_member = max(
        living_members,
        key=lambda avatar: int(getattr(getattr(avatar, "cultivation_progress", None), "level", 0) or 0),
        default=None,
    )
    patriarch = next(
        (
            avatar
            for avatar in living_members
            if getattr(getattr(avatar, "sect_rank", None), "value", "") == "patriarch"
        ),
        None,
    )
    self_assessment = {
        "member_count": len(getattr(sect, "members", {})),
        "alive_member_count": len(living_members),
        "peak_member_realm": str(getattr(getattr(peak_member, "cultivation_progress", None), "realm", "") or ""),
        "patriarch_realm": str(getattr(getattr(patriarch, "cultivation_progress", None), "realm", "") or ""),
        "war_readiness": "stretched" if border_tile_count > max(1, tile_count // 3) else "stable",
        "war_weariness": int(getattr(sect, "war_weariness", 0) or 0),
        "resource_pressure": treasury_pressure,
        "can_afford_recruit_count": current_stones // max(1, recruit_cost),
        "can_afford_support_count": current_stones // max(1, support_amount),
    }

    rule = {
        "rule_id": str(getattr(sect, "rule_id", "") or ""),
        "rule_desc": str(getattr(sect, "rule_desc", "") or ""),
    }

    def _technique_grade_rank(avatar) -> int:
        technique = getattr(avatar, "technique", None)
        grade = getattr(technique, "grade", None)
        grade_value = getattr(grade, "value", "")
        order = {"LOWER": 1, "MIDDLE": 2, "UPPER": 3}
        return order.get(str(grade_value), 0)

    def _technique_grade_text(avatar) -> str:
        technique = getattr(avatar, "technique", None)
        grade = getattr(technique, "grade", None)
        return str(grade) if grade is not None else ""

    def _build_governance_summary(avatar) -> Dict[str, Any]:
        recent_events = []
        try:
            recent_events = world.event_manager.get_major_events_by_avatar(
                str(getattr(avatar, "id", "")),
                limit=3,
            )
        except Exception:
            recent_events = []
        return {
            "realm": str(getattr(getattr(avatar, "cultivation_progress", None), "realm", "") or ""),
            "alignment": str(getattr(avatar, "alignment", "") or ""),
            "sect": str(getattr(getattr(avatar, "sect", None), "name", "") or ""),
            "root": str(getattr(avatar, "root", "") or ""),
            "orthodoxy": str(getattr(getattr(avatar, "orthodoxy", None), "name", "") or ""),
            "recent_events": [
                str(getattr(ev, "content", ""))
                for ev in recent_events
                if getattr(ev, "content", "")
            ][:3],
        }

    recruitment_candidates: List[Dict[str, Any]] = []
    member_candidates: List[Dict[str, Any]] = []
    all_avatars = getattr(getattr(world, "avatar_manager", None), "avatars", {}) or {}
    for avatar in all_avatars.values():
        if getattr(avatar, "is_dead", False):
            continue

        avatar_sect = getattr(avatar, "sect", None)
        if avatar_sect is None:
            recruitment_candidates.append(
                {
                    "avatar_id": str(getattr(avatar, "id", "")),
                    "name": str(getattr(avatar, "name", "")),
                    "alignment": str(getattr(avatar, "alignment", "") or ""),
                    "realm": str(getattr(getattr(avatar, "cultivation_progress", None), "realm", "") or ""),
                    "magic_stone": int(getattr(getattr(avatar, "magic_stone", None), "value", 0)),
                    "technique_name": str(getattr(getattr(avatar, "technique", None), "name", "") or ""),
                    "technique_grade": _technique_grade_text(avatar),
                    "technique_grade_rank": _technique_grade_rank(avatar),
                    "alignment_recruitable": bool(sect.is_alignment_recruitable(getattr(avatar, "alignment", None))),
                    "detailed_info": avatar.get_info(detailed=True),
                    "governance_summary": _build_governance_summary(avatar),
                }
            )
            continue

        if avatar_sect != sect:
            continue

        member_candidates.append(
            {
                "avatar_id": str(getattr(avatar, "id", "")),
                "name": str(getattr(avatar, "name", "")),
                "alignment": str(getattr(avatar, "alignment", "") or ""),
                "realm": str(getattr(getattr(avatar, "cultivation_progress", None), "realm", "") or ""),
                "rank": str(getattr(avatar, "get_sect_rank_name", lambda: "")() or ""),
                "magic_stone": int(getattr(getattr(avatar, "magic_stone", None), "value", 0)),
                "technique_name": str(getattr(getattr(avatar, "technique", None), "name", "") or ""),
                "technique_grade": _technique_grade_text(avatar),
                "technique_grade_rank": _technique_grade_rank(avatar),
                "is_rule_breaker": bool(sect.is_member_rule_breaker(avatar)),
                **sect.get_member_status_snapshot(avatar),
                "detailed_info": avatar.get_info(detailed=True),
                "governance_summary": _build_governance_summary(avatar),
            }
        )

    recruitment_candidates.sort(
        key=lambda item: (
            0 if item["alignment_recruitable"] else 1,
            -item["technique_grade_rank"],
            item["magic_stone"],
            item["name"],
        )
    )
    member_candidates.sort(
        key=lambda item: (
            0 if item["is_rule_breaker"] else 1,
            -float(item.get("status_score", 0.0) or 0.0),
            -int(item.get("sect_contribution", 0) or 0),
            -int(item.get("base_battle_strength", 0) or 0),
            item["name"],
        )
    )

    # 4. 当前宗门关系快照
    # 统一使用 SectManager + compute_sect_relations 计算关系数值与理由
    extra_breakdown_by_pair = world.get_active_sect_relation_breakdown(current_month)
    diplomacy_by_pair = world.get_active_sect_diplomacy_breakdown(
        current_month,
        sect_ids=[int(s.id) for s in active_sects],
    )
    relations_raw = compute_sect_relations(
        active_sects,
        tile_owners,
        border_contact_counts=snapshot.border_contact_counts,
        extra_breakdown_by_pair=extra_breakdown_by_pair,
        diplomacy_by_pair=diplomacy_by_pair,
    )

    relations: List[Dict[str, Any]] = []
    diplomacy_targets: List[Dict[str, Any]] = []
    active_wars: List[Dict[str, Any]] = []
    border_contact_by_other_id: Dict[int, int] = {}
    other_sect_by_id = {int(s.id): s for s in active_sects}
    for pair, edge_count in snapshot.border_contact_counts.items():
        if int(sect.id) == int(pair[0]):
            border_contact_by_other_id[int(pair[1])] = int(edge_count)
        elif int(sect.id) == int(pair[1]):
            border_contact_by_other_id[int(pair[0])] = int(edge_count)
    for item in relations_raw:
        sid_a = int(item["sect_a_id"])
        sid_b = int(item["sect_b_id"])
        value = int(item["value"])
        if sect.id == sid_a:
            other_id = sid_b
            other_name = item["sect_b_name"]
        elif sect.id == sid_b:
            other_id = sid_a
            other_name = item["sect_a_name"]
        else:
            continue

        relations.append(
            {
                "other_sect_id": other_id,
                "other_sect_name": other_name,
                "value": value,
                "diplomacy_status": str(item.get("diplomacy_status", "peace") or "peace"),
                "diplomacy_duration_months": int(item.get("diplomacy_duration_months", 0) or 0),
                "reason_breakdown": list(item.get("reason_breakdown", [])),
            }
        )
        diplomacy_state = world.get_sect_diplomacy_state(sect.id, other_id, current_month=current_month)
        diplomacy_target = {
            "other_sect_id": other_id,
            "other_sect_name": other_name,
            "status": str(diplomacy_state.get("status", "peace") or "peace"),
            "war_months": int(diplomacy_state.get("war_months", 0) or 0),
            "peace_months": int(diplomacy_state.get("peace_months", 0) or 0),
            "last_battle_month": diplomacy_state.get("last_battle_month"),
            "war_reason": str(diplomacy_state.get("reason", "") or ""),
            "relation_value": value,
            "border_contact_edges": int(border_contact_by_other_id.get(other_id, 0)),
            "territory_overlap_tiles": int(border_contact_by_other_id.get(other_id, 0)),
            "other_total_battle_strength": float(getattr(other_sect_by_id.get(other_id), "total_battle_strength", 0.0)),
            "power_ratio": float(getattr(sect, "total_battle_strength", 0.0)) / max(
                1.0,
                float(getattr(other_sect_by_id.get(other_id), "total_battle_strength", 0.0)),
            ),
        }
        diplomacy_targets.append(diplomacy_target)
        if diplomacy_target["status"] == "war":
            active_wars.append(diplomacy_target)

    # 简单的关系文字总结：统计友好 / 敌对数量以及最极端的关系
    friendly_count = sum(1 for r in relations if r["value"] >= 20)
    hostile_count = sum(1 for r in relations if r["value"] <= -20)
    neutral_count = len(relations) - friendly_count - hostile_count
    strongest = max(relations, key=lambda r: r["value"], default=None)
    weakest = min(relations, key=lambda r: r["value"], default=None)

    strongest_desc = (
        f"best with {strongest['other_sect_name']}({strongest['value']})"
        if strongest is not None
        else "no_best"
    )
    weakest_desc = (
        f"worst with {weakest['other_sect_name']}({weakest['value']})"
        if weakest is not None
        else "no_worst"
    )

    relations_summary = (
        f"total={len(relations)}, friendly={friendly_count}, "
        f"hostile={hostile_count}, neutral={neutral_count}, "
        f"{strongest_desc}, {weakest_desc}"
    )

    # 5. 历史事件（最近 N 条，与本宗相关）
    # 复用 EventStorage.get_events 的 sect_id 过滤能力，取最近若干条。
    recent_events: List[Any] = []
    if history_limit > 0:
        events, _ = event_storage.get_events(sect_id=int(sect.id), limit=history_limit)
        # get_events 返回按时间倒序（最新在前）；这里保持该顺序即可，
        # 或者根据需要转为时间正序。
        recent_events = list(reversed(events))

    # 将历史事件简单格式化为多行文本，便于 LLM 使用
    lines: List[str] = []
    for ev in recent_events:
        try:
            month_stamp = int(getattr(ev, "month_stamp", 0))
        except Exception:
            month_stamp = 0
        content = str(getattr(ev, "content", ""))
        lines.append(t("[{month_stamp}] {content}", month_stamp=month_stamp, content=content))
    history_summary_text = "\n".join(lines)

    history = {
        "recent_events": recent_events,
        "summary_text": history_summary_text,
    }

    return SectDecisionContext(
        basic_structured=basic_structured,
        basic_text=basic_text,
        power=power,
        territory=territory,
        self_assessment=self_assessment,
        economy=economy,
        rule=rule,
        identity=identity,
        diplomacy_targets=diplomacy_targets,
        active_wars=active_wars,
        recruitment_candidates=recruitment_candidates,
        member_candidates=member_candidates,
        relations=relations,
        relations_summary=relations_summary,
        history=history,
    )

