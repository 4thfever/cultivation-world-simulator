"""
存档功能模块

主要功能：
- save_game: 保存游戏完整状态到JSON文件
- get_save_info: 读取存档的元信息（不加载完整数据）
- list_saves: 列出所有存档文件

存档内容：
- meta: 版本号、保存时间、游戏时间、事件数据库信息
- world: 游戏时间戳、本局启用的宗门列表
- avatars: 所有角色的完整状态（通过AvatarSaveMixin.to_save_dict序列化）
- events: 最近N条事件历史（仅用于向后兼容迁移，新事件存储在SQLite中）
- simulator: 模拟器配置（如出生率）

存档格式：
- JSON（明文，易于调试）+ SQLite事件数据库
- 存档位置：assets/saves/ (配置在config.yml中)
- 事件数据库：{save_name}_events.db（与JSON文件同目录）

注意事项：
- 不支持跨版本兼容（版本号仅记录，不做检查）
- 地图本身不保存（因为地图是固定的，只保存宗门总部位置）
- relations在Avatar中已转换为id映射，避免循环引用
- 事件实时写入SQLite，JSON中的events字段仅用于旧存档迁移
"""
import json
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.core.world import World
    from src.sim.simulator import Simulator
    from src.classes.core.sect import Sect

from src.utils.config import CONFIG
from src.classes.language import language_manager
from src.sim.load.load_game import get_events_db_path



def sanitize_save_name(name: str) -> str:
    """清理存档名称，只保留安全字符。"""
    # 移除文件系统不允许的字符。
    safe_name = re.sub(r'[\\/:*?"<>|]', '', name)
    # 只保留中文、字母、数字和下划线。
    safe_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', safe_name)
    return safe_name[:50] if safe_name else "save"


