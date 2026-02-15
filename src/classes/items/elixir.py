from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Union, Optional

from src.utils.df import game_configs, get_str, get_int
from src.classes.effect import load_effect_from_str, format_effects_to_text
from src.systems.cultivation import Realm
from src.classes.items.item import Item


class ElixirType(Enum):
    """丹药类型"""
    Breakthrough = "Breakthrough"  # 破境
    Lifespan = "Lifespan"          # 延寿
    BurnBlood = "BurnBlood"        # 燃血
    Heal = "Heal"                  # 疗伤
    Unknown = "Unknown"


@dataclass
class Elixir(Item):
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
    effects: Union[dict[str, object], list[dict[str, object]]] = field(default_factory=dict)
    effect_desc: str = ""

    def __hash__(self):
        return hash(self.id)

    def get_info(self, detailed: bool = False) -> str:
        """获取信息"""
        if detailed:
            return self.get_detailed_info()
        return f"{self.name}"

    def get_detailed_info(self) -> str:
        """获取详细信息"""
        from src.i18n import t
        effect_part = t(" Effect: {effect_desc}", effect_desc=self.effect_desc) if self.effect_desc else ""
        return f"{self.name}（{str(self.realm)}·{self._get_type_name()}，{self.desc}）{effect_part}"
    
    def _get_type_name(self) -> str:
        from src.i18n import t
        type_name_ids = {
            ElixirType.Breakthrough: "elixir_type_breakthrough",
            ElixirType.Lifespan: "elixir_type_lifespan",
            ElixirType.BurnBlood: "elixir_type_burn_blood",
            ElixirType.Heal: "elixir_type_heal",
        }
        msgid = type_name_ids.get(self.type, "Unknown")
        return t(msgid)

    def get_colored_info(self) -> str:
        """获取带颜色标记的信息，供前端渲染使用"""
        # 使用对应境界的颜色
        r, g, b = self.realm.color_rgb
        return f"<color:{r},{g},{b}>{self.get_info()}</color>"

    def get_structured_info(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "desc": self.desc,
            "grade": str(self.realm),
            "type": "elixir",
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
    _expire_time: Union[int, float] = field(init=False)

    def __post_init__(self):
        self._expire_time = self.consume_time + self._get_max_duration()

    def _get_max_duration(self) -> Union[int, float]:
        """获取丹药的最长持续时间"""
        effects = self.elixir.effects
        if isinstance(effects, dict):
            effects = [effects]
        
        max_d = 0
        for eff in effects:
            # 如果没有 duration_month 字段，视为永久效果
            if "duration_month" not in eff:
                return float('inf')
            max_d = max(max_d, int(eff.get("duration_month", 0)))
        return max_d

    def is_completely_expired(self, current_month: int) -> bool:
        """
        判断丹药是否彻底失效（所有效果都过期）
        """
        return current_month >= self._expire_time

    def get_active_effects(self, current_month: int) -> List[dict[str, object]]:
        """
        获取当前时间点仍然有效的 effects 列表
        """
        active = []
        effects = self.elixir.effects
        if isinstance(effects, dict):
            effects = [effects]
        
        for eff in effects:
            # 永久效果
            if "duration_month" not in eff:
                active.append(eff)
                continue
            
            # 有时限效果
            duration = int(eff.get("duration_month", 0))
            if duration > 0:
                if current_month < self.consume_time + duration:
                    active.append(eff)
        
        return active


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
            id=get_int(row, "item_id"),
            name=name,
            realm=realm,
            type=elixir_type,
            desc=desc,
            price=price,
            effects=effects,
            effect_desc=effect_desc
        )

        elixirs_by_id[elixir.id] = elixir
        
        if name not in elixirs_by_name:
            elixirs_by_name[name] = []
        elixirs_by_name[name].append(elixir)
        
        # 注册到全局注册表
        from src.classes.items.registry import ItemRegistry
        ItemRegistry.register(elixir.id, elixir)

    return elixirs_by_id, elixirs_by_name


elixirs_by_id: Dict[int, Elixir] = {}
elixirs_by_name: Dict[str, List[Elixir]] = {}

def reload():
    """重新加载数据"""
    new_id, new_name = _load_elixirs()
    
    elixirs_by_id.clear()
    elixirs_by_id.update(new_id)
    
    elixirs_by_name.clear()
    elixirs_by_name.update(new_name)

# 模块初始化时执行一次
reload()


def get_elixirs_by_realm(realm: Realm) -> List[Elixir]:
    """获取指定境界的所有丹药"""
    return [e for e in elixirs_by_id.values() if e.realm == realm]


def get_random_elixir_by_realm(realm: Realm) -> Optional[Elixir]:
    """获取指定境界的随机丹药"""
    candidates = get_elixirs_by_realm(realm)
    if not candidates:
        return None
    return random.choice(candidates).instantiate()
