from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.classes.world_lore_snapshot import build_world_lore_snapshot
from src.run.log import get_logger
from src.systems.world_lore_rewrite import (
    WorldLoreRewriteRunner,
    apply_world_lore_rewrite,
    build_world_lore_context,
)

if TYPE_CHECKING:
    from src.classes.core.world import World


@dataclass
class WorldLore:
    text: str = ""


class WorldLoreManager:
    """
    开局阶段根据“世界观与历史”文本，对本局地点、宗门、功法和装备文本做一次性全量重写。
    """

    def __init__(self, world: "World"):
        self.world = world
        self.logger = get_logger().logger

    async def apply_world_lore(self, lore_text: str) -> None:
        lore_text = str(lore_text or "").strip()
        if not lore_text:
            return

        self.logger.info("[WorldLore] 正在根据世界观与历史重塑世界...")
        context = build_world_lore_context(self.world, lore_text)
        draft = await WorldLoreRewriteRunner(context).run()
        apply_world_lore_rewrite(self.world, draft)
        self.world.world_lore_snapshot = build_world_lore_snapshot(
            self.world,
            lore_text=lore_text,
            draft=draft,
            rewrite_config=context.config,
        )
        self.logger.info("[WorldLore] 世界观与历史塑形完成")
