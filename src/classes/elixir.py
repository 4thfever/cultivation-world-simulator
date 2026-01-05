from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from src.utils.df import game_configs, get_str, get_int
from src.classes.effect import load_effect_from_str, format_effects_to_text
from src.classes.cultivation import Realm


class ElixirType(Enum):
    """丹药类型"""
    Breakthrough = "Breakthrough"  # 破境
    Lifespan = "Lifespan"          # 延寿
    BurnBlood = "BurnBlood"        # 燃血
    Heal = "Heal"                  # 疗伤
    Unknown = "Unknown"


@dataclass
class Elixir:
    """
    丹药类
    字段与 static/game_configs/elixir.csv 对应
    """
    id: int
    name: str
    realm: Realm
    type: ElixirType
    desc: str
    price: int
    effects: dict[str, object] = field(default_factory=dict)
    effect_desc: str = ""

    def get_info(self, detailed: bool = False) -> str:
        """获取信息"""
        if detailed:
            return self.get_detailed_info()
        return f"{self.name}"

    def get_detailed_info(self) -> str:
        """获取详细信息"""
        effect_part = f" 效果：{self.effect_desc}" if self.effect_desc else ""
        return f"{self.name}（{self.realm.value}·{self._get_type_name()}，{self.desc}）{effect_part}"
    
    def _get_type_name(self) -> str:
        type_names = {
            ElixirType.Breakthrough: "破境",
            ElixirType.Lifespan: "延寿",
            ElixirType.BurnBlood: "燃血",
            ElixirType.Heal: "疗伤",
        }
        return type_names.get(self.type, "未知")

    def get_colored_info(self) -> str:
        """获取带颜色标记的信息，供前端渲染使用"""
        # 使用对应境界的颜色
        r, g, b = self.realm.color_rgb
        return f"<color:{r},{g},{b}>{self.get_info()}</color>"

    def get_structured_info(self) -> dict:
        return {
            "name": self.name,
            "desc": self.desc,
            "grade": self.realm.value,
            "type": self.type.value,
            "type_name": self._get_type_name(),
            "price": self.price,
            "color": self.realm.color_rgb,
            "effect_desc": self.effect_desc,
        }


@dataclass
class ConsumedElixir:
    """
    已服用的丹药记录
    """
    elixir: Elixir
    consume_time: int  # 服用时的 MonthStamp


def _load_elixirs() -> tuple[Dict[int, Elixir], Dict[str, List[Elixir]]]:
    """
    加载丹药配置
    :return: (id索引字典, name索引字典(值为list))
    """
    elixirs_by_id: Dict[int, Elixir] = {}
    elixirs_by_name: Dict[str, List[Elixir]] = {}
    
    if "elixir" not in game_configs:
        return elixirs_by_id, elixirs_by_name

    df = game_configs["elixir"]
    for row in df:
        elixir_id = get_int(row, "id")
        name = get_str(row, "name")
        desc = get_str(row, "desc")
        price = get_int(row, "price")
        
        # 解析境界
        realm_str = get_str(row, "realm")
        # 尝试匹配 Realm 枚举
        realm = Realm.Qi_Refinement # 默认
        for r in Realm:
            if r.value == realm_str or r.name == realm_str:
                realm = r
                break
                
        # 解析类型
        elixir_type = ElixirType(get_str(row, "type"))
            
        # 解析 effects
        effects = load_effect_from_str(get_str(row, "effects"))
        effect_desc = format_effects_to_text(effects)

        elixir = Elixir(
            id=elixir_id,
            name=name,
            realm=realm,
            type=elixir_type,
            desc=desc,
            price=price,
            effects=effects,
            effect_desc=effect_desc
        )

        elixirs_by_id[elixir_id] = elixir
        
        if name not in elixirs_by_name:
            elixirs_by_name[name] = []
        elixirs_by_name[name].append(elixir)

    return elixirs_by_id, elixirs_by_name


# 导出全局变量
elixirs_by_id, elixirs_by_name = _load_elixirs()
