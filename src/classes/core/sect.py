from dataclasses import dataclass, field
from pathlib import Path
import json

from src.classes.alignment import Alignment
from src.utils.df import game_configs, get_str, get_float, get_int
from src.classes.effect import load_effect_from_str
from src.classes.core.orthodoxy import get_orthodoxy
from src.utils.config import CONFIG

from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.technique import Technique
    from src.classes.sect_ranks import SectRank
    from src.classes.weapon_type import WeaponType

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
    # 宗门倾向的兵器类型
    preferred_weapon: Optional["WeaponType"] = None
    # 影响角色或系统的效果
    effects: dict[str, object] = field(default_factory=dict)
    effect_desc: str = ""
    # 宗门自定义职位名称（可选）：SectRank -> 名称
    rank_names: dict[str, str] = field(default_factory=dict)
    # 道统ID
    orthodoxy_id: str = "dao"
    
    # 运行时成员列表：Avatar ID -> Avatar
    members: dict[str, "Avatar"] = field(default_factory=dict, init=False)
    # 功法对象列表：Technique
    techniques: list["Technique"] = field(default_factory=list, init=False)

    def __post_init__(self):
        self.members = {}
        self.techniques = []

    def add_member(self, avatar: "Avatar") -> None:
        """添加成员到宗门"""
        if avatar.id not in self.members:
            self.members[avatar.id] = avatar
    
    def remove_member(self, avatar: "Avatar") -> None:
        """从宗门移除成员"""
        if avatar.id in self.members:
            del self.members[avatar.id]

    def get_info(self) -> str:
        from src.i18n import t
        hq = self.headquarter
        orthodoxy = get_orthodoxy(self.orthodoxy_id)
        orthodoxy_name = t(orthodoxy.name) if orthodoxy else self.orthodoxy_id
        return t("{sect_name} (Orthodoxy: {orthodoxy}, Alignment: {alignment}, Headquarters: {hq_name})",
                sect_name=self.name, orthodoxy=orthodoxy_name, alignment=str(self.alignment), hq_name=hq.name)

    def get_detailed_info(self) -> str:
        # 详细描述：风格、阵营、驻地
        from src.i18n import t
        hq = self.headquarter
        effect_part = t(" Effect: {effect_desc}", effect_desc=self.effect_desc) if self.effect_desc else ""
        
        orthodoxy = get_orthodoxy(self.orthodoxy_id)
        orthodoxy_name = t(orthodoxy.name) if orthodoxy else self.orthodoxy_id
        
        return t("{sect_name} (Orthodoxy: {orthodoxy}, Alignment: {alignment}, Style: {style}, Headquarters: {hq_name}){effect}",
                sect_name=self.name, orthodoxy=orthodoxy_name, alignment=str(self.alignment), 
                style=t(self.member_act_style), hq_name=hq.name, effect=effect_part)
    
    def get_rank_name(self, rank: "SectRank") -> str:
        """
        获取宗门的职位名称（支持自定义）
        
        Args:
            rank: 宗门职位枚举
            
        Returns:
            职位名称字符串
        """
        from src.classes.sect_ranks import SectRank, DEFAULT_RANK_NAMES
        from src.i18n import t
        # 优先使用自定义名称，否则使用默认名称
        val = self.rank_names.get(rank.value, DEFAULT_RANK_NAMES.get(rank, t("Disciple")))
        return t(val)

    def get_structured_info(self) -> dict:
        hq = self.headquarter
        from src.i18n import t
        from src.classes.sect_ranks import RANK_ORDER
        from src.server.main import resolve_avatar_pic_id
        from src.classes.technique import techniques_by_name
        
        # 成员列表：直接从 self.members 获取
        members_list = []
        for a in self.members.values():
            rank_enum = getattr(a, "sect_rank", None)
            sort_val = 999
            if rank_enum and rank_enum in RANK_ORDER:
                sort_val = RANK_ORDER[rank_enum]
                
            members_list.append({
                "id": str(a.id),
                "name": a.name,
                "pic_id": resolve_avatar_pic_id(a),
                "gender": a.gender.value if hasattr(a.gender, "value") else "male",
                "rank": a.get_sect_rank_name(),
                "realm": a.cultivation_progress.get_info() if hasattr(a, 'cultivation_progress') else t("Unknown"),
                "_sort_val": sort_val
            })
        # 按职位排序
        members_list.sort(key=lambda x: x["_sort_val"])
        # 清理排序字段
        for m in members_list:
            del m["_sort_val"]

        # 填充 techniques
        # 使用 technique_names 从全局字典中查找对应的 Technique 对象并序列化
        techniques_data = []
        for t_name in self.technique_names:
            t_obj = techniques_by_name.get(t_name)
            if t_obj:
                techniques_data.append(t_obj.get_structured_info())
            else:
                # Fallback for missing techniques: create a minimal structure
                techniques_data.append({
                    "name": t_name,
                    "desc": t("(Unknown technique)"),
                    "grade": "",
                    "color": (200, 200, 200), # Gray
                    "attribute": "",
                    "effect_desc": ""
                })

        orthodoxy = get_orthodoxy(self.orthodoxy_id)

        return {
            "id": self.id,
            "name": self.name,
            "desc": self.desc,
            "alignment": str(self.alignment), # 直接返回中文
            "style": t(self.member_act_style),
            "hq_name": hq.name,
            "hq_desc": hq.desc,
            "effect_desc": self.effect_desc,
            "techniques": techniques_data,
            # 兼容旧字段，如果前端还要用的话（建议迁移后废弃）
            "technique_names": self.technique_names,
            "preferred_weapon": str(self.preferred_weapon) if self.preferred_weapon else "",
            "members": members_list,
            "orthodoxy": orthodoxy.get_info(detailed=True) if orthodoxy else {"id": self.orthodoxy_id}
        }

