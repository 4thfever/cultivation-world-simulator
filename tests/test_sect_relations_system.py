import pytest
from pathlib import Path

from src.classes.core.sect import Sect, SectHeadQuarter
from src.classes.alignment import Alignment
from src.systems.sect_relations import (
    SectRelationReason,
    compute_sect_relations,
)


def _make_sect(
    sid: int,
    name: str,
    alignment: Alignment,
    orthodoxy_id: str = "dao",
) -> Sect:
    hq = SectHeadQuarter(name="HQ", desc="", image=Path(""))
    return Sect(
        id=sid,
        name=name,
        desc="",
        member_act_style="",
        alignment=alignment,
        headquarter=hq,
        technique_names=[],
        orthodoxy_id=orthodoxy_id,
    )


def test_compute_sect_relations_alignment_orthodoxy_and_territory():
    """宗门关系数值应综合阵营、道统与势力范围冲突。"""
    sect_a = _make_sect(1, "正道宗", Alignment.RIGHTEOUS, orthodoxy_id="dao")
    sect_b = _make_sect(2, "魔道宗", Alignment.EVIL, orthodoxy_id="dao")

    # 1 个重叠格子
    tile_owners = {
        (0, 0): [1, 2],
        (1, 0): [1],
    }

    relations = compute_sect_relations([sect_a, sect_b], tile_owners)

    assert len(relations) == 1
    rel = relations[0]

    assert rel["sect_a_id"] == 1
    assert rel["sect_b_id"] == 2

    # 期望得分：阵营相反 -40，道统相同 +10，1 个重叠格 -2 => -32
    assert rel["value"] == -32

    reasons = set(rel["reasons"])
    assert SectRelationReason.ALIGNMENT_OPPOSITE.value in reasons
    assert SectRelationReason.ORTHODOXY_SAME.value in reasons
    assert SectRelationReason.TERRITORY_CONFLICT.value in reasons


def test_compute_sect_relations_no_overlap_neutral_alignment():
    """中立或无重叠时，仅由阵营/道统决定关系数值。"""
    sect_a = _make_sect(1, "中立宗一", Alignment.NEUTRAL, orthodoxy_id="dao")
    sect_b = _make_sect(2, "中立宗二", Alignment.NEUTRAL, orthodoxy_id="buddha")

    # 无任何重叠
    tile_owners = {}

    relations = compute_sect_relations([sect_a, sect_b], tile_owners)
    assert len(relations) == 1
    rel = relations[0]

    # 阵营相同 +20，道统不同 -15，总计 +5
    assert rel["value"] == 5

    reasons = set(rel["reasons"])
    assert SectRelationReason.ALIGNMENT_SAME.value in reasons
    assert SectRelationReason.ORTHODOXY_DIFFERENT.value in reasons
    assert SectRelationReason.TERRITORY_CONFLICT.value not in reasons

