from __future__ import annotations

from enum import Enum
from typing import Dict, Iterable, List, Tuple

from src.classes.core.sect import Sect
from src.utils.config import CONFIG


class SectRelationReason(str, Enum):
    ALIGNMENT_OPPOSITE = "ALIGNMENT_OPPOSITE"
    ALIGNMENT_SAME = "ALIGNMENT_SAME"
    ORTHODOXY_DIFFERENT = "ORTHODOXY_DIFFERENT"
    ORTHODOXY_SAME = "ORTHODOXY_SAME"
    TERRITORY_CONFLICT = "TERRITORY_CONFLICT"
    WAR_STATE = "WAR_STATE"
    PEACE_STATE = "PEACE_STATE"
    LONG_PEACE = "LONG_PEACE"
    RANDOM_EVENT = "RANDOM_EVENT"


def _clamp(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(max_value, value))


def _compute_pair_score(a: Sect, b: Sect, border_contact_edges: int) -> Tuple[int, List[dict]]:
    """
    计算一对宗门之间的关系数值与理由。
    数值范围：-100 ~ 100。
    构成要素：
        - 阵营：正邪相对 -40，同阵营 +20，中立相关 0。
        - 道统：相同 +10，不同 -15。
        - 势力边界接触：接壤越密集，关系越紧张。
    """
    from src.classes.alignment import Alignment

    score = 0
    breakdown: List[dict] = []

    # 阵营
    align_a = getattr(a, "alignment", None)
    align_b = getattr(b, "alignment", None)
    if align_a is not None and align_b is not None:
        if ((align_a == Alignment.RIGHTEOUS and align_b == Alignment.EVIL) or
                (align_a == Alignment.EVIL and align_b == Alignment.RIGHTEOUS)):
            score -= 40
            breakdown.append(
                {
                    "reason": SectRelationReason.ALIGNMENT_OPPOSITE.value,
                    "delta": -40,
                }
            )
        elif align_a == align_b:
            score += 20
            breakdown.append(
                {
                    "reason": SectRelationReason.ALIGNMENT_SAME.value,
                    "delta": 20,
                }
            )

    # 道统
    orth_a = getattr(a, "orthodoxy_id", "") or ""
    orth_b = getattr(b, "orthodoxy_id", "") or ""
    if orth_a and orth_b:
        if orth_a == orth_b:
            score += 10
            breakdown.append(
                {
                    "reason": SectRelationReason.ORTHODOXY_SAME.value,
                    "delta": 10,
                }
            )
        else:
            score -= 15
            breakdown.append(
                {
                    "reason": SectRelationReason.ORTHODOXY_DIFFERENT.value,
                    "delta": -15,
                }
            )

    # 势力范围冲突（线性）
    if border_contact_edges > 0:
        sect_conf = getattr(CONFIG, "sect", None)
        dense_threshold = int(getattr(sect_conf, "territory_dense_border_threshold", 8)) if sect_conf else 8
        penalty = min(border_contact_edges, 24)
        if border_contact_edges >= dense_threshold:
            penalty += min(8, max(1, border_contact_edges // max(1, dense_threshold)))
        score -= penalty
        breakdown.append(
            {
                "reason": SectRelationReason.TERRITORY_CONFLICT.value,
                "delta": -penalty,
                "meta": {
                    "border_contact_edges": border_contact_edges,
                    # 兼容旧前端/旧提示词的字段名，语义上已退化为“边界接触强度”。
                    "overlap_tiles": border_contact_edges,
                },
            }
        )

    score = _clamp(int(score), -100, 100)
    return score, breakdown


def compute_sect_relations(
    sects: Iterable[Sect],
    tile_owners: Dict[Tuple[int, int], List[int]],
    border_contact_counts: Dict[Tuple[int, int], int] | None = None,
    extra_breakdown_by_pair: Dict[Tuple[int, int], List[dict]] | None = None,
    diplomacy_by_pair: Dict[Tuple[int, int], List[dict]] | None = None,
) -> List[dict]:
    """
    计算一组宗门之间的关系。

    Args:
        sects: 需要计算的宗门列表（建议只传 active 宗门）。
        tile_owners: 地图中每个格子被哪些宗门占据的映射。

    Returns:
        列表，每项结构：
        {
            "sect_a_id": int,
            "sect_a_name": str,
            "sect_b_id": int,
            "sect_b_name": str,
            "value": int,                # -100 ~ 100
            "reason_breakdown": list[dict],   # 每条包含 reason / delta / meta
        }
    """
    sect_list = [s for s in sects if s is not None]
    if len(sect_list) < 2:
        return []

    # 预建 id -> sect 映射，避免后续多次遍历
    sect_by_id: Dict[int, Sect] = {int(s.id): s for s in sect_list}

    if border_contact_counts is None:
        border_contact_counts = {}
        for (x, y), owners in tile_owners.items():
            if not owners:
                continue
            owner_id = int(owners[0])
            if owner_id not in sect_by_id:
                continue
            for dx, dy in ((1, 0), (0, 1)):
                neighbor_owners = tile_owners.get((x + dx, y + dy), [])
                if not neighbor_owners:
                    continue
                neighbor_id = int(neighbor_owners[0])
                if neighbor_id == owner_id or neighbor_id not in sect_by_id:
                    continue
                key = (owner_id, neighbor_id) if owner_id < neighbor_id else (neighbor_id, owner_id)
                border_contact_counts[key] = border_contact_counts.get(key, 0) + 1

    results: List[dict] = []

    # 遍历所有两两组合
    ids = sorted(sect_by_id.keys())
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            sid_a = ids[i]
            sid_b = ids[j]
            sect_a = sect_by_id[sid_a]
            sect_b = sect_by_id[sid_b]

            border_contact_edges = border_contact_counts.get((sid_a, sid_b), 0)
            value, reason_breakdown = _compute_pair_score(sect_a, sect_b, border_contact_edges)
            for extra_item in (extra_breakdown_by_pair or {}).get((sid_a, sid_b), []):
                delta = int(extra_item.get("delta", 0))
                value += delta
                reason_breakdown.append(
                    {
                        "reason": str(extra_item.get("reason", SectRelationReason.RANDOM_EVENT.value)),
                        "delta": delta,
                        "meta": dict(extra_item.get("meta", {}) or {}),
                    }
                )
            diplomacy_items = (diplomacy_by_pair or {}).get((sid_a, sid_b), [])
            diplomacy_status = "peace"
            diplomacy_duration_months = 0
            for diplomacy_item in diplomacy_items:
                delta = int(diplomacy_item.get("delta", 0))
                value += delta
                meta = dict(diplomacy_item.get("meta", {}) or {})
                if meta.get("status") in {"war", "peace"}:
                    diplomacy_status = str(meta["status"])
                    diplomacy_duration_months = int(
                        meta.get("war_months", meta.get("peace_months", 0)) or 0
                    )
                reason_breakdown.append(
                    {
                        "reason": str(diplomacy_item.get("reason", SectRelationReason.PEACE_STATE.value)),
                        "delta": delta,
                        "meta": meta,
                    }
                )
            value = _clamp(int(value), -100, 100)

            results.append(
                {
                    "sect_a_id": sid_a,
                    "sect_a_name": sect_a.name,
                    "sect_b_id": sid_b,
                    "sect_b_name": sect_b.name,
                    "value": value,
                    "diplomacy_status": diplomacy_status,
                    "diplomacy_duration_months": diplomacy_duration_months,
                    "reason_breakdown": reason_breakdown,
                }
            )

    return results

