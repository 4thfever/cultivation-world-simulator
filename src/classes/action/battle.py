from __future__ import annotations

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.battle import decide_battle, get_effective_strength_pair
from src.classes.story_teller import StoryTeller
from src.classes.action.event_helper import EventHelper
from src.utils.asyncio_utils import schedule_background


class Battle(InstantAction):
    COMMENT = "与目标进行对战，判定胜负"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "AvatarName"}
    # 提供用于故事生成的提示词：不出现血量/伤害等数值描述
    STORY_PROMPT: str | None = (
        "不要出现具体血量、伤害点数或任何数值表达。"
    )

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

        # 异步生成战斗小故事并在完成后推送事件，避免阻塞事件循环
        target = self._get_target(avatar_name)
        start_text = getattr(self, "_start_event_content", "") or result_event.content
        month_at_finish = self.world.month_stamp

        async def _gen_and_push_story():
            story = await StoryTeller.tell_from_actors_async(start_text, result_event.content, self.avatar, target, prompt=self.STORY_PROMPT)
            story_event = Event(month_at_finish, story, related_avatars=rel_ids)
            EventHelper.push_pair(story_event, initiator=self.avatar, target=target, to_sidebar_once=True)

        def _fallback_sync():
            story = StoryTeller.tell_from_actors(start_text, result_event.content, self.avatar, target, prompt=self.STORY_PROMPT)
            story_event = Event(month_at_finish, story, related_avatars=rel_ids)
            EventHelper.push_pair(story_event, initiator=self.avatar, target=target, to_sidebar_once=True)

        schedule_background(_gen_and_push_story(), fallback=_fallback_sync)

        return [result_event]


