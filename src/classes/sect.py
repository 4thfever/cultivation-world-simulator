from dataclasses import dataclass, field
from pathlib import Path
import json

from src.classes.alignment import Alignment
from src.utils.df import game_configs
from src.classes.effect import load_effect_from_str
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
    headquarter: SectHeadQuarter
    # 本宗关联的功法名称（来自 technique.csv 的 sect 列）
    technique_names: list[str]
    # 随机选择宗门时使用的权重（默认1）
    weight: float = 1.0
    # 宗门倾向的兵器类型（字符串，如"剑"、"刀"等）
    preferred_weapon: str = ""
    # 影响角色或系统的效果
    effects: dict[str, object] = field(default_factory=dict)
    # 宗门自定义职位名称（可选）：SectRank -> 名称
    rank_names: dict[str, str] = field(default_factory=dict)

    def get_info(self) -> str:
        hq = self.headquarter
        return f"{self.name}（阵营：{self.alignment}，驻地：{hq.name}）"

    def get_detailed_info(self) -> str:
        # 详细描述：风格、阵营、驻地
        hq = self.headquarter
        return f"{self.name}（阵营：{self.alignment}，风格：{self.member_act_style}，驻地：{hq.name}）"
    
    def get_rank_name(self, rank: "SectRank") -> str:
        """
        获取宗门的职位名称（支持自定义）
        
        Args:
            rank: 宗门职位枚举
            
        Returns:
            职位名称字符串
        """
        from src.classes.sect_ranks import SectRank, DEFAULT_RANK_NAMES
        # 优先使用自定义名称，否则使用默认名称
        return self.rank_names.get(rank.value, DEFAULT_RANK_NAMES.get(rank, "弟子"))
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
    # 读取宗门驻地映射（优先从 sect_region.csv 获取驻地地名/描述）
    sect_region_df = game_configs.get("sect_region")
    hq_by_sect_id: dict[int, tuple[str, str]] = {}
    if sect_region_df is not None:
        for _, sr in sect_region_df.iterrows():
            sid_str = str(sr.get("sect_id", "")).strip()
            # 跳过说明行或空值
            if not sid_str.isdigit():
                continue
            sid = int(sid_str)
            hq_name = str(sr.get("headquarter_name", "")).strip()
            hq_desc = str(sr.get("headquarter_desc", "")).strip()
            hq_by_sect_id[sid] = (hq_name, hq_desc)
    # 可能不存在 technique 配表或未添加 sect 列，做容错
    tech_df = game_configs.get("technique")
    assets_base = Path("assets/sects")
    for _, row in df.iterrows():
        image_path = assets_base / f"{row['name']}.png"

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

        # 读取 effects（兼容 JSON/单引号字面量/空）
        effects = load_effect_from_str(row.get("effects", ""))

        # 读取倾向兵器类型
        preferred_weapon_val = row.get("preferred_weapon", "")
        preferred_weapon = str(preferred_weapon_val).strip() if str(preferred_weapon_val) != "nan" else ""

        # 从 sect_region.csv 中优先取驻地名称/描述；否则兼容旧列或退回宗门名
        csv_hq = hq_by_sect_id.get(int(row["id"]))
        hq_name_from_csv = (csv_hq[0] if csv_hq else "").strip() if csv_hq else ""
        hq_desc_from_csv = (csv_hq[1] if csv_hq else "").strip() if csv_hq else ""

        sect = Sect(
            id=int(row["id"]),
            name=str(row["name"]),
            desc=str(row["desc"]),
            member_act_style=str(row["member_act_style"]),
            alignment=Alignment.from_str(row["alignment"]),
            # 驻地：优先 sect_region.csv；否则兼容旧列；最终回退宗门名
            headquarter=SectHeadQuarter(
                name=(hq_name_from_csv or str(row.get("headquarter_name", "")).strip() or str(row["name"])) ,
                desc=(hq_desc_from_csv or str(row.get("headquarter_desc", ""))),
                image=image_path,
            ),
            technique_names=technique_names,
            weight=weight,
            preferred_weapon=preferred_weapon,
            effects=effects,
        )
        sects_by_id[sect.id] = sect
        sects_by_name[sect.name] = sect

    return sects_by_id, sects_by_name


# 导出：从配表加载 sect 数据
sects_by_id, sects_by_name = _load_sects()


def get_sect_info_with_rank(avatar: "Avatar", detailed: bool = False) -> str:
    """
    获取包含职位的宗门信息字符串
    
    Args:
        avatar: 角色对象
        detailed: 是否包含宗门详细信息（阵营、风格、驻地等）
        
    Returns:
        - 散修：返回"散修"
        - detailed=False：返回"明心剑宗长老"
        - detailed=True：返回"明心剑宗长老（阵营：正，风格：...，驻地：...）"
    """
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from src.classes.avatar import Avatar
    
    # 散修直接返回
    if avatar.sect is None:
        return "散修"
    
    # 获取职位+宗门名（如"明心剑宗长老"）
    sect_rank_str = avatar.get_sect_str()
    
    # 如果不需要详细信息，直接返回职位字符串
    if not detailed:
        return sect_rank_str
    
    # 需要详细信息：拼接宗门的详细描述
    sect_detail = avatar.sect.get_detailed_info()  # "明心剑宗（阵营：正，...）"
    
    # 提取括号及其内容
    if "（" in sect_detail:
        detail_part = sect_detail[sect_detail.index("（"):]
        return f"{sect_rank_str}{detail_part}"
    
    # 如果没有括号（理论上不应该出现），直接返回职位字符串
    return sect_rank_str