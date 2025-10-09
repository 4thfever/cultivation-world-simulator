from __future__ import annotations

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.battle import decide_battle
from src.classes.story_teller import StoryTeller


class Battle(InstantAction):
    COMMENT = "与目标进行对战，判定胜负"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "AvatarName"}

    def _get_target(self, avatar_name: str):
        for v in self.world.avatar_manager.avatars.values():
            if v.name == avatar_name:
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
        self._last_result = (winner.name, loser.name, loser_damage, winner_damage)

    def can_start(self, avatar_name: str | None = None) -> bool:
        if avatar_name is None:
            return False
        return self._get_target(avatar_name) is not None

    def start(self, avatar_name: str) -> Event:
        target = self._get_target(avatar_name)
        target_name = target.name if target is not None else avatar_name
        event = Event(self.world.month_stamp, f"{self.avatar.name} 对 {target_name} 发起战斗")
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
        result_event = Event(self.world.month_stamp, result_text)

        # 生成战斗小故事：直接复用已生成的事件文本
        target = self._get_target(avatar_name)
        avatar_infos = StoryTeller.build_avatar_infos(self.avatar, target)
        start_text = getattr(self, "_start_event_content", "") or result_event.content
        story = StoryTeller.tell_story(avatar_infos, start_text, result_event.content)
        story_event = Event(self.world.month_stamp, story)
        return [result_event, story_event]


