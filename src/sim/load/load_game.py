"""
读档功能模块

主要功能：
- load_game: 从JSON文件加载游戏完整状态
- get_events_db_path: 根据存档路径计算事件数据库路径
- check_save_compatibility: 检查存档版本兼容性（当前未实现严格检查）

加载流程（两阶段）：
1. 第一阶段：加载所有Avatar对象（relations留空）
   - 通过AvatarLoadMixin.from_save_dict反序列化
   - 配表对象（Technique, Material等）通过id从全局字典获取
2. 第二阶段：重建Avatar之间的relations网络
   - 必须在所有Avatar加载完成后才能建立引用关系
   
错误容错：
- 缺失的配表对象引用会被跳过（如删除的Item）
- 无法重建的动作会被置为None
- 不存在的Avatar引用会被忽略

事件存储：
- 事件存储在 SQLite 数据库中（{save_name}_events.db）
- 旧存档的 JSON 事件会自动迁移到 SQLite

注意事项：
- 读档后会重置前端UI状态（头像图像、插值等）
- 地图从头重建（因为地图是固定的），但会恢复宗门总部位置
"""
import json
from pathlib import Path
from typing import Tuple, List, Optional, TYPE_CHECKING
import src.utils.config as app_config

if TYPE_CHECKING:
    from src.classes.core.world import World
    from src.sim.simulator import Simulator
    from src.classes.core.sect import Sect

from src.systems.time import MonthStamp
from src.classes.custom_content import CustomContentRegistry
from src.classes.event import Event
from src.classes.relation.relation import RelationState
from src.classes.world_lore_snapshot import apply_world_lore_snapshot
from src.config import get_settings_service
from src.utils.config import CONFIG


def get_events_db_path(save_path: Path) -> Path:
    """
    根据存档路径计算事件数据库路径。

    例如：save_20260105_1423.json -> save_20260105_1423_events.db
    """
    return save_path.with_suffix("").with_name(save_path.stem + "_events.db")


def _get_current_saves_dir() -> Path:
    return Path(app_config.CONFIG.paths.saves)


