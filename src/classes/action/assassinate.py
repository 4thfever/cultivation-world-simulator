from __future__ import annotations
from typing import TYPE_CHECKING
import random

from src.classes.action import InstantAction
from src.classes.action.cooldown import cooldown_action
from src.classes.event import Event
from src.classes.battle import decide_battle, get_assassination_success_rate
from src.classes.story_teller import StoryTeller
from src.classes.normalize import normalize_avatar_name
from src.classes.death import handle_death
from src.classes.death_reason import DeathReason
from src.classes.kill_and_grab import kill_and_grab

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


@cooldown_action
class Assassinate(InstantAction):
    COMMENT = "暗杀目标，失败则变为战斗"
    DOABLES_REQUIREMENTS = "任何时候都可以执行；需要冷却"
    PARAMS = {"avatar_name": "AvatarName"}
    ACTION_CD_MONTHS = 12
    
    # 成功与失败的提示词
    STORY_PROMPT_SUCCESS = (
        "这是关于一次成功的暗杀。不需要描写战斗过程，重点描写刺客如何潜伏、接近，以及最后那一击的致命与悄无声息。"
        "目标甚至没有反应过来就已经陨落。"
    )
    STORY_PROMPT_FAIL = (
        "这是关于一次失败的暗杀。刺客试图暗杀目标，但被目标敏锐地察觉了。"
        "双方随后爆发了激烈的正面冲突。"
        "不要出现具体血量数值。"
    )
    
    # 暗杀是大事（长期记忆）
    IS_MAJOR: bool = True

    def _get_target(self, avatar_name: str) -> Avatar | None:
        normalized_name = normalize_avatar_name(avatar_name)
        for v in self.world.avatar_manager.avatars.values():
            if v.name == normalized_name:
                return v
        return None

    def _execute(self, avatar_name: str) -> None:
        target = self._get_target(avatar_name)
        if target is None:
            return
            
        # 判定暗杀是否成功
        success_rate = get_assassination_success_rate(self.avatar, target)
        is_success = random.random() < success_rate
        
        self._is_assassinate_success = is_success
        
        if is_success:
            # 暗杀成功，目标直接死亡
            target.hp.current = 0
            self._last_result = None # 不需要战斗结果
        else:
            # 暗杀失败，转入正常战斗
            winner, loser, loser_damage, winner_damage = decide_battle(self.avatar, target)
            # 应用双方伤害
            loser.hp.reduce(loser_damage)
            winner.hp.reduce(winner_damage)
            
            # 增加熟练度（既然打起来了）
            proficiency_gain = random.uniform(1.0, 3.0)
            self.avatar.increase_weapon_proficiency(proficiency_gain)
            target.increase_weapon_proficiency(proficiency_gain)
            
            self._last_result = (winner, loser, loser_damage, winner_damage)

    def can_start(self, avatar_name: str | None = None) -> tuple[bool, str]:
        # 注意：cooldown_action 装饰器会覆盖这个方法并在调用此方法前检查 CD
        if avatar_name is None:
            return False, "缺少参数 avatar_name"
        ok = self._get_target(avatar_name) is not None
        return (ok, "" if ok else "目标不存在")

    def start(self, avatar_name: str) -> Event:
        target = self._get_target(avatar_name)
        target_name = target.name if target is not None else avatar_name
        
        event = Event(self.world.month_stamp, f"{self.avatar.name} 潜伏在阴影中，试图暗杀 {target_name}...", related_avatars=[self.avatar.id, target.id] if target else [self.avatar.id], is_major=True)
        self._start_event_content = event.content
        return event

    async def finish(self, avatar_name: str) -> list[Event]:
        target = self._get_target(avatar_name)
        if target is None:
            return []
            
        rel_ids = [self.avatar.id, target.id]
        
        if getattr(self, '_is_assassinate_success', False):
            # --- 暗杀成功 ---
            result_text = f"{self.avatar.name} 暗杀成功！{target.name} 在毫无防备中陨落。"
            
            # 杀人夺宝
            loot_text = await kill_and_grab(self.avatar, target)
            result_text += loot_text
            
            result_event = Event(self.world.month_stamp, result_text, related_avatars=rel_ids, is_major=True)
            
            # 生成故事
            story = await StoryTeller.tell_story(
                self._start_event_content, 
                result_event.content, 
                self.avatar, 
                target, 
                prompt=self.STORY_PROMPT_SUCCESS,
                allow_relation_changes=True
            )
            story_event = Event(self.world.month_stamp, story, related_avatars=rel_ids, is_story=True)
            
            # 死亡清理
            handle_death(self.world, target, DeathReason.BATTLE)
            
            return [result_event, story_event]
            
        else:
            # --- 暗杀失败，转入战斗 ---
            res = getattr(self, '_last_result', None)
            if not (isinstance(res, tuple) and len(res) == 4):
                return [] 
                
            winner, loser, loser_damage, winner_damage = res
            
            is_fatal = loser.hp <= 0
            
            prefix = f"暗杀失败！双方爆发激战。"
            
            if is_fatal:
                result_text = f"{prefix} {winner.name} 最终战胜并斩杀了 {loser.name} (伤害 {loser_damage})。"
                loot_text = await kill_and_grab(winner, loser)
                result_text += loot_text
            else:
                result_text = f"{prefix} {winner.name} 战胜了 {loser.name}，造成 {loser_damage} 点伤害，自身受损 {winner_damage} 点。"
            
            result_event = Event(self.world.month_stamp, result_text, related_avatars=rel_ids, is_major=True)
            
            # 生成故事
            story = await StoryTeller.tell_story(
                self._start_event_content,
                result_event.content,
                self.avatar,
                target,
                prompt=self.STORY_PROMPT_FAIL,
                allow_relation_changes=True
            )
            story_event = Event(self.world.month_stamp, story, related_avatars=rel_ids, is_story=True)
            
            if is_fatal:
                handle_death(self.world, loser, DeathReason.BATTLE)
                
            return [result_event, story_event]

