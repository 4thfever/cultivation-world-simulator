import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING
import logging

from src.classes.item_registry import ItemRegistry
from src.classes.technique import techniques_by_id, techniques_by_name
from src.classes.weapon import weapons_by_name
from src.utils.llm.client import call_llm_with_task_name
from src.run.log import get_logger

if TYPE_CHECKING:
    from src.classes.world import World

class HistoryManager:
    """
    历史管理器
    在游戏开局时，根据历史文本一次性修改世界中的对象数据。
    """
    def __init__(self, world: "World"):
        self.world = world
        # 配置目录路径
        self.config_dir = Path("static/game_configs")
        self.logger = get_logger().logger

    async def apply_history_influence(self, history_text: str):
        """
        核心方法：读取 CSV -> LLM 分析 -> 更新内存对象
        """
        # 1. 准备 Prompt 参数：直接读取 CSV 原始内容
        infos = {
            "world_info": str(self.world.static_info) if self.world else "",
            "history_str": history_text,
            "city_regions": self._read_csv("city_region.csv"),
            "normal_regions": self._read_csv("normal_region.csv"),
            "cultivate_regions": self._read_csv("cultivate_region.csv"),
            "techniques": self._read_csv("technique.csv"),
            "weapons": self._read_csv("weapon.csv"),
            "auxiliarys": self._read_csv("auxiliary.csv"),
        }

        # 2. 调用 LLM
        self.logger.info("[History] 正在根据历史推演世界变化...")
        try:
            result = await call_llm_with_task_name(
                task_name="history_influence",
                template_path="static/templates/history_influence.txt",
                infos=infos,
                max_retries=3 # 增加重试次数，确保 JSON 格式正确
            )
        except Exception as e:
            self.logger.error(f"[History] LLM 调用或解析失败: {e}")
            return

        # 3. 应用变更到内存对象
        if result:
            self._apply_changes(result)
        else:
            self.logger.info("[History] LLM 返回为空，未进行任何修改")

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

    def _apply_changes(self, result: Dict[str, Any]):
        """分发并应用变更"""
        
        # 3.1 区域变更
        self._update_regions(result.get("city_regions_change", {}))
        self._update_regions(result.get("normal_regions_change", {}))
        self._update_regions(result.get("cultivate_regions_change", {}))
        
        # 3.2 功法变更
        self._update_techniques(result.get("techniques_change", {}))
        
        # 3.3 装备变更
        self._update_items(result.get("weapons_change", {}), weapons_by_name)
        self._update_items(result.get("auxiliarys_change", {}), None) # 辅助装备可能没有全局 name 索引

    def _update_regions(self, changes: Dict[str, Any]):
        """更新区域 (Map.regions)"""
        if not changes: return
        
        count = 0
        for rid_str, data in changes.items():
            try:
                rid = int(rid_str)
                # 从 World.Map 获取区域
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
                    
                    # 同步 techniques_by_name 索引
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
                    
                    # 同步可选的 name 索引 (如 weapons_by_name)
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
    history_str = "上古时期..."
    # 注意：这里直接运行可能会报错，因为需要 World 对象
    # 这里只是为了保留文件结构的完整性
    pass
