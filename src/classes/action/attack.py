from __future__ import annotations
from typing import TYPE_CHECKING

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.battle import decide_battle, get_effective_strength_pair
from src.classes.story_teller import StoryTeller
from src.classes.normalize import normalize_avatar_name
from src.classes.death import handle_death
from src.classes.death_reason import DeathReason
from src.classes.kill_and_grab import kill_and_grab

class Attack(InstantAction):
    ACTION_NAME = "发起战斗"
    DESC = "攻击目标，进行对战"
    DOABLES_REQUIREMENTS = "无限制"
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
        
        target = self._get_target(avatar_name)
        start_text = getattr(self, '_start_event_content', "")
        
        from src.classes.battle import handle_battle_finish
        return await handle_battle_finish(
            self.world,
            self.avatar,
            target,
            res,
            start_text,
            self.STORY_PROMPT,
            check_loot=True
        )
