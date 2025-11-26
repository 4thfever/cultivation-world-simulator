from __future__ import annotations
from typing import TYPE_CHECKING

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.battle import decide_battle, get_effective_strength_pair
from src.classes.story_teller import StoryTeller
from src.classes.normalize import normalize_avatar_name
from src.classes.death import handle_death
from src.classes.equipment_grade import EquipmentGrade
from src.classes.single_choice import make_decision
import random

if TYPE_CHECKING:
    from src.classes.avatar import Avatar
    from src.classes.weapon import Weapon
    from src.classes.auxiliary import Auxiliary


async def handle_loot(winner: Avatar, loser: Avatar) -> str:
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
        context = f"战斗胜利，{loser.name} 身死道消，留下了一件{loot_item.grade.value}{'兵器' if loot_type == 'weapon' else '辅助装备'}『{loot_item.name}』（{loot_item.desc}）。"
        options = [
            {
                "key": "A",
                "desc": f"夺取{loot_item.grade.value}『{loot_item.name}』（{loot_item.desc}），替换掉身上的『{winner_current.name}』（{winner_current.grade.value}，{winner_current.desc}）。"
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
        
        return f"并夺取了对方的{loot_item.grade.value}『{loot_item.name}』！"
    
    return ""


class Battle(InstantAction):
    COMMENT = "与目标进行对战，判定胜负"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "AvatarName"}
    # 提供用于故事生成的提示词：不出现血量/伤害等数值描述
    STORY_PROMPT: str | None = (
        "不要出现具体血量、伤害点数或任何数值表达。战斗要体现出双方的功法、境界、装备等。"
    )
    # 战斗是大事（长期记忆）
    IS_MAJOR: bool = True

    def _get_target(self, avatar_name: str):
        """
        根据名字查找目标角色；找不到返回 None。
        会自动规范化名字（去除括号等附加信息）以提高容错性。
        """
        normalized_name = normalize_avatar_name(avatar_name)
        for v in self.world.avatar_manager.avatars.values():
            if v.name == normalized_name:
                return v
        return None

    def _execute(self, avatar_name: str) -> None:
        target = self._get_target(avatar_name)
        if target is None:
            return
        winner, loser, loser_damage, winner_damage = decide_battle(self.avatar, target)
        # 应用双方伤害
        loser.hp.reduce(loser_damage)
        winner.hp.reduce(winner_damage)
        
        # 增加双方兵器熟练度（战斗经验）
        import random
        proficiency_gain = random.uniform(1.0, 3.0)
        self.avatar.increase_weapon_proficiency(proficiency_gain)
        if target is not None:
            target.increase_weapon_proficiency(proficiency_gain)
        
        self._last_result = (winner, loser, loser_damage, winner_damage)

    def can_start(self, avatar_name: str | None = None) -> tuple[bool, str]:
        if avatar_name is None:
            return False, "缺少参数 avatar_name"
        ok = self._get_target(avatar_name) is not None
        return (ok, "" if ok else "目标不存在")

    def start(self, avatar_name: str) -> Event:
        target = self._get_target(avatar_name)
        target_name = target.name if target is not None else avatar_name
        # 展示双方折算战斗力（基于对手、含克制）
        s_att, s_def = get_effective_strength_pair(self.avatar, target)
        rel_ids = [self.avatar.id]
        if target is not None:
            try:
                rel_ids.append(target.id)
            except Exception:
                pass
        event = Event(self.world.month_stamp, f"{self.avatar.name} 对 {target_name} 发起战斗（战斗力：{self.avatar.name} {int(s_att)} vs {target_name} {int(s_def)}）", related_avatars=rel_ids, is_major=True)
        # 记录开始事件内容，供故事生成使用
        self._start_event_content = event.content
        return event

    # InstantAction 已实现 step 完成

    async def finish(self, avatar_name: str) -> list[Event]:
        res = self._last_result
        if not (isinstance(res, tuple) and len(res) == 4):
            return []
        winner, loser = res[0], res[1]
        loser_damage, winner_damage = res[2], res[3]

        # 判定是否致死
        is_fatal = loser.hp <= 0
        if is_fatal:
            result_text = f"{winner.name} 战胜了 {loser.name}，造成{loser_damage}点伤害。{loser.name} 遭受重创，当场陨落。"
            
            # 杀人夺宝
            loot_text = await handle_loot(winner, loser)
            result_text += loot_text

        else:
            result_text = f"{winner.name} 战胜了 {loser.name}，{loser.name} 受伤{loser_damage}点，{winner.name} 也受伤{winner_damage}点"

        rel_ids = [self.avatar.id]
        target = self._get_target(avatar_name)
        try:
            if target is not None:
                rel_ids.append(target.id)
        except Exception:
            pass
        result_event = Event(self.world.month_stamp, result_text, related_avatars=rel_ids, is_major=True)

        # 生成战斗小故事
        start_text = self._start_event_content if hasattr(self, '_start_event_content') else result_event.content
        # 战斗强制双人模式，允许改变关系
        story = await StoryTeller.tell_story(start_text, result_event.content, self.avatar, target, prompt=self.STORY_PROMPT, allow_relation_changes=True)
        story_event = Event(self.world.month_stamp, story, related_avatars=rel_ids, is_story=True)

        # 如果死亡，执行死亡清理（在故事生成后，保证关系数据可用）
        if is_fatal:
            handle_death(self.world, loser)

        return [result_event, story_event]
