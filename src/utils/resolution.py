from typing import Any, Tuple, Optional

from src.classes.normalize import normalize_goods_name
from src.classes.elixir import elixirs_by_name
from src.classes.weapon import weapons_by_name
from src.classes.auxiliary import auxiliaries_by_name
from src.classes.item import items_by_name

def resolve_goods_by_name(target_name: str) -> Tuple[Any, str, str]:
    """
    解析物品名称，返回 (对象, 类型, 显示名称)。
    如果未找到，返回 (None, "unknown", normalized_name)。
    
    类型字符串: "elixir", "item", "weapon", "auxiliary", "unknown"
    
    查找顺序:
    1. 丹药 (Elixir)
    2. 兵器 (Weapon)
    3. 辅助装备 (Auxiliary)
    4. 普通物品 (Item)
    """
    normalized_name = normalize_goods_name(target_name)
    
    # 1. 尝试作为丹药查找
    if normalized_name in elixirs_by_name:
        # elixirs_by_name 返回的是 list，我们取第一个作为对象
        # 注意：对于购买/显示信息来说，取第一个通常是没问题的，
        # 但如果有特定逻辑需要区分同名不同境界的丹药，可能需要更精细的处理。
        # 这里保持原有逻辑。
        elixir = elixirs_by_name[normalized_name][0]
        return elixir, "elixir", elixir.name

    # 2. 尝试作为兵器查找
    weapon = weapons_by_name.get(normalized_name)
    if weapon:
        return weapon, "weapon", weapon.name

    # 3. 尝试作为辅助装备查找
    auxiliary = auxiliaries_by_name.get(normalized_name)
    if auxiliary:
        return auxiliary, "auxiliary", auxiliary.name

    # 4. 尝试作为普通物品查找
    item = items_by_name.get(normalized_name)
    if item:
        return item, "item", item.name

    return None, "unknown", normalized_name

