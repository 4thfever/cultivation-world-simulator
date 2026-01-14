from __future__ import annotations

import random
from pathlib import Path
from typing import TYPE_CHECKING

from .mutual_action import MutualAction
from src.classes.action.cooldown import cooldown_action
from src.classes.event import Event
from src.classes.story_teller import StoryTeller
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


@cooldown_action
class DualCultivation(MutualAction):
    """双修：合欢宗弟子可与交互范围内的修士尝试双修。

    - 仅限发起方为合欢宗成员
    - 仅当目标在交互范围内
    - 目标可以选择 接受 或 拒绝
    - 若接受：发起者获得大量修为（约为修炼的 3~5 倍，随对方等级浮动），目标不获得修为
    - 成功进入后生成一段"恋爱/双修"的小故事
    """

    ACTION_NAME = "双修"
    EMOJI = "💕"
    DESC = "以情入道的双修之术，仅合欢宗弟子可发起，对象可接受或拒绝"
    DOABLES_REQUIREMENTS = "发起者为合欢宗；目标在交互范围内；不能连续执行"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS = ["Accept", "Reject"]
    # 提供用于故事生成的提示词，供 StoryTeller 模板参考
    STORY_PROMPT: str | None = "两位修士在双修过程中情愫暗生，以含蓄、雅致的文字描绘一段暧昧而不露骨的双修体验，体现彼此性格、境界差异与甜蜜的恋爱时光。不要体现经验的数值。"
    # 双修的社交冷却：避免频繁请求
    ACTION_CD_MONTHS: int = 3
    # 双修是大事（长期记忆）
    IS_MAJOR: bool = True

    def _get_template_path(self) -> Path:
        # 复用 mutual_action 模板，仅需返回 Accept/Reject
        return CONFIG.paths.templates / "mutual_action.txt"

    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """检查双修特有的启动条件"""
        return True, ""

    def start(self, target_avatar: "Avatar|str") -> Event:
        target = self._get_target_avatar(target_avatar)
        target_name = target.name if target is not None else str(target_avatar)
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
            
        event = Event(self.world.month_stamp, f"{self.avatar.name} 邀请 {target_name} 进行双修", related_avatars=rel_ids, is_major=True)
        
        # 记录开始文本用于故事生成
        self._start_event_content = event.content
        # 初始化内部标记，避免后续 getattr
        self._dual_cultivation_success = False
        self._dual_exp_gain = 0
        return event

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        fb = str(feedback_name).strip()
        if fb == "Accept":
            # 接受则当场结算修为收益（发起者获得，对象不获得），并记录标记供 finish 生成故事
            self._apply_dual_cultivation_gain(self.avatar, target_avatar)
            self._dual_cultivation_success = True
        else:
            # 拒绝
            self._dual_cultivation_success = False

    def _apply_dual_cultivation_gain(self, initiator: "Avatar", target: "Avatar") -> None:
        # 以“修炼”的基础经验为参照：base=100 * essence_density
        # 由于此处不依赖具体修炼区域灵气，取一个稳定的基准值：视为 essence_density=1 的基础；
        # 然后按对方等级决定 3~5 倍之间的倍数。
        base = 100
        # 对方等级越高，倍数越高（3.0 ~ 5.0），做一个线性映射并夹紧
        other_level = target.cultivation_progress.level
        factor = 3.0 + min(2.0, max(0.0, other_level / 60.0 * 2.0))  # level 0-120 -> +0~4，但上限5
        # 添加少量抖动，避免过度稳定
        jitter = random.uniform(-0.2, 0.2)
        factor = max(3.0, min(5.0, factor + jitter))
        exp_gain = int(base * factor)
        # 附加“双修经验提升”效果（如法宝）
        extra_raw = initiator.effects.get("extra_dual_cultivation_exp", 0)
        extra = int(extra_raw or 0)
        exp_gain += extra
        initiator.cultivation_progress.add_exp(exp_gain)
        self._dual_exp_gain = exp_gain

    async def finish(self, target_avatar: "Avatar|str") -> list[Event]:
        target = self._get_target_avatar(target_avatar)
        events: list[Event] = []
        success = self._dual_cultivation_success
        if target is None:
            return events

        if success:
            gain = int(self._dual_exp_gain)
            result_text = f"{self.avatar.name} 获得修为经验 +{gain} 点"
            result_event = Event(self.world.month_stamp, result_text, related_avatars=[self.avatar.id, target.id], is_major=True)
            
            events.append(result_event)

            # 生成恋爱/双修小故事
            start_text = self._start_event_content or result_event.content
            # 双修强制双人模式，允许改变关系
            story = await StoryTeller.tell_story(start_text, result_event.content, self.avatar, target, prompt=self.STORY_PROMPT, allow_relation_changes=True)
            story_event = Event(self.world.month_stamp, story, related_avatars=[self.avatar.id, target.id], is_story=True)
            
            events.append(story_event)

        return events
