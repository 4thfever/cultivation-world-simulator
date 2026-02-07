from __future__ import annotations
from typing import TYPE_CHECKING
import random

from src.classes.single_choice import handle_item_exchange

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


async def kill_and_grab(winner: Avatar, loser: Avatar) -> str:
    """
    处理杀人夺宝逻辑
    
    Args:
        winner: 胜利者
        loser: 失败者（已死亡）
        
    Returns:
        str: 夺宝结果描述文本（如"并夺取了..."），如果没有夺取则为空字符串
    """
    loot_candidates = []
    
    # 检查兵器
    if loser.weapon:
        loot_candidates.append(("weapon", loser.weapon))
    
    # 检查辅助装备
    if loser.auxiliary:
        loot_candidates.append(("auxiliary", loser.auxiliary))
    
    if not loot_candidates:
        return ""

    # 优先高境界
    loot_candidates.sort(key=lambda x: x[1].realm, reverse=True)
    # 筛选出最高优先级的那些
    best_realm = loot_candidates[0][1].realm
    best_candidates = [c for c in loot_candidates if c[1].realm == best_realm]
    loot_type, loot_item = random.choice(best_candidates)
    
    # 判定是否夺取
    item_label = '兵器' if loot_type == 'weapon' else '辅助装备'
    # 使用 str() 来触发 Realm 的 __str__ 方法进行 i18n 翻译。
    context = f"战斗胜利，{loser.name} 身死道消，留下了一件{str(loot_item.realm)}{item_label}『{loot_item.name}』。"
    
    swapped, log_text = await handle_item_exchange(
        avatar=winner,
        new_item=loot_item,
        item_type=loot_type,
        context_intro=context,
        can_sell_new=False
    )

    if swapped:
        if loot_type == "weapon":
            loser.change_weapon(None)
        else:
            loser.change_auxiliary(None)
        
        return f"缴获了{item_label}『{loot_item.name}』。{log_text}"
    
    return ""