def save_game(
    world: "World",
    simulator: "Simulator",
    existed_sects: List["Sect"],
    save_path: Optional[Path] = None,
    custom_name: Optional[str] = None
) -> tuple[bool, Optional[str]]:
    """
    保存游戏状态到文件

    Args:
        world: 世界对象
        simulator: 模拟器对象
        existed_sects: 本局启用的宗门列表
        save_path: 保存路径，默认为saves/时间戳_游戏时间.json
        custom_name: 用户自定义的存档名称

    Returns:
        (保存是否成功, 保存的文件名)
    """
    try:
        # 确定保存路径
        if save_path is None:
            saves_dir = CONFIG.paths.saves
            saves_dir.mkdir(parents=True, exist_ok=True)

            # 生成友好的文件名。
            now = datetime.now()
            time_str = now.strftime("%Y%m%d_%H%M%S")
            year = world.month_stamp.get_year()
            month = world.month_stamp.get_month().value
            game_time_str = f"Y{year}M{month}"

            # 处理自定义名称。
            if custom_name:
                safe_name = sanitize_save_name(custom_name)
                filename = f"{safe_name}_{time_str}.json"
            else:
                filename = f"{time_str}_{game_time_str}.json"

            save_path = saves_dir / filename
        else:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 计算事件数据库路径。
        events_db_path = get_events_db_path(save_path)

        # 确保当前的 SQLite 数据库被复制到新存档的位置。
        # 如果当前使用的是其他数据库文件，需要将其复制过来。
        if hasattr(world.event_manager, "_storage") and world.event_manager._storage:
             current_db_path = world.event_manager._storage._db_path
             if current_db_path != events_db_path:
                 import shutil
                 # 确保源文件存在
                 if current_db_path.exists():
                    # 确保目标目录存在
                    events_db_path.parent.mkdir(parents=True, exist_ok=True)
                    # 复制数据库文件
                    shutil.copy2(current_db_path, events_db_path)
                    print(f"已复制事件数据库: {current_db_path} -> {events_db_path}")
                 else:
                     print(f"警告: 当前事件数据库不存在: {current_db_path}")

        # 计算角色统计。
        alive_count = len(world.avatar_manager.avatars)
        dead_count = len(world.avatar_manager.dead_avatars)
        total_count = alive_count + dead_count

        # 构建元信息
        meta = {
            "version": CONFIG.meta.version,
            "save_time": datetime.now().isoformat(),
            "game_time": f"{world.month_stamp.get_year()}年{world.month_stamp.get_month().value}月",
            "language": str(language_manager),
            # SQLite 事件数据库信息。
            "events_db": str(events_db_path.name),
            "event_count": world.event_manager.count(),
            # 新增元数据。
            "avatar_count": total_count,
            "alive_count": alive_count,
            "dead_count": dead_count,
            "custom_name": custom_name,
        }
        
        # 构建世界数据
        # 收集有主洞府信息
        from src.classes.environment.region import CultivateRegion, CityRegion
        cultivate_regions_hosts = {}
        regions_status = {}
        
        if hasattr(world.map, 'regions'):
             for rid, region in world.map.regions.items():
                 # 保存洞府主人
                 if isinstance(region, CultivateRegion) and region.host_avatar:
                     cultivate_regions_hosts[str(rid)] = region.host_avatar.id
                 
                 # 保存城市繁荣度
                 if isinstance(region, CityRegion):
                     regions_status[str(rid)] = {
                         "prosperity": region.prosperity
                     }

        world_data = {
            "month_stamp": int(world.month_stamp),
            "start_year": world.start_year,
            "existed_sect_ids": [sect.id for sect in existed_sects],
            # 天地灵机
            "current_phenomenon_id": world.current_phenomenon.id if world.current_phenomenon else None,
            "phenomenon_start_year": world.phenomenon_start_year if hasattr(world, 'phenomenon_start_year') else 0,
            "cultivate_regions_hosts": cultivate_regions_hosts,
            "regions_status": regions_status,
            # 出世物品流转
            "circulation": world.circulation.to_save_dict(),
            # 世界历史
            "history": {
                "text": world.history.text,
                "modifications": world.history.modifications
            },
        }
        
        # 保存所有Avatar（第一阶段：不含relations）
        # 需要保存活人和死者
        avatars_data = []
        for avatar in world.avatar_manager._iter_all_avatars():
            avatars_data.append(avatar.to_save_dict())
        
        # 保存事件历史（限制数量）
        max_events = CONFIG.save.max_events_to_save
        events_data = []
        recent_events = world.event_manager.get_recent_events(limit=max_events)
        for event in recent_events:
            events_data.append(event.to_dict())
        
        # 保存模拟器数据
        simulator_data = {
            "awakening_rate": simulator.awakening_rate
        }
        
        # 组装完整的存档数据
        save_data = {
            "meta": meta,
            "world": world_data,
            "avatars": avatars_data,
            "events": events_data,
            "simulator": simulator_data
        }
        
        # 写入文件
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        print(f"游戏已保存到: {save_path}")
        return True, save_path.name
        
    except Exception as e:
        print(f"保存游戏失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def get_save_info(save_path: Path) -> Optional[dict]:
    """
    读取存档文件的元信息（不加载完整数据）
    
    Args:
        save_path: 存档路径
        
    Returns:
        存档元信息字典，如果读取失败返回None
    """
    try:
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("meta", {})
    except Exception:
        return None


def list_saves(saves_dir: Optional[Path] = None) -> List[tuple[Path, dict]]:
    """
    列出所有存档文件及其元信息
    
    Args:
        saves_dir: 存档目录，默认为config中的saves目录
        
    Returns:
        [(存档路径, 元信息字典), ...]
    """
    if saves_dir is None:
        saves_dir = CONFIG.paths.saves
    
    if not saves_dir.exists():
        return []
    
    saves = []
    for save_file in saves_dir.glob("*.json"):
        info = get_save_info(save_file)
        if info is not None:
            saves.append((save_file, info))
    
    # 按保存时间倒序排列
    saves.sort(key=lambda x: x[1].get("save_time", ""), reverse=True)
    return saves

