import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, Callable, TYPE_CHECKING, Coroutine

from src.classes.item_registry import ItemRegistry
from src.classes.technique import techniques_by_id, techniques_by_name
from src.classes.weapon import weapons_by_name
from src.classes.sect import sects_by_id, sects_by_name
from src.utils.llm.client import call_llm_with_task_name
from src.run.log import get_logger

if TYPE_CHECKING:
    from src.classes.world import World

class HistoryManager:
    """
    历史管理器
    在游戏开局时，根据历史文本一次性修改世界中的对象数据。
    支持并发调用 LLM 分别处理不同领域的数据（地图、宗门、物品）。
    """
    def __init__(self, world: "World"):
        self.world = world
        self.config_dir = Path("static/game_configs")
        self.logger = get_logger().logger

    async def apply_history_influence(self, history_text: str):
        """
        核心方法：读取 CSV -> 并发 LLM 分析 -> 更新内存对象
        """
        self.logger.info("[History] 正在根据历史推演世界变化 (并发模式)...")
        
        world_info = str(self.world.static_info) if self.world else ""
        
        # 1. 构建并发任务
        tasks = []

        # Task 1: Map (Regions)
        tasks.append(self._create_task(
            task_suffix="map",
            template="static/templates/history_influence_map.txt",
            infos={
                "world_info": world_info,
                "history_str": history_text,
                "city_regions": self._read_csv("city_region.csv"),
                "normal_regions": self._read_csv("normal_region.csv"),
                "cultivate_regions": self._read_csv("cultivate_region.csv"),
            },
            handler=self._apply_map_changes
        ))

        # Task 2: Sects & Sect Regions
        tasks.append(self._create_task(
            task_suffix="sect",
            template="static/templates/history_influence_sect.txt",
            infos={
                "world_info": world_info,
                "history_str": history_text,
                "sects": self._read_csv("sect.csv"),
                "sect_regions": self._read_csv("sect_region.csv"),
            },
            handler=self._apply_sect_changes
        ))

        # Task 3: Items (Techniques, Weapons, Auxiliarys)
        tasks.append(self._create_task(
            task_suffix="item",
            template="static/templates/history_influence_item.txt",
            infos={
                "world_info": world_info,
                "history_str": history_text,
                "techniques": self._read_csv("technique.csv"),
                "weapons": self._read_csv("weapon.csv"),
                "auxiliarys": self._read_csv("auxiliary.csv"),
            },
            handler=self._apply_item_changes
        ))

        # 2. 并发执行并等待所有结果
        await asyncio.gather(*tasks)
        self.logger.info("[History] 历史推演完成")

    async def _create_task(
        self, 
        task_suffix: str, 
        template: str, 
        infos: Dict[str, Any], 
        handler: Callable[[Dict[str, Any]], None]
    ):
        """
        创建一个执行单元：调用 LLM -> 处理回调
        """
        task_name = f"history_influence_{task_suffix}"
        try:
            result = await call_llm_with_task_name(
                task_name=task_name,
                template_path=template,
                infos=infos,
                max_retries=3
            )
            if result:
                handler(result)
            else:
                self.logger.info(f"[History] {task_name} 返回为空，未进行修改")
        except Exception as e:
            self.logger.error(f"[History] {task_name} 任务失败: {e}")

    def _read_csv(self, filename: str) -> str:
        """读取 CSV 文件原始内容"""
        file_path = self.config_dir / filename
        if not file_path.exists():
            self.logger.warning(f"[History] Warning: 配置文件不存在 {file_path}")
            return ""
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.logger.error(f"[History] 读取文件 {filename} 失败: {e}")
            return ""

    # --- Handlers ---

    def _apply_map_changes(self, result: Dict[str, Any]):
        """处理地图区域变更"""
        self._update_regions(result.get("city_regions_change", {}))
        self._update_regions(result.get("normal_regions_change", {}))
        self._update_regions(result.get("cultivate_regions_change", {}))

    def _apply_sect_changes(self, result: Dict[str, Any]):
        """处理宗门及宗门驻地变更"""
        # 1. 宗门驻地 (从 Map 任务移过来)
        self._update_regions(result.get("sect_regions_change", {}))

        # 2. 宗门本体
        changes = result.get("sects_change", {})
        if not changes: return

        count = 0
        for sid_str, data in changes.items():
            try:
                sid = int(sid_str)
                sect = sects_by_id.get(sid)
                if sect:
                    old_name = sect.name
                    self._update_obj_attrs(sect, data)
                    
                    # 同步 sects_by_name 索引
                    if sect.name != old_name:
                        if old_name in sects_by_name:
                            del sects_by_name[old_name]
                        sects_by_name[sect.name] = sect
                    
                    self.logger.info(f"[History] 宗门变更 - ID: {sid}, Name: {sect.name}, Desc: {sect.desc}")
                    count += 1
            except Exception as e:
                self.logger.error(f"[History] 宗门更新失败 - ID: {sid_str}, Error: {e}")
                continue
        if count > 0:
            self.logger.info(f"[History] 更新了 {count} 个宗门")

    def _apply_item_changes(self, result: Dict[str, Any]):
        """处理物品/功法变更"""
        self._update_techniques(result.get("techniques_change", {}))
        self._update_items(result.get("weapons_change", {}), weapons_by_name)
        self._update_items(result.get("auxiliarys_change", {}), None)

    # --- Update Logic ---

    def _update_regions(self, changes: Dict[str, Any]):
        """更新区域 (Map.regions)"""
        if not changes: return
        
        count = 0
        for rid_str, data in changes.items():
            try:
                rid = int(rid_str)
                if self.world and self.world.map:
                    region = self.world.map.regions.get(rid)
                    if region:
                        self._update_obj_attrs(region, data)
                        self.logger.info(f"[History] 区域变更 - ID: {rid}, Name: {region.name}, Desc: {region.desc}")
                        count += 1
            except Exception as e:
                self.logger.error(f"[History] 区域更新失败 - ID: {rid_str}, Error: {e}")
                continue
        if count > 0:
            self.logger.info(f"[History] 更新了 {count} 个区域")

    def _update_techniques(self, changes: Dict[str, Any]):
        """更新功法 (techniques_by_id)"""
        if not changes: return
        
        count = 0
        for tid_str, data in changes.items():
            try:
                tid = int(tid_str)
                tech = techniques_by_id.get(tid)
                if tech:
                    old_name = tech.name
                    self._update_obj_attrs(tech, data)
                    
                    if tech.name != old_name:
                        if old_name in techniques_by_name:
                            del techniques_by_name[old_name]
                        techniques_by_name[tech.name] = tech
                    
                    self.logger.info(f"[History] 功法变更 - ID: {tid}, Name: {tech.name}, Desc: {tech.desc}")
                    count += 1
            except Exception as e:
                self.logger.error(f"[History] 功法更新失败 - ID: {tid_str}, Error: {e}")
                continue
        if count > 0:
            self.logger.info(f"[History] 更新了 {count} 本功法")

    def _update_items(self, changes: Dict[str, Any], by_name_index: Optional[Dict[str, Any]]):
        """更新物品 (ItemRegistry)"""
        if not changes: return

        count = 0
        for iid_str, data in changes.items():
            try:
                iid = int(iid_str)
                item = ItemRegistry.get(iid)
                if item:
                    old_name = item.name
                    self._update_obj_attrs(item, data)
                    
                    if by_name_index is not None and item.name != old_name:
                        if old_name in by_name_index:
                            del by_name_index[old_name]
                        by_name_index[item.name] = item
                    
                    self.logger.info(f"[History] 装备变更 - ID: {iid}, Name: {item.name}, Desc: {item.desc}")
                    count += 1
            except Exception as e:
                self.logger.error(f"[History] 装备更新失败 - ID: {iid_str}, Error: {e}")
                continue
        if count > 0:
            self.logger.info(f"[History] 更新了 {count} 件装备")

    def _update_obj_attrs(self, obj: Any, data: Dict[str, Any]):
        """通用属性更新 helper"""
        if "name" in data and data["name"]:
            obj.name = str(data["name"])
        if "desc" in data and data["desc"]:
            obj.desc = str(data["desc"])

if __name__ == "__main__":
    # 模拟运行
    pass
