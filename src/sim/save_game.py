"""
存档功能模块
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional

from src.classes.world import World
from src.sim.simulator import Simulator
from src.classes.sect import Sect
from src.utils.config import CONFIG


def save_game(
    world: World,
    simulator: Simulator,
    existed_sects: List[Sect],
    save_path: Optional[Path] = None
) -> bool:
    """
    保存游戏状态到文件
    
    Args:
        world: 世界对象
        simulator: 模拟器对象
        existed_sects: 本局启用的宗门列表
        save_path: 保存路径，默认为saves/save.json
        
    Returns:
        保存是否成功
    """
    try:
        # 确定保存路径
        if save_path is None:
            saves_dir = CONFIG.paths.saves
            saves_dir.mkdir(parents=True, exist_ok=True)
            save_path = saves_dir / "save.json"
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
        world_data = {
            "month_stamp": int(world.month_stamp),
            "existed_sect_ids": [sect.id for sect in existed_sects]
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
        return True
        
    except Exception as e:
        print(f"保存游戏失败: {e}")
        import traceback
        traceback.print_exc()
        return False


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

