from __future__ import annotations

from enum import Enum
from typing import Dict, Iterable, List, Tuple

from src.classes.core.sect import Sect


class SectRelationReason(str, Enum):
    ALIGNMENT_OPPOSITE = "ALIGNMENT_OPPOSITE"
    ALIGNMENT_SAME = "ALIGNMENT_SAME"
    ORTHODOXY_DIFFERENT = "ORTHODOXY_DIFFERENT"
    ORTHODOXY_SAME = "ORTHODOXY_SAME"
    TERRITORY_CONFLICT = "TERRITORY_CONFLICT"


def _clamp(value: int, min_value: int, max_value: int) -> int:
    return max(min_value, min(max_value, value))


def _compute_pair_score(a: Sect, b: Sect, overlap_tiles: int) -> Tuple[int, List[SectRelationReason]]:
    """
    计算一对宗门之间的关系数值与理由。
    数值范围：-100 ~ 100。
    构成要素：
        - 阵营：正邪相对 -40，同阵营 +20，中立相关 0。
        - 道统：相同 +10，不同 -15。
        - 势力范围冲突：每个重叠格 -2，最多 -30。
    """
    from src.classes.alignment import Alignment

    score = 0
    reasons: List[SectRelationReason] = []

    # 阵营
    align_a = getattr(a, "alignment", None)
    align_b = getattr(b, "alignment", None)
    if align_a is not None and align_b is not None:
        if ((align_a == Alignment.RIGHTEOUS and align_b == Alignment.EVIL) or
                (align_a == Alignment.EVIL and align_b == Alignment.RIGHTEOUS)):
            score -= 40
            reasons.append(SectRelationReason.ALIGNMENT_OPPOSITE)
        elif align_a == align_b:
            score += 20
            reasons.append(SectRelationReason.ALIGNMENT_SAME)

    # 道统
    orth_a = getattr(a, "orthodoxy_id", "") or ""
    orth_b = getattr(b, "orthodoxy_id", "") or ""
    if orth_a and orth_b:
        if orth_a == orth_b:
            score += 10
            reasons.append(SectRelationReason.ORTHODOXY_SAME)
        else:
            score -= 15
            reasons.append(SectRelationReason.ORTHODOXY_DIFFERENT)

    # 势力范围冲突（线性）
    if overlap_tiles > 0:
        penalty = min(overlap_tiles * 2, 30)
        score -= penalty
        reasons.append(SectRelationReason.TERRITORY_CONFLICT)

    score = _clamp(int(score), -100, 100)
    return score, reasons


def compute_sect_relations(
    sects: Iterable[Sect],
    tile_owners: Dict[Tuple[int, int], List[int]],
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
            "reasons": list[str],        # SectRelationReason 枚举的 value
        }
    """
    sect_list = [s for s in sects if s is not None]
    if len(sect_list) < 2:
        return []

    # 预建 id -> sect 映射，避免后续多次遍历
    sect_by_id: Dict[int, Sect] = {int(s.id): s for s in sect_list}

    # 统计每对宗门之间的重叠格数
    overlap_counts: Dict[Tuple[int, int], int] = {}
    for owners in tile_owners.values():
        # 只保留在 sect_by_id 中存在且去重后的 ID
        unique_ids = sorted({int(sid) for sid in owners if sid in sect_by_id})
        if len(unique_ids) < 2:
            continue
        for i in range(len(unique_ids)):
            for j in range(i + 1, len(unique_ids)):
                key = (unique_ids[i], unique_ids[j])
                overlap_counts[key] = overlap_counts.get(key, 0) + 1

    results: List[dict] = []

    # 遍历所有两两组合
    ids = sorted(sect_by_id.keys())
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            sid_a = ids[i]
            sid_b = ids[j]
            sect_a = sect_by_id[sid_a]
            sect_b = sect_by_id[sid_b]

            overlap = overlap_counts.get((sid_a, sid_b), 0)
            value, reasons = _compute_pair_score(sect_a, sect_b, overlap)

            results.append(
                {
                    "sect_a_id": sid_a,
                    "sect_a_name": sect_a.name,
                    "sect_b_id": sid_b,
                    "sect_b_name": sect_b.name,
                    "value": value,
                    "reasons": [r.value for r in reasons],
                }
            )

    return results

