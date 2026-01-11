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

if TYPE_CHECKING:
    from src.classes.world import World
    from src.sim.simulator import Simulator
    from src.classes.sect import Sect

from src.classes.calendar import MonthStamp
from src.classes.event import Event
from src.classes.relation import Relation
from src.utils.config import CONFIG


def get_events_db_path(save_path: Path) -> Path:
    """
    根据存档路径计算事件数据库路径。

    例如：save_20260105_1423.json -> save_20260105_1423_events.db
    """
    return save_path.with_suffix("").with_name(save_path.stem + "_events.db")


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
        saves_dir = CONFIG.paths.saves
        save_path = saves_dir / "save.json"
    else:
        save_path = Path(save_path)
    
    if not save_path.exists():
        raise FileNotFoundError(f"存档文件不存在: {save_path}")
    
    try:
        # 运行时导入，避免循环依赖
        from src.classes.world import World
        from src.classes.avatar import Avatar
        from src.classes.sect import sects_by_id
        from src.sim.simulator import Simulator
        from src.run.load_map import load_cultivation_world_map
        
        # 读取存档文件
        with open(save_path, "r", encoding="utf-8") as f:
            save_data = json.load(f)
        
        # 读取元信息
        meta = save_data.get("meta", {})
        print(f"正在加载存档 (版本: {meta.get('version', 'unknown')}, "
              f"游戏时间: {meta.get('game_time', 'unknown')})")
        
        # 重建地图（地图本身不变，只需重建宗门总部位置）
        game_map = load_cultivation_world_map()
        
        # 读取世界数据
        world_data = save_data.get("world", {})
        month_stamp = MonthStamp(world_data["month_stamp"])
        
        # 计算事件数据库路径。
        events_db_path = get_events_db_path(save_path)

        # 重建World对象（使用 SQLite 事件存储）。
        world = World.create_with_db(
            map=game_map,
            month_stamp=month_stamp,
            events_db_path=events_db_path,
        )
        
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
        
        # 第一阶段：重建所有Avatar（不含relations）
        avatars_data = save_data.get("avatars", [])
        all_avatars = {}
        for avatar_data in avatars_data:
            avatar = Avatar.from_save_dict(avatar_data, world)
            all_avatars[avatar.id] = avatar
        
        # 第二阶段：重建relations（需要所有avatar都已加载）
        for avatar_data in avatars_data:
            avatar_id = avatar_data["id"]
            avatar = all_avatars[avatar_id]
            relations_dict = avatar_data.get("relations", {})
            
            for other_id, relation_value in relations_dict.items():
                if other_id in all_avatars:
                    other_avatar = all_avatars[other_id]
                    relation = Relation(relation_value)
                    avatar.relations[other_avatar] = relation
        
        # 将所有avatar添加到world
        world.avatar_manager.avatars = all_avatars
        
        # 恢复洞府主人关系
        cultivate_regions_hosts = world_data.get("cultivate_regions_hosts", {})
        from src.classes.region import CultivateRegion
        for rid_str, avatar_id in cultivate_regions_hosts.items():
            rid = int(rid_str)
            if rid in game_map.regions:
                region = game_map.regions[rid]
                if isinstance(region, CultivateRegion) and avatar_id in all_avatars:
                    region.host_avatar = all_avatars[avatar_id]
        
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

        # 检查是否需要从 JSON 迁移事件（向后兼容旧存档）。
        db_event_count = world.event_manager.count()
        events_data = save_data.get("events", [])

        if db_event_count == 0 and len(events_data) > 0:
            # SQLite 数据库是空的，但 JSON 中有事件，执行迁移。
            print(f"正在从 JSON 迁移 {len(events_data)} 条事件到 SQLite...")
            for event_data in events_data:
                event = Event.from_dict(event_data)
                world.event_manager.add_event(event)
            print("事件迁移完成")
        else:
            print(f"已从 SQLite 加载 {db_event_count} 条事件")

        # 重建Simulator
        simulator_data = save_data.get("simulator", {})
        simulator = Simulator(world)
        # 兼容旧存档 "birth_rate"
        simulator.awakening_rate = simulator_data.get("awakening_rate", simulator_data.get("birth_rate", CONFIG.game.npc_awakening_rate_per_month))
        
        print(f"存档加载成功！共加载 {len(all_avatars)} 个角色")
        return world, simulator, existed_sects
        
    except Exception as e:
        print(f"加载游戏失败: {e}")
        import traceback
        traceback.print_exc()
        raise


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