def _split_names(value: object) -> list[str]:
    raw = "" if value is None or str(value) == "nan" else str(value)
    sep = CONFIG.df.ids_separator
    parts = [x.strip() for x in raw.split(sep) if x.strip()] if raw else []
    return parts

def _merge_effects_dict(base: dict[str, object], addition: dict[str, object]) -> dict[str, object]:
    """合并两个 effects 字典（简单合并逻辑）"""
    if not base and not addition:
        return {}
    merged: dict[str, object] = dict(base) if base else {}
    for key, val in (addition or {}).items():
        if key in merged:
            old = merged[key]
            if isinstance(old, list) and isinstance(val, list):
                # 去重并集
                seen = set(old)
                result = list(old)
                for x in val:
                    if x not in seen:
                        seen.add(x)
                        result.append(x)
                merged[key] = result
            elif isinstance(old, (int, float)) and isinstance(val, (int, float)):
                merged[key] = old + val
            else:
                # 默认覆盖
                merged[key] = val
        else:
            merged[key] = val
    return merged

def _load_sects_data() -> tuple[dict[int, Sect], dict[str, Sect]]:
    """从配表加载 sect 数据
    返回：新的 (sects_by_id, sects_by_name)
    """
    new_by_id: dict[int, Sect] = {}
    new_by_name: dict[str, Sect] = {}

    df = game_configs["sect"]
    # 读取宗门驻地映射（优先从 sect_region.csv 获取驻地地名/描述）
    sect_region_df = game_configs.get("sect_region")
    hq_by_sect_id: dict[int, tuple[str, str]] = {}
    if sect_region_df is not None:
        for sr in sect_region_df:
            sid = get_int(sr, "sect_id", -1)
            if sid == -1:
                continue
            hq_name = get_str(sr, "name")
            hq_desc = get_str(sr, "desc")
            hq_by_sect_id[sid] = (hq_name, hq_desc)
    
    # 可能不存在 technique 配表或未添加 sect 列，做容错
    tech_df = game_configs.get("technique")
    assets_base = Path("assets/sects")
    
    for row in df:
        name = get_str(row, "name")
        image_path = assets_base / f"{name}.png"
        
        # 先读取当前宗门 ID，供后续使用
        sid = get_int(row, "id")

        # 收集该宗门下配置的功法名称
        technique_names: list[str] = []
        # 检查 tech_df 是否存在以及是否有数据
        if tech_df:
            technique_names = [
                get_str(t, "name")
                for t in tech_df
                if get_int(t, "sect_id") == sid and get_str(t, "name")
            ]

        weight = get_float(row, "weight", 1.0)

        # 读取 effects
        base_effects = load_effect_from_str(get_str(row, "effects"))
        
        # 道统处理
        orthodoxy_id = get_str(row, "orthodoxy_id") or "dao"
        orthodoxy = get_orthodoxy(orthodoxy_id)
        
        # 合并道统 Effects 到宗门 Effects
        final_effects = base_effects
        if orthodoxy and orthodoxy.effects:
             # 以道统为基础，宗门效果叠加/覆盖之
             final_effects = _merge_effects_dict(orthodoxy.effects, base_effects)
        
        from src.classes.effect import format_effects_to_text
        effect_desc = format_effects_to_text(final_effects)

        # 读取倾向兵器类型
        from src.classes.weapon_type import WeaponType
        preferred_weapon_str = get_str(row, "preferred_weapon")
        preferred_weapon = WeaponType.from_str(preferred_weapon_str) if preferred_weapon_str else None

        # 解析自定义职位
        raw_ranks = get_str(row, "rank_names")
        rank_names_map = {}
        if raw_ranks:
            # 格式：掌门;长老;内门;外门
            parts = [x.strip() for x in raw_ranks.split(";") if x.strip()]
            if len(parts) == 4:
                from src.classes.sect_ranks import SectRank
                rank_names_map = {
                    SectRank.Patriarch.value: parts[0],
                    SectRank.Elder.value: parts[1],
                    SectRank.InnerDisciple.value: parts[2],
                    SectRank.OuterDisciple.value: parts[3],
                }

        # 从 sect_region.csv 中优先取驻地名称/描述；否则兼容旧列或退回宗门名
        csv_hq = hq_by_sect_id.get(sid)
        hq_name_from_csv = (csv_hq[0] if csv_hq else "").strip() if csv_hq else ""
        hq_desc_from_csv = (csv_hq[1] if csv_hq else "").strip() if csv_hq else ""

        hq_name = hq_name_from_csv or get_str(row, "headquarter_name") or name
        hq_desc = hq_desc_from_csv or get_str(row, "headquarter_desc")

        sect = Sect(
            id=sid,
            name=name,
            desc=get_str(row, "desc"),
            member_act_style=get_str(row, "member_act_style"),
            alignment=Alignment.from_str(get_str(row, "alignment")),
            headquarter=SectHeadQuarter(
                name=hq_name,
                desc=hq_desc,
                image=image_path,
            ),
            technique_names=technique_names,
            weight=weight,
            preferred_weapon=preferred_weapon,
            effects=final_effects,
            effect_desc=effect_desc,
            rank_names=rank_names_map,
            orthodoxy_id=orthodoxy_id,
        )
        new_by_id[sect.id] = sect
        new_by_name[sect.name] = sect

    return new_by_id, new_by_name

