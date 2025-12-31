from __future__ import annotations
from typing import TYPE_CHECKING
import random

from src.classes.single_choice import make_decision

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


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
    
    should_loot = False
    
    # 判定是否夺取
    # 1. 如果winner当前部位为空，直接夺取
    winner_current = getattr(winner, loot_type)
    if winner_current is None :
        should_loot = True
    else:
        # 其他情况下都让 AI 决策
        # 构建详细描述，包含效果
        item_desc = loot_item.get_detailed_info()
        current_desc = winner_current.get_detailed_info()

        context = f"战斗胜利，{loser.name} 身死道消，留下了一件{loot_item.realm.value}{'兵器' if loot_type == 'weapon' else '辅助装备'}『{item_desc}』。"
        options = [
            {
                "key": "A",
                "desc": f"夺取『{loot_item.name}』，卖掉身上的『{winner_current.name}』换取灵石。\n  - 新装备：{item_desc}\n  - 原装备：{current_desc}"
            },
            {
                "key": "B",
                "desc": f"放弃『{loot_item.name}』，保留身上的『{winner_current.name}』。"
            }
        ]
        choice = await make_decision(winner, context, options)
        if choice == "A":
            should_loot = True
    
    if should_loot:
        if loot_type == "weapon":
            # 自动卖掉旧武器
            if winner.weapon is not None:
                winner.sell_weapon(winner.weapon)
            winner.change_weapon(loot_item)
            loser.change_weapon(None)
        else:
            # 自动卖掉旧辅助装备
            if winner.auxiliary is not None:
                winner.sell_auxiliary(winner.auxiliary)
            winner.change_auxiliary(loot_item)
            loser.change_auxiliary(None)
        
        return f"{winner.name}夺取了对方的{loot_item.realm.value}『{loot_item.name}』！"
    
    return ""

