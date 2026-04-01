from typing import TYPE_CHECKING, Any, Dict, List

from src.classes.effect import format_effects_to_text
from src.i18n import t
from src.sim.managers.sect_manager import SectManager
from src.systems.sect_relations import compute_sect_relations
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.core.sect import Sect
    from src.classes.core.world import World


def _sect_runtime_source_label(source: str, language_manager: object) -> str:
    """
    根据当前语言返回运行时宗门效果来源的可读标签。
    逻辑与 /api/detail 中 sect 分支保持一致。
    """
    key = (source or "").strip().lower()

    if key == "base":
        return t("Base effect")
    if key == "sect_random_event":
        return t("Sect random event")
    return source or t("Temporary effect")


def build_sect_detail(sect: "Sect", world: "World", language_manager: object) -> Dict[str, Any]:
    """
    组装宗门详情的完整结构化信息。

    - 基础字段来自 sect.get_structured_info()
    - 运行时效果字段与 /api/detail 现有实现保持完全一致
    """
    # 1. 先获取领域层提供的基础信息
    info: Dict[str, Any] = sect.get_structured_info()

    # 2. 拼接运行时效果信息（与原 /api/detail 保持等价）
    current_month = int(getattr(world, "month_stamp", 0))
    runtime_items: List[Dict[str, Any]] = []

    base_runtime_effects = dict(getattr(sect, "sect_effects", {}) or {})
    if base_runtime_effects:
        base_desc = format_effects_to_text(base_runtime_effects).strip()
        if base_desc:
            runtime_items.append(
                {
                    "source": "base",
                    "source_label": _sect_runtime_source_label("base", language_manager),
                    "desc": base_desc,
                    "remaining_months": -1,
                    "is_permanent": True,
                }
            )

    for temp in sect.get_active_temporary_sect_effects(current_month):
        effects = dict(temp.get("effects", {}) or {})
        if not effects:
            continue

        desc = format_effects_to_text(effects).strip()
        if not desc:
            continue

        start_month = int(temp.get("start_month", current_month))
        duration = max(0, int(temp.get("duration", 0)))
        remaining_months = max(0, start_month + duration - current_month)
        source = str(temp.get("source", "temporary") or "temporary")

        runtime_items.append(
            {
                "source": source,
                "source_label": _sect_runtime_source_label(source, language_manager),
                "desc": desc,
                "remaining_months": remaining_months,
                "is_permanent": False,
            }
        )

    active_effects = sect.get_sect_effects(current_month)
    info["runtime_effect_desc"] = (
        format_effects_to_text(active_effects).strip() if active_effects else ""
    )
    sect_conf = getattr(CONFIG, "sect", None)
    base_income = float(getattr(sect_conf, "income_per_tile", 10)) if sect_conf else 10.0
    info["runtime_extra_income_per_tile"] = float(
        sect.get_extra_income_per_tile(current_month)
    )
    info["runtime_effects_count"] = len(runtime_items)
    info["runtime_effect_items"] = runtime_items
    info["periodic_thinking"] = str(getattr(sect, "periodic_thinking", "") or "")
    info["war_weariness"] = int(getattr(sect, "war_weariness", 0) or 0)
    # 兼容旧字段，前端迁移完成后可删除。
    info["yearly_thinking"] = info["periodic_thinking"]

    sect_manager = SectManager(world)
    snapshot = sect_manager.get_snapshot()
    tile_count = len(snapshot.owned_tiles_by_sect.get(int(sect.id), []))
    border_tile_count = int(snapshot.border_tiles_by_sect.get(int(sect.id), 0))

    effective_income_per_tile = max(
        0.0,
        base_income + float(sect.get_extra_income_per_tile(current_month)),
    )
    estimated_income_by_sect = sect_manager.calculate_income_by_sect(snapshot)
    estimated_yearly_income = int(estimated_income_by_sect.get(int(sect.id), 0.0))
    estimated_yearly_upkeep, _ = sect.estimate_yearly_member_upkeep()
    info["territory_summary"] = {
        "tile_count": tile_count,
        "border_tile_count": border_tile_count,
        "border_pressure_ratio": (float(border_tile_count) / float(tile_count)) if tile_count > 0 else 0.0,
        # 兼容旧字段。
        "conflict_tile_count": border_tile_count,
        "headquarter_center": snapshot.sect_centers.get(int(sect.id)),
    }
    info["economy_summary"] = {
        "current_magic_stone": int(getattr(sect, "magic_stone", 0)),
        "effective_income_per_tile": effective_income_per_tile,
        "controlled_tile_income": float(tile_count) * effective_income_per_tile,
        "estimated_yearly_income": estimated_yearly_income,
        "estimated_yearly_upkeep": estimated_yearly_upkeep,
    }

    extra_breakdown_by_pair = world.get_active_sect_relation_breakdown(current_month)
    diplomacy_by_pair = world.get_active_sect_diplomacy_breakdown(
        current_month,
        sect_ids=[int(s.id) for s in snapshot.active_sects],
    )
    relations_raw = compute_sect_relations(
        snapshot.active_sects,
        snapshot.tile_owners,
        border_contact_counts=snapshot.border_contact_counts,
        extra_breakdown_by_pair=extra_breakdown_by_pair,
        diplomacy_by_pair=diplomacy_by_pair,
    )
    relation_by_other_id: Dict[int, Dict[str, Any]] = {}
    for item in relations_raw:
        if int(item["sect_a_id"]) == int(sect.id):
            relation_by_other_id[int(item["sect_b_id"])] = item
        elif int(item["sect_b_id"]) == int(sect.id):
            relation_by_other_id[int(item["sect_a_id"])] = item

    sect_context = getattr(world, "sect_context", None)
    active_sects = (
        sect_context.get_active_sects()
        if sect_context is not None
        else (getattr(world, "existed_sects", []) or [])
    )
    diplomacy_items: List[Dict[str, Any]] = []
    current_month = int(getattr(world, "month_stamp", 0))
    active_war_count = 0
    strongest_enemy_name = ""
    strongest_enemy_relation = 0
    for other in active_sects:
        if other is None or int(getattr(other, "id", 0)) == int(getattr(sect, "id", 0)):
            continue
        state = world.get_sect_diplomacy_state(int(sect.id), int(other.id), current_month=current_month)
        relation_item = relation_by_other_id.get(int(other.id), {})
        relation_value = int(relation_item.get("value", 0) or 0)
        if str(state.get("status", "peace") or "peace") == "war":
            active_war_count += 1
        if relation_value < strongest_enemy_relation:
            strongest_enemy_relation = relation_value
            strongest_enemy_name = str(getattr(other, "name", "") or "")
        reason_breakdown = list(relation_item.get("reason_breakdown", []))
        reason_summary = " / ".join(
            f"{item.get('reason', '')}:{int(item.get('delta', 0))}"
            for item in reason_breakdown[:4]
            if item.get("reason")
        )
        diplomacy_items.append(
            {
                "other_sect_id": int(other.id),
                "other_sect_name": str(getattr(other, "name", "") or ""),
                "status": str(state.get("status", "peace") or "peace"),
                "duration_months": int(
                    state.get("war_months", state.get("peace_months", 0)) or 0
                ),
                "war_months": int(state.get("war_months", 0) or 0),
                "peace_months": int(state.get("peace_months", 0) or 0),
                "relation_value": relation_value,
                "war_reason": str(state.get("reason", "") or ""),
                "last_battle_month": state.get("last_battle_month"),
                "reason_summary": reason_summary,
            }
        )
    info["diplomacy_items"] = diplomacy_items
    info["war_summary"] = {
        "active_war_count": active_war_count,
        "peace_count": max(0, len(diplomacy_items) - active_war_count),
        "strongest_enemy_name": strongest_enemy_name,
        "strongest_enemy_relation": strongest_enemy_relation,
    }

    return info

