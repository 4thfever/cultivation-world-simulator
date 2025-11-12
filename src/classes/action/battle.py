from __future__ import annotations

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.battle import decide_battle, get_effective_strength_pair
from src.classes.story_teller import StoryTeller
from src.classes.normalize import normalize_avatar_name


class Battle(InstantAction):
    COMMENT = "与目标进行对战，判定胜负"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "AvatarName"}
    # 提供用于故事生成的提示词：不出现血量/伤害等数值描述
    STORY_PROMPT: str | None = (
        "不要出现具体血量、伤害点数或任何数值表达。"
    )

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
        
        self._last_result = (winner.name, loser.name, loser_damage, winner_damage)

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
        event = Event(self.world.month_stamp, f"{self.avatar.name} 对 {target_name} 发起战斗（战斗力：{self.avatar.name} {int(s_att)} vs {target_name} {int(s_def)}）", related_avatars=rel_ids)
        # 记录开始事件内容，供故事生成使用
        self._start_event_content = event.content
        return event

    # InstantAction 已实现 step 完成

    def finish(self, avatar_name: str) -> list[Event]:
        res = self._last_result
        if not (isinstance(res, tuple) and len(res) == 4):
            return []
        winner, loser = res[0], res[1]
        loser_damage, winner_damage = res[2], res[3]
        result_text = f"{winner} 战胜了 {loser}，{loser} 受伤{loser_damage}点，{winner} 也受伤{winner_damage}点"
        rel_ids = [self.avatar.id]
        try:
            t = self._get_target(avatar_name)
            if t is not None:
                rel_ids.append(t.id)
        except Exception:
            pass
        result_event = Event(self.world.month_stamp, result_text, related_avatars=rel_ids)

        # 生成战斗小故事（同步调用，与其他动作保持一致）
        target = self._get_target(avatar_name)
        start_text = getattr(self, "_start_event_content", "") or result_event.content
        story = StoryTeller.tell_from_actors(start_text, result_event.content, self.avatar, target, prompt=self.STORY_PROMPT)
        story_event = Event(self.world.month_stamp, story, related_avatars=rel_ids)

        return [result_event, story_event]


