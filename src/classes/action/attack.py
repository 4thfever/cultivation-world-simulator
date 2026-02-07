from __future__ import annotations
from typing import TYPE_CHECKING

from src.i18n import t
from src.classes.action import InstantAction
from src.classes.action.targeting_mixin import TargetingMixin
from src.classes.event import Event
from src.systems.battle import decide_battle, get_effective_strength_pair
from src.utils.resolution import resolve_query

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar

class Attack(InstantAction, TargetingMixin):
    # 多语言 ID
    ACTION_NAME_ID = "attack_action_name"
    DESC_ID = "attack_description"
    REQUIREMENTS_ID = "attack_requirements"
    STORY_PROMPT_ID = "attack_story_prompt"
    
    # 不需要翻译的常量
    EMOJI = "⚔️"
    PARAMS = {"avatar_name": "AvatarName"}
    
    # 战斗是大事（长期记忆）
    IS_MAJOR: bool = True
    
    @classmethod
    def get_story_prompt(cls) -> str:
        """获取故事提示词的翻译"""
        return t(cls.STORY_PROMPT_ID)

    def _execute(self, avatar_name: str) -> None:
        from src.classes.core.avatar import Avatar
        target = resolve_query(avatar_name, self.world, expected_types=[Avatar]).obj
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

    def can_start(self, avatar_name: str) -> tuple[bool, str]:
        if not avatar_name:
            return False, t("Missing target parameter")
            
        from src.classes.core.avatar import Avatar
        target = resolve_query(avatar_name, self.world, expected_types=[Avatar]).obj
        if target is None:
            return False, t("Target does not exist")
        if target.is_dead:
            return False, t("Target is already dead")
            
        return True, ""

    def start(self, avatar_name: str) -> Event:
        from src.classes.core.avatar import Avatar
        target = resolve_query(avatar_name, self.world, expected_types=[Avatar]).obj
        target_name = target.name if target is not None else avatar_name
        # 展示双方折算战斗力（基于对手、含克制）
        s_att, s_def = get_effective_strength_pair(self.avatar, target)
        rel_ids = [self.avatar.id]
        if target is not None:
            try:
                rel_ids.append(target.id)
            except Exception:
                pass
        content = t("{attacker} initiates battle against {target} (Power: {attacker} {att_power} vs {target} {def_power})",
                   attacker=self.avatar.name, target=target_name, 
                   att_power=int(s_att), def_power=int(s_def))
        event = Event(self.world.month_stamp, content, related_avatars=rel_ids, is_major=True)
        # 记录开始事件内容，供故事生成使用
        self._start_event_content = event.content
        return event

    # InstantAction 已实现 step 完成

    async def finish(self, avatar_name: str) -> list[Event]:
        res = self._last_result
        if not (isinstance(res, tuple) and len(res) == 4):
            return []
        
        from src.classes.core.avatar import Avatar
        target = resolve_query(avatar_name, self.world, expected_types=[Avatar]).obj
        start_text = getattr(self, '_start_event_content', "")
        
        from src.systems.battle import handle_battle_finish
        return await handle_battle_finish(
            self.world,
            self.avatar,
            target,
            res,
            start_text,
            self.get_story_prompt(),
            check_loot=True
        )