# 全局容器（保持引用不变）
sects_by_id: dict[int, Sect] = {}
sects_by_name: dict[str, Sect] = {}

def reload():
    """重新加载数据，保留全局字典引用"""
    new_id, new_name = _load_sects_data()
    
    sects_by_id.clear()
    sects_by_id.update(new_id)
    
    sects_by_name.clear()
    sects_by_name.update(new_name)

# 模块初始化时执行一次
reload()


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
        from src.classes.core.avatar import Avatar
    
    # 散修直接返回
    from src.i18n import t
    if avatar.sect is None:
        return t("Rogue Cultivator")
    
    # 获取职位+宗门名（如"明心剑宗长老"）
    sect_rank_str = avatar.get_sect_str()
    
    # 如果不需要详细信息，直接返回职位字符串
    if not detailed:
        return sect_rank_str
    
    # 需要详细信息：拼接宗门的详细描述
    # 不解析字符串，而是重新构造
    hq = avatar.sect.headquarter
    effect_part = t(" Effect: {effect_desc}", effect_desc=avatar.sect.effect_desc) if avatar.sect.effect_desc else ""
    
    # 构造详细信息，使用标准空格和括号
    orthodoxy = get_orthodoxy(avatar.sect.orthodoxy_id)
    orthodoxy_name = t(orthodoxy.name) if orthodoxy else avatar.sect.orthodoxy_id
    
    detail_content = t("(Orthodoxy: {orthodoxy}, Alignment: {alignment}, Style: {style}, Headquarters: {hq_name}){effect}",
                       orthodoxy=orthodoxy_name,
                       alignment=avatar.sect.alignment, 
                       style=t(avatar.sect.member_act_style), 
                       hq_name=hq.name, 
                       effect=effect_part)
    
    return f"{sect_rank_str} {detail_content}"
