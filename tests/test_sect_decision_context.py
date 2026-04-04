import tempfile
from pathlib import Path

from src.classes.core.world import World
from src.classes.core.sect import Sect, SectHeadQuarter
from src.classes.alignment import Alignment
from src.classes.event import Event
from src.classes.event_storage import EventStorage
from src.classes.language import language_manager
from src.i18n import reload_translations
from src.sim.managers.sect_manager import SectManager
from src.systems.time import MonthStamp
from src.systems.sect_decision_context import build_sect_decision_context, SectDecisionContext


def _create_world_with_sects(base_world: World) -> tuple[World, Sect, Sect]:
    """
    基于标准 base_world 构造一个带有两个宗门和宗门总部区域的世界。

    - sect1：有总部区域，用于产生势力范围与收入；
    - sect2：无总部区域，仅用于关系计算。
    """
    world: World = base_world
    game_map = world.map

    # 为 sect1 注册一个 SectRegion，使其拥有总部中心与势力范围
    from src.classes.environment.sect_region import SectRegion

    r1_id = 1001
    cors1 = [(0, 0)]
    r1 = SectRegion(id=r1_id, name="R1", desc="", sect_id=1, sect_name="测试宗门1", cors=cors1)
    game_map.regions[r1_id] = r1
    game_map.region_cors[r1_id] = cors1
    game_map.update_sect_regions()

    hq = SectHeadQuarter(name="测试驻地", desc="", image=Path(""))
    sect1 = Sect(
        id=1,
        name="测试宗门1",
        desc="",
        member_act_style="",
        alignment=Alignment.NEUTRAL,
        headquarter=hq,
        technique_names=[],
    )
    sect2 = Sect(
        id=2,
        name="测试宗门2",
        desc="",
        member_act_style="",
        alignment=Alignment.EVIL,
        headquarter=hq,
        technique_names=[],
    )

    world.existed_sects = [sect1, sect2]
    world.sect_context.from_existed_sects(world.existed_sects)

    return world, sect1, sect2


def _create_event_storage_with_sect_events(sect_id: int) -> EventStorage:
    """创建一个临时 EventStorage，并写入几条与指定宗门相关的事件。"""
    tmpdir = tempfile.TemporaryDirectory()
    db_path = Path(tmpdir.name) / "sect_events.db"
    storage = EventStorage(db_path)

    # 三条事件，按 month_stamp 递增
    e1 = Event(month_stamp=MonthStamp(1), content="E1", related_sects=[sect_id])
    e2 = Event(month_stamp=MonthStamp(2), content="E2", related_sects=[sect_id])
    e3 = Event(month_stamp=MonthStamp(3), content="E3", related_sects=[sect_id])
    for ev in (e1, e2, e3):
        storage.add_event(ev)

    # 将临时目录挂到实例上，便于测试结束后手动清理
    storage._tmpdir = tmpdir  # type: ignore[attr-defined]
    return storage


def _cleanup_event_storage(storage: EventStorage) -> None:
    """关闭并清理临时 EventStorage。"""
    tmpdir = getattr(storage, "_tmpdir", None)
    storage.close()
    if tmpdir is not None:
        tmpdir.cleanup()


def test_build_sect_decision_context_basic(base_world):
    """基础快照：应包含静态信息、当前战力/势力、经济与历史事件。"""
    world, sect1, sect2 = _create_world_with_sects(base_world)

    # 先跑一遍 update_sects，使战力、半径和收入为最新
    manager = SectManager(world)
    manager.update_sects()

    storage = _create_event_storage_with_sect_events(sect1.id)
    try:
        ctx = build_sect_decision_context(sect1, world, storage, history_limit=2)
    finally:
        _cleanup_event_storage(storage)

    assert isinstance(ctx, SectDecisionContext)

    # 基础信息
    assert ctx.basic_structured["name"] == sect1.name
    assert sect1.name in ctx.basic_text

    # 势力与战力：应与当前 sect 字段保持一致，且至少有半径
    assert ctx.power["influence_radius"] == sect1.influence_radius
    assert ctx.power["total_battle_strength"] == sect1.total_battle_strength
    assert ctx.territory["tile_count"] >= 0

    # 经济信息：只读当前字段与基于势力格推导出的收入能力
    assert ctx.economy["current_magic_stone"] == sect1.magic_stone
    assert ctx.economy["effective_income_per_tile"] >= 0.0
    assert ctx.economy["controlled_tile_income"] == ctx.economy["effective_income_per_tile"] * ctx.territory["tile_count"]
    assert "estimated_member_upkeep" in ctx.economy
    assert "estimated_net_annual_balance" in ctx.economy
    assert "treasury_pressure" in ctx.economy
    assert isinstance(ctx.economy["member_upkeep_breakdown"], list)
    assert ctx.rule["rule_id"] == ""
    assert ctx.identity["purpose"] == sect1.desc
    assert ctx.identity["rule_desc"] == sect1.rule_desc
    assert ctx.self_assessment["war_weariness"] == 0
    assert isinstance(ctx.recruitment_candidates, list)
    assert isinstance(ctx.member_candidates, list)

    # 历史事件：只保留最近 N 条
    recent = ctx.history["recent_events"]
    assert len(recent) == 2
    # 最新两条应是 month_stamp 为 2 和 3 的事件
    stamps = [int(e.month_stamp) for e in recent]
    assert stamps == [2, 3]
    summary = ctx.history["summary_text"]
    assert "E2" in summary and "E3" in summary


def test_build_sect_decision_context_relations(base_world):
    """关系快照：应包含与其他宗门的当前关系信息。"""
    world, sect1, sect2 = _create_world_with_sects(base_world)

    manager = SectManager(world)
    manager.update_sects()

    storage = _create_event_storage_with_sect_events(sect1.id)
    try:
        ctx = build_sect_decision_context(sect1, world, storage, history_limit=0)
    finally:
        _cleanup_event_storage(storage)

    # 至少应包含与 sect2 的一条关系记录
    others = {r["other_sect_id"] for r in ctx.relations}
    assert sect2.id in others

    # 关系值应在 [-100, 100] 区间
    for r in ctx.relations:
        assert -100 <= r["value"] <= 100

    # relations_summary 至少应包含总数信息
    assert f"total={len(ctx.relations)}" in ctx.relations_summary
    assert isinstance(ctx.diplomacy_targets, list)
    assert ctx.diplomacy_targets
    assert ctx.diplomacy_targets[0]["status"] in {"war", "peace"}


def test_build_sect_decision_context_localizes_runtime_notes(base_world):
    world, sect1, _ = _create_world_with_sects(base_world)

    manager = SectManager(world)
    manager.update_sects()

    storage = _create_event_storage_with_sect_events(sect1.id)
    original_lang = str(language_manager)
    try:
        language_manager._current = "en-US"
        reload_translations()
        ctx = build_sect_decision_context(sect1, world, storage, history_limit=1)
    finally:
        _cleanup_event_storage(storage)
        language_manager._current = original_lang
        reload_translations()

    assert ctx.economy["action_cost_notes"]
    assert all("灵石" not in note for note in ctx.economy["action_cost_notes"])
    assert "spirit stones" in ctx.economy["action_cost_notes"][0]
    assert "[3] E3" in ctx.history["summary_text"]

