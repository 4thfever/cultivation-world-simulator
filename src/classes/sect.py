from dataclasses import dataclass
from pathlib import Path

from src.classes.alignment import Alignment
from src.utils.df import game_configs
from src.utils.config import CONFIG


"""
宗门、宗门总部基础数据。
驻地名称与描述已迁移到 sect_region.csv，供地图区域系统使用。
此处仅保留宗门本体信息与头像编辑所需的静态字段。
"""

# 宗门驻地（基础展示数据，具体地图位置在 sect_region.csv 中定义）
@dataclass
class SectHeadQuarter:
    """
    宗门总部
    """
    name: str
    desc: str
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
    male_sect_given_names: list[str]
    female_sect_given_names: list[str]
    headquarter: SectHeadQuarter
    # 本宗关联的功法名称（来自 technique.csv 的 sect 列）
    technique_names: list[str]
    # 随机选择宗门时使用的权重（默认1）
    weight: float = 1.0
    # 功法：在technique.csv中配置
    # TODO：法宝
    # TODO：宗内等级和称谓

    def get_info(self) -> str:
        hq = self.headquarter
        return f"{self.name}（阵营：{self.alignment}，驻地：{hq.name}）"

    def get_detailed_info(self) -> str:
        # 详细描述：风格、阵营、驻地
        hq = self.headquarter
        return f"{self.name}（阵营：{self.alignment}，风格：{self.member_act_style}，驻地：{hq.name}）"
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
    # 可能不存在 technique 配表或未添加 sect 列，做容错
    tech_df = game_configs.get("technique")
    assets_base = Path("assets/sects")
    for _, row in df.iterrows():
        image_path = assets_base / f"{row['name']}.png"
        male_given_names = _split_names(row["male_sect_given_names"]) 
        female_given_names = _split_names(row["female_sect_given_names"]) 

        # 收集该宗门下配置的功法名称
        technique_names: list[str] = []
        if tech_df is not None and "sect" in tech_df.columns:
            technique_names = [
                str(tname).strip()
                for tname in tech_df.loc[tech_df["sect"] == row["name"], "name"].tolist()
                if str(tname).strip()
            ]

        # 读取权重（缺省/NaN 则为 1.0）
        weight_val = row.get("weight", 1)
        weight = float(str(weight_val)) if str(weight_val) != "nan" else 1.0

        sect = Sect(
            id=int(row["id"]),
            name=str(row["name"]),
            desc=str(row["desc"]),
            member_act_style=str(row["member_act_style"]),
            alignment=Alignment.from_str(row["alignment"]),
            sect_surnames=_split_names(row["sect_surnames"]),
            male_sect_given_names=male_given_names,
            female_sect_given_names=female_given_names,
            # 保留旧字段的兼容读取（如旧csv仍包含headquarter_*列则读入；否则使用宗门名与空描述）
            headquarter=SectHeadQuarter(
                name=(str(row.get("headquarter_name", "")).strip() or str(row["name"])) ,
                desc=str(row.get("headquarter_desc", "")),
                image=image_path,
            ),
            technique_names=technique_names,
            weight=weight,
        )
        sects_by_id[sect.id] = sect
        sects_by_name[sect.name] = sect

    return sects_by_id, sects_by_name


# 导出：从配表加载 sect 数据
sects_by_id, sects_by_name = _load_sects()