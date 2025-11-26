from __future__ import annotations
from typing import TYPE_CHECKING
import random

from src.classes.equipment_grade import EquipmentGrade
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
    if loser.weapon and loser.weapon.grade != EquipmentGrade.COMMON:
        loot_candidates.append(("weapon", loser.weapon))
    
    # 检查辅助装备
    if loser.auxiliary and loser.auxiliary.grade != EquipmentGrade.COMMON:
            loot_candidates.append(("auxiliary", loser.auxiliary))
    
    if not loot_candidates:
        return ""

    # 优先选法宝，其次宝物；如果有多个同级，随机选一个
    loot_candidates.sort(key=lambda x: 1 if x[1].grade == EquipmentGrade.ARTIFACT else 0, reverse=True)
    # 筛选出最高优先级的那些
    best_grade = loot_candidates[0][1].grade
    best_candidates = [c for c in loot_candidates if c[1].grade == best_grade]
    loot_type, loot_item = random.choice(best_candidates)
    
    should_loot = False
    
    # 判定是否夺取
    # 1. 如果winner当前部位为空或为凡品，直接夺取
    winner_current = getattr(winner, loot_type)
    if winner_current is None or winner_current.grade == EquipmentGrade.COMMON:
        should_loot = True
    else:
        # 2. 否则让 AI 决策
        # 构建详细描述，包含效果
        item_desc = loot_item.get_detailed_info()
        current_desc = winner_current.get_detailed_info()

        context = f"战斗胜利，{loser.name} 身死道消，留下了一件{loot_item.grade.value}{'兵器' if loot_type == 'weapon' else '辅助装备'}『{item_desc}』。"
        options = [
            {
                "key": "A",
                "desc": f"夺取『{loot_item.name}』，替换掉身上的『{winner_current.name}』。\n  - 新装备：{item_desc}\n  - 原装备：{current_desc}"
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
            winner.change_weapon(loot_item)
            from src.classes.weapon import get_common_weapon
            loser.change_weapon(get_common_weapon(loot_item.weapon_type)) # 给死者塞个凡品防止空指针
        else:
            winner.change_auxiliary(loot_item)
            loser.change_auxiliary(None)
        
        return f"{winner.name}夺取了对方的{loot_item.grade.value}『{loot_item.name}』！"
    
    return ""

