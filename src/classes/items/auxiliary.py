from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict

from src.utils.df import game_configs, get_str, get_int
from src.classes.effect import load_effect_from_str
from src.systems.cultivation import Realm
from src.classes.items.item import Item


@dataclass
class Auxiliary(Item):
    """
    辅助装备类：提供各种辅助功能的装备
    字段与 static/game_configs/auxiliary.csv 对应：
    - realm: 装备等级（练气/筑基/金丹/元婴）
    - effects: 解析为 dict，用于与 Avatar.effects 合并
    """
    id: int
    name: str
    realm: Realm
    desc: str
    effects: dict[str, object] = field(default_factory=dict)
    effect_desc: str = ""
    # 特殊属性（用于存储实例特定数据）
    special_data: dict = field(default_factory=dict)

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
        souls = ""
        if self.name == "万魂幡" and self.special_data.get("devoured_souls", 0) > 0:
            souls = t(" Devoured Souls: {count}", count=self.special_data['devoured_souls'])
        
        effect_part = t(" Effect: {effect_desc}", effect_desc=self.effect_desc) if self.effect_desc else ""
        return f"[{self.id}] {self.name}（{str(self.realm)}，{self.desc}{souls}）{effect_part}"
    
    def get_colored_info(self) -> str:
        """获取带颜色标记的信息，供前端渲染使用"""
        r, g, b = self.realm.color_rgb
        return f"<color:{r},{g},{b}>{self.get_info()}</color>"

    def get_structured_info(self) -> dict:
        full_desc = self.desc
        # 特殊数据处理
        souls = 0
        if self.name == "万魂幡":
            souls = self.special_data.get("devoured_souls", 0)
            if souls > 0:
                from src.i18n import t
                full_desc = t("{desc} (Devoured Souls: {souls})", desc=full_desc, souls=souls)

        grade_display = str(self.realm)

        return {
            "id": str(self.id),
            "name": self.name,
            "desc": full_desc,
            "type": "auxiliary",
            "color": self.realm.color_rgb,
            "effect_desc": self.effect_desc,
        }


def _load_auxiliaries_data() -> tuple[Dict[int, Auxiliary], Dict[str, Auxiliary]]:
    """从配表加载 auxiliary 数据。
    返回：新的 (按ID、按名称 的映射)。
    """
    new_by_id: Dict[int, Auxiliary] = {}
    new_by_name: Dict[str, Auxiliary] = {}

    df = game_configs.get("auxiliary")
    if df is None:
        return new_by_id, new_by_name

    for row in df:
        effects = load_effect_from_str(get_str(row, "effects"))
        from src.classes.effect import format_effects_to_text
        effect_desc = format_effects_to_text(effects)
        
        # 解析grade
        grade_str = get_str(row, "grade", "练气")
        realm = Realm.from_str(grade_str)

        a = Auxiliary(
            id=get_int(row, "item_id"),
            name=get_str(row, "name"),
            realm=realm,
            desc=get_str(row, "desc"),
            effects=effects,
            effect_desc=effect_desc,
        )

        new_by_id[a.id] = a
        new_by_name[a.name] = a
        
        # 注册到全局注册表
        from src.classes.items.registry import ItemRegistry
        ItemRegistry.register(a.id, a)

    return new_by_id, new_by_name

# 全局容器
auxiliaries_by_id: Dict[int, Auxiliary] = {}
auxiliaries_by_name: Dict[str, Auxiliary] = {}

def reload():
    """重新加载数据，保留全局字典引用"""
    new_id, new_name = _load_auxiliaries_data()
    
    auxiliaries_by_id.clear()
    auxiliaries_by_id.update(new_id)
    
    auxiliaries_by_name.clear()
    auxiliaries_by_name.update(new_name)

# 模块初始化时执行一次
reload()


def get_random_auxiliary_by_realm(realm: Realm) -> Optional[Auxiliary]:
    """获取指定境界的随机辅助装备"""
    import random
    candidates = [a for a in auxiliaries_by_id.values() if a.realm == realm]
    if not candidates:
        return None
    return random.choice(candidates).instantiate()
