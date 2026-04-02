import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

from src.classes.core.sect import sects_by_id, sects_by_name
from src.classes.items.registry import ItemRegistry
from src.classes.items.weapon import weapons_by_name
from src.classes.sect_metadata import sync_world_sect_metadata
from src.classes.technique import techniques_by_id, techniques_by_name
from src.run.log import get_logger
from src.utils.config import CONFIG
from src.utils.llm.client import call_llm_with_task_name

if TYPE_CHECKING:
    from src.classes.core.world import World


@dataclass
class WorldLore:
    text: str = ""


class WorldLoreManager:
    """
    在开局阶段根据“世界观与历史”文本，对既有世界静态设定做一次性重塑。
    该过程只修改当前这局世界的静态描述，不再记录差分回放。
    """

    def __init__(self, world: "World"):
        self.world = world
        self.config_dir = CONFIG.paths.game_configs
        self.logger = get_logger().logger

    async def apply_world_lore(self, lore_text: str) -> None:
        self.logger.info("[WorldLore] 正在根据世界观与历史重塑世界...")

        world_info = str(self.world.static_info) if self.world else ""
        tasks = [
            self._create_task(
                task_suffix="map",
                template_name="world_lore_map.txt",
                infos={
                    "world_info": world_info,
                    "world_lore": lore_text,
                    "city_regions": self._read_csv("city_region.csv"),
                    "normal_regions": self._read_csv("normal_region.csv"),
                    "cultivate_regions": self._read_csv("cultivate_region.csv"),
                },
                handler=self._apply_region_lore_changes,
            ),
            self._create_task(
                task_suffix="sect",
                template_name="world_lore_sect.txt",
                infos={
                    "world_info": world_info,
                    "world_lore": lore_text,
                    "sects": self._read_csv("sect.csv"),
                    "sect_regions": self._read_csv("sect_region.csv"),
                },
                handler=self._apply_sect_lore_changes,
            ),
            self._create_task(
                task_suffix="item",
                template_name="world_lore_item.txt",
                infos={
                    "world_info": world_info,
                    "world_lore": lore_text,
                    "techniques": self._read_csv("technique.csv"),
                    "weapons": self._read_csv("weapon.csv"),
                    "auxiliarys": self._read_csv("auxiliary.csv"),
                },
                handler=self._apply_item_lore_changes,
            ),
        ]
        await asyncio.gather(*tasks)
        self.logger.info("[WorldLore] 世界观与历史塑形完成")

    async def _create_task(
        self,
        *,
        task_suffix: str,
        template_name: str,
        infos: dict[str, Any],
        handler: Callable[[dict[str, Any]], None],
    ) -> None:
        task_name = f"world_lore_{task_suffix}"
        template_path = CONFIG.paths.templates / template_name
        try:
            result = await call_llm_with_task_name(
                task_name=task_name,
                template_path=str(template_path),
                infos=infos,
                max_retries=3,
            )
            if result:
                handler(result)
            else:
                self.logger.info(f"[WorldLore] {task_name} 返回为空，未进行修改")
        except Exception as exc:
            self.logger.error(f"[WorldLore] {task_name} 任务失败: {exc}")

    def _read_csv(self, filename: str) -> str:
        file_path = self.config_dir / filename
        if not file_path.exists():
            self.logger.warning(f"[WorldLore] 配置文件不存在: {file_path}")
            return ""
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as exc:
            self.logger.error(f"[WorldLore] 读取文件 {filename} 失败: {exc}")
            return ""

    def _apply_region_lore_changes(self, result: dict[str, Any]) -> None:
        self._update_regions(result.get("city_regions_change", {}))
        self._update_regions(result.get("normal_regions_change", {}))
        self._update_regions(result.get("cultivate_regions_change", {}))

    def _apply_sect_lore_changes(self, result: dict[str, Any]) -> None:
        self._update_regions(result.get("sect_regions_change", {}))
        changes = result.get("sects_change", {})

        count = 0
        for sect_id_str, data in changes.items():
            try:
                sect_id = int(sect_id_str)
            except (TypeError, ValueError):
                self.logger.error(f"[WorldLore] 非法宗门 ID: {sect_id_str}")
                continue

            sect = sects_by_id.get(sect_id)
            if sect is None:
                continue

            old_name = sect.name
            self._update_obj_attrs(sect, data)
            if sect.name != old_name:
                sects_by_name.pop(old_name, None)
                sects_by_name[sect.name] = sect
            self.logger.info(f"[WorldLore] 宗门重塑 - ID: {sect_id}, Name: {sect.name}, Desc: {sect.desc}")
            count += 1

        if count > 0:
            self.logger.info(f"[WorldLore] 更新了 {count} 个宗门")

        if self.world is not None:
            sync_world_sect_metadata(self.world)

    def _apply_item_lore_changes(self, result: dict[str, Any]) -> None:
        self._update_techniques(result.get("techniques_change", {}))
        self._update_items(result.get("weapons_change", {}), weapons_by_name, "装备")
        self._update_items(result.get("auxiliarys_change", {}), None, "辅助装备")

    def _update_regions(self, changes: dict[str, Any]) -> None:
        if not changes:
            return

        count = 0
        for region_id_str, data in changes.items():
            try:
                region_id = int(region_id_str)
            except (TypeError, ValueError):
                self.logger.error(f"[WorldLore] 非法区域 ID: {region_id_str}")
                continue

            region = self.world.map.regions.get(region_id) if self.world and self.world.map else None
            if region is None:
                continue

            self._update_obj_attrs(region, data)
            self.logger.info(f"[WorldLore] 区域重塑 - ID: {region_id}, Name: {region.name}, Desc: {region.desc}")
            count += 1

        if count > 0:
            self.logger.info(f"[WorldLore] 更新了 {count} 个区域")

    def _update_techniques(self, changes: dict[str, Any]) -> None:
        if not changes:
            return

        count = 0
        for technique_id_str, data in changes.items():
            try:
                technique_id = int(technique_id_str)
            except (TypeError, ValueError):
                self.logger.error(f"[WorldLore] 非法功法 ID: {technique_id_str}")
                continue

            technique = techniques_by_id.get(technique_id)
            if technique is None:
                continue

            old_name = technique.name
            self._update_obj_attrs(technique, data)
            if technique.name != old_name:
                techniques_by_name.pop(old_name, None)
                techniques_by_name[technique.name] = technique
            self.logger.info(
                f"[WorldLore] 功法重塑 - ID: {technique_id}, Name: {technique.name}, Desc: {technique.desc}"
            )
            count += 1

        if count > 0:
            self.logger.info(f"[WorldLore] 更新了 {count} 本功法")

    def _update_items(
        self,
        changes: dict[str, Any],
        by_name_index: dict[str, Any] | None,
        category_label: str,
    ) -> None:
        if not changes:
            return

        count = 0
        for item_id_str, data in changes.items():
            try:
                item_id = int(item_id_str)
            except (TypeError, ValueError):
                self.logger.error(f"[WorldLore] 非法物品 ID: {item_id_str}")
                continue

            item = ItemRegistry.get(item_id)
            if item is None:
                continue

            old_name = item.name
            self._update_obj_attrs(item, data)
            if by_name_index is not None and item.name != old_name:
                by_name_index.pop(old_name, None)
                by_name_index[item.name] = item
            self.logger.info(f"[WorldLore] {category_label}重塑 - ID: {item_id}, Name: {item.name}, Desc: {item.desc}")
            count += 1

        if count > 0:
            self.logger.info(f"[WorldLore] 更新了 {count} 件{category_label}")

    @staticmethod
    def _update_obj_attrs(obj: Any, data: dict[str, Any]) -> None:
        if "name" in data and data["name"]:
            obj.name = str(data["name"])
        if "desc" in data and data["desc"]:
            obj.desc = str(data["desc"])
