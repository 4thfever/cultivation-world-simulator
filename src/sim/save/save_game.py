"""
存档功能模块

主要功能：
- save_game: 保存游戏完整状态到JSON文件
- get_save_info: 读取存档的元信息（不加载完整数据）
- list_saves: 列出所有存档文件

存档内容：
- meta: 版本号、保存时间、游戏时间
- world: 游戏时间戳、本局启用的宗门列表
- avatars: 所有角色的完整状态（通过AvatarSaveMixin.to_save_dict序列化）
- events: 最近N条事件历史（N在config.yml中配置）
- simulator: 模拟器配置（如出生率）

存档格式：JSON（明文，易于调试）
存档位置：assets/saves/ (配置在config.yml中)

注意事项：
- 当前版本只支持单一存档槽位（save.json）
- 不支持跨版本兼容（版本号仅记录，不做检查）
- 地图本身不保存（因为地图是固定的，只保存宗门总部位置）
- relations在Avatar中已转换为id映射，避免循环引用
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.world import World
    from src.sim.simulator import Simulator
    from src.classes.sect import Sect

from src.utils.config import CONFIG


def save_game(
    world: "World",
    simulator: "Simulator",
    existed_sects: List["Sect"],
    save_path: Optional[Path] = None
) -> tuple[bool, Optional[str]]:
    """
    保存游戏状态到文件
    
    Args:
        world: 世界对象
        simulator: 模拟器对象
        existed_sects: 本局启用的宗门列表
        save_path: 保存路径，默认为saves/时间戳_游戏时间.json
        
    Returns:
        (保存是否成功, 保存的文件名)
    """
    try:
        # 确定保存路径
        if save_path is None:
            saves_dir = CONFIG.paths.saves
            saves_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成友好的文件名：20251111_193000_Y100M1.json
            now = datetime.now()
            time_str = now.strftime("%Y%m%d_%H%M%S")
            year = world.month_stamp.get_year()
            month = world.month_stamp.get_month().value
            game_time_str = f"Y{year}M{month}"
            
            filename = f"{time_str}_{game_time_str}.json"
            save_path = saves_dir / filename
        else:
            save_path = Path(save_path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 构建元信息
        meta = {
            "version": CONFIG.meta.version,
            "save_time": datetime.now().isoformat(),
            "game_time": f"{world.month_stamp.get_year()}年{world.month_stamp.get_month().value}月"
        }
        
        # 构建世界数据
        # 收集有主洞府信息
        from src.classes.region import CultivateRegion
        cultivate_regions_hosts = {}
        if hasattr(world.map, 'regions'):
             for rid, region in world.map.regions.items():
                 if isinstance(region, CultivateRegion) and region.host_avatar:
                     cultivate_regions_hosts[str(rid)] = region.host_avatar.id

        world_data = {
            "month_stamp": int(world.month_stamp),
            "existed_sect_ids": [sect.id for sect in existed_sects],
            # 天地灵机
            "current_phenomenon_id": world.current_phenomenon.id if world.current_phenomenon else None,
            "phenomenon_start_year": world.phenomenon_start_year if hasattr(world, 'phenomenon_start_year') else 0,
            "cultivate_regions_hosts": cultivate_regions_hosts,
        }
        
        # 保存所有Avatar（第一阶段：不含relations）
        avatars_data = []
        for avatar in world.avatar_manager.avatars.values():
            avatars_data.append(avatar.to_save_dict())
        
        # 保存事件历史（限制数量）
        max_events = CONFIG.save.max_events_to_save
        events_data = []
        recent_events = world.event_manager.get_recent_events(limit=max_events)
        for event in recent_events:
            events_data.append(event.to_dict())
        
        # 保存模拟器数据
        simulator_data = {
            "birth_rate": simulator.birth_rate
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