def load_game(save_path: Optional[Path] = None) -> Tuple["World", "Simulator", List["Sect"]]:
    """
    从文件加载游戏状态
    
    Args:
        save_path: 存档路径，默认为saves/save.json
        
    Returns:
        (world, simulator, existed_sects)
        
    Raises:
        FileNotFoundError: 如果存档文件不存在
        Exception: 如果加载失败
    """
    # 确定加载路径
    if save_path is None:
        saves_dir = _get_current_saves_dir()
        save_path = saves_dir / "save.json"
    else:
        save_path = Path(save_path)
    
    if not save_path.exists():
        raise FileNotFoundError(f"存档文件不存在: {save_path}")
    
    try:
        # 运行时导入，避免循环依赖
        from src.classes.core.world import World
        from src.classes.core.avatar import Avatar
        from src.classes.core.dynasty import Dynasty
        from src.classes.core.sect import sects_by_id
        from src.sim.simulator import Simulator
        from src.run.load_map import load_cultivation_world_map
        
        # 读取存档文件
        with open(save_path, "r", encoding="utf-8") as f:
            save_data = json.load(f)
        
        # 读取元信息
        meta = save_data.get("meta", {})
        print(f"Loading save (Version: {meta.get('version', 'unknown')}, "
              f"游戏时间: {meta.get('game_time', 'unknown')})")
        
        # 重建地图（地图本身不变，只需重建宗门总部位置）
        game_map = load_cultivation_world_map()
        
        # 读取世界数据
        world_data = save_data.get("world", {})
        month_stamp = MonthStamp(world_data["month_stamp"])
        start_year = world_data.get("start_year", 100)
        
        # 计算事件数据库路径。
        events_db_path = get_events_db_path(save_path)

        # 重建World对象（使用 SQLite 事件存储）。
        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=events_db_path,
            start_year=start_year,
        )
        CustomContentRegistry.load_from_dict(save_data.get("custom_content"))
        dynasty_data = world_data.get("dynasty")
        if dynasty_data is not None:
            world.dynasty = Dynasty.from_dict(dynasty_data)
        
        # 恢复 playthrough_id (如果旧存档没有，这里就保留默认生成的 uuid)
        if "playthrough_id" in meta:
            world.playthrough_id = meta["playthrough_id"]
        
        # 恢复本局世界观与历史输入
        world_lore_data = world_data.get("world_lore", {})
        world.world_lore.text = world_lore_data.get("text", "")
        world.world_lore_snapshot = world_data.get("world_lore_snapshot", {}) or {}
        apply_world_lore_snapshot(world, world.world_lore_snapshot)
        
        # 重建天地灵机
        from src.classes.celestial_phenomenon import celestial_phenomena_by_id
        phenomenon_id = world_data.get("current_phenomenon_id")
        if phenomenon_id is not None and phenomenon_id in celestial_phenomena_by_id:
            world.current_phenomenon = celestial_phenomena_by_id[phenomenon_id]
            world.phenomenon_start_year = world_data.get("phenomenon_start_year", 0)
            
        # 恢复出世物品流转
        circulation_data = world_data.get("circulation", {})
        world.circulation.load_from_dict(circulation_data)
        
        # 获取本局启用的宗门
        existed_sect_ids = world_data.get("existed_sect_ids", [])
        existed_sects = [sects_by_id[sid] for sid in existed_sect_ids if sid in sects_by_id]

        world.sect_relation_modifiers = list(world_data.get("sect_relation_modifiers", []) or [])
        world.prune_expired_sect_relation_modifiers(int(world.month_stamp))
        world.sect_wars = list(world_data.get("sect_wars", []) or [])

        for sect in sects_by_id.values():
            sect.magic_stone = 0
            sect.is_active = True
            sect.periodic_thinking = ""
            sect.last_decision_summary = ""
            sect.sect_effects = {}
            sect.temporary_sect_effects = []
            sect.set_war_weariness(0)

        sect_runtime_states = (
            world_data.get("sect_runtime_states", {})
            or world_data.get("sect_runtime_effects", {})
        )
        for sid_key, state in (sect_runtime_states or {}).items():
            try:
                sid = int(sid_key)
            except (TypeError, ValueError):
                continue
            sect = sects_by_id.get(sid)
            if sect is None:
                continue
            state_dict = state if isinstance(state, dict) else {}
            sect.magic_stone = int(state_dict.get("magic_stone", 0) or 0)
            sect.is_active = bool(state_dict.get("is_active", True))
            sect.periodic_thinking = str(state_dict.get("periodic_thinking", "") or "")
            sect.last_decision_summary = str(state_dict.get("last_decision_summary", "") or "")
            sect.sect_effects = dict(state_dict.get("sect_effects", {}) or {})
            sect.temporary_sect_effects = list(state_dict.get("temporary_sect_effects", []) or [])
            sect.set_war_weariness(state_dict.get("war_weariness", 0))
            sect.cleanup_expired_temporary_sect_effects(int(world.month_stamp))
        
        # 第一阶段：重建所有Avatar（不含relations）
        avatars_data = save_data.get("avatars", [])
        all_avatars = {}
        living_avatars = {}
        dead_avatars = {}

        for avatar_data in avatars_data:
            avatar = Avatar.from_save_dict(avatar_data, world)
            all_avatars[avatar.id] = avatar
            
            # 分流：生者与死者
            if avatar.is_dead:
                dead_avatars[avatar.id] = avatar
            else:
                living_avatars[avatar.id] = avatar
        
        # 第二阶段：重建relations（需要所有avatar都已加载）
        for avatar_data in avatars_data:
            avatar_id = avatar_data["id"]
            avatar = all_avatars[avatar_id]
            relations_dict = avatar_data.get("relations", {})
            
            for other_id, relation_state_data in relations_dict.items():
                if other_id in all_avatars:
                    other_avatar = all_avatars[other_id]
                    avatar.relations[other_avatar] = RelationState.from_save_dict(relation_state_data)
        
        # 将所有avatar添加到world
        world.avatar_manager.avatars = living_avatars
        world.avatar_manager.dead_avatars = dead_avatars
        
        # 恢复洞府主人关系
        cultivate_regions_hosts = world_data.get("cultivate_regions_hosts", {})
        regions_status = world_data.get("regions_status", {})
        
        from src.classes.environment.region import CultivateRegion, CityRegion
        for rid_str, avatar_id in cultivate_regions_hosts.items():
            rid = int(rid_str)
            if rid in game_map.regions:
                region = game_map.regions[rid]
                if isinstance(region, CultivateRegion) and avatar_id in all_avatars:
                    avatar = all_avatars[avatar_id]
                    # 使用 occupy_region 建立双向绑定
                    avatar.occupy_region(region)
        
        # 恢复区域状态 (如城市人口)
        for rid_str, status in regions_status.items():
            rid = int(rid_str)
            if rid in game_map.regions:
                region = game_map.regions[rid]
                if isinstance(region, CityRegion):
                    region.population = status.get("population", region.population)
        
        # 重建宗门成员关系与功法列表
        from src.classes.technique import techniques_by_name
        
        # 1. 重建成员
        for avatar in all_avatars.values():
            if avatar.sect:
                # 存档中 avatar.sect 已经被 Avatar.from_save_dict 恢复为 Sect 对象引用
                # 但 Sect.members 是空的（因为 Sect 是重新加载配置生成的）
                avatar.sect.add_member(avatar)
        
        # 2. 重建功法对象列表（兼容旧存档）
        for sect in existed_sects:
            if not sect.techniques and sect.technique_names:
                sect.techniques = []
                for t_name in sect.technique_names:
                    if t_name in techniques_by_name:
                        sect.techniques.append(techniques_by_name[t_name])

        # 使用 SectContext 统一本局宗门作用域
        world.existed_sects = existed_sects
        world.sect_context.from_existed_sects(existed_sects)

        # 检查是否需要从 JSON 迁移事件（向后兼容旧存档）。
        db_event_count = world.event_manager.count()
        events_data = save_data.get("events", [])

        if db_event_count == 0 and len(events_data) > 0:
            # SQLite 数据库是空的，但 JSON 中有事件，执行迁移。
            print(f"Migrating {len(events_data)} events from JSON to SQLite...")
            for event_data in events_data:
                event = Event.from_dict(event_data)
                world.event_manager.add_event(event)
            print("Event migration completed")
        else:
            print(f"Loaded {db_event_count} events from SQLite")

        # 重建Simulator
        simulator_data = save_data.get("simulator", {})
        run_config_snapshot = save_data.get("run_config", _model_to_dict(get_settings_service().get_default_run_config()))
        world.run_config_snapshot = run_config_snapshot
        simulator = Simulator(world)
        # 兼容旧存档 "birth_rate"
        simulator.awakening_rate = simulator_data.get(
            "awakening_rate",
            simulator_data.get("birth_rate", run_config_snapshot.get("npc_awakening_rate_per_month", CONFIG.game.npc_awakening_rate_per_month))
        )
        
        print(f"Save loaded successfully! Loaded {len(all_avatars)} avatars")
        return world, simulator, existed_sects
        
    except Exception as e:
        print(f"Failed to load game: {e}")
        import traceback
        traceback.print_exc()
        raise


def _model_to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def check_save_compatibility(save_path: Path) -> Tuple[bool, str]:
    """
    检查存档兼容性
    
    Args:
        save_path: 存档路径
        
    Returns:
        (是否兼容, 错误信息)
    """
    try:
        with open(save_path, "r", encoding="utf-8") as f:
            save_data = json.load(f)
        
        meta = save_data.get("meta", {})
        save_version = meta.get("version", "unknown")
        current_version = CONFIG.meta.version
        
        # 当前不做版本兼容性检查，直接返回兼容
        # 未来可以在这里添加版本比较逻辑
        return True, ""
        
    except Exception as e:
        return False, f"无法读取存档文件: {e}"

