from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict

from src.utils.df import game_configs
from src.classes.effect import load_effect_from_str
from src.classes.sect import Sect, sects_by_id


@dataclass
class Treasure:
    """
    法宝：配置驱动，暂不挂接到 Avatar。
    字段与 static/game_configs/treasure.csv 对应：
    - sect_id：对应宗门ID（见 sect.csv）；允许为空表示无特定宗门归属
    - effects：解析为 dict，用于未来与 Avatar.effects 合并
    """
    id: int
    name: str
    sect_id: Optional[int]
    desc: str
    effects: dict[str, object] = field(default_factory=dict)
    sect: Optional[Sect] = None
    # 万魂幡专用：吞噬魂魄计数（0~10000）
    devoured_souls: int = 0

    def get_info(self) -> str:
        suffix = f"（吞噬魂魄：{self.devoured_souls}）" if self.name == "万魂幡" and self.devoured_souls > 0 else ""
        return f"{self.name}{suffix}"

    def get_detailed_info(self) -> str:
        souls = f" 吞噬魂魄：{self.devoured_souls}" if self.name == "万魂幡" and self.devoured_souls > 0 else ""
        return f"{self.name}（{self.desc}）{souls}"


def _load_treasures() -> tuple[Dict[int, Treasure], Dict[str, Treasure], Dict[int, Treasure]]:
    """从配表加载 treasure 数据。
    返回：(按ID、按名称、按宗门ID 的映射)。
    若同一宗门配置多个法宝，按首次出现保留（每门至多一个）。
    """
    treasures_by_id: Dict[int, Treasure] = {}
    treasures_by_name: Dict[str, Treasure] = {}
    treasures_by_sect_id: Dict[int, Treasure] = {}

    df = game_configs.get("treasure")
    if df is None:
        return treasures_by_id, treasures_by_name, treasures_by_sect_id

    for _, row in df.iterrows():
        raw_sect = row.get("sect_id")
        sect_id: Optional[int] = None
        if raw_sect is not None and str(raw_sect).strip() and str(raw_sect).strip() != "nan":
            sect_id = int(float(raw_sect))

        raw_effects_val = row.get("effects", "")
        effects = load_effect_from_str(raw_effects_val)

        sect_obj: Optional[Sect] = sects_by_id.get(int(sect_id)) if sect_id is not None else None

        t = Treasure(
            id=int(row["id"]),
            name=str(row["name"]),
            sect_id=sect_id,
            desc=str(row.get("desc", "")),
            effects=effects,
            sect=sect_obj,
        )

        # no-op

        treasures_by_id[t.id] = t
        treasures_by_name[t.name] = t
        if t.sect_id is not None and t.sect_id not in treasures_by_sect_id:
            treasures_by_sect_id[t.sect_id] = t

    return treasures_by_id, treasures_by_name, treasures_by_sect_id


treasures_by_id, treasures_by_name, treasures_by_sect_id = _load_treasures()