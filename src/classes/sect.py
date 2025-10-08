from dataclasses import dataclass
from pathlib import Path

from src.classes.alignment import Alignment
from src.utils.df import game_configs
from src.utils.config import CONFIG


# 宗门驻地
@dataclass
class SectHeadQuarter:
    """
    宗门总部
    """
    name: str
    image: Path

@dataclass
class Sect:
    """
    宗门
    """
    id: int
    name: str
    desc: str
    member_act_style: str
    alignment: Alignment
    sect_surnames: list[str]
    sect_given_names: list[str]
    headquarter: SectHeadQuarter
    # 功法：在technique.csv中配置
    # TODO：法宝
    # TODO：宗内等级和称谓
def _split_names(value: object) -> list[str]:
    raw = "" if value is None or str(value) == "nan" else str(value)
    sep = CONFIG.df.ids_separator
    parts = [x.strip() for x in raw.split(sep) if x.strip()] if raw else []
    return parts


def _load_sects() -> tuple[dict[int, Sect], dict[str, Sect]]:
    """从配表加载 sect 数据"""
    sects_by_id: dict[int, Sect] = {}
    sects_by_name: dict[str, Sect] = {}

    df = game_configs["sect"]
    assets_base = Path("assets/sects")
    for _, row in df.iterrows():
        image_path = assets_base / f"{row['name']}.png"

        sect = Sect(
            id=int(row["id"]),
            name=str(row["name"]),
            desc=str(row["desc"]),
            member_act_style=str(row["member_act_style"]),
            alignment=Alignment.from_str(row.get("alignment", "中")),
            sect_surnames=_split_names(row.get("sect_surnames", "")),
            sect_given_names=_split_names(row.get("sect_given_names", "")),
            headquarter=SectHeadQuarter(name=str(row["name"]), image=image_path),
        )
        sects_by_id[sect.id] = sect
        sects_by_name[sect.name] = sect

    return sects_by_id, sects_by_name


# 导出：从配表加载 sect 数据
sects_by_id, sects_by_name = _load_sects()