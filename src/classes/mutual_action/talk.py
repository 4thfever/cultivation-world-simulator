from __future__ import annotations

from typing import TYPE_CHECKING

from src.i18n import t
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.event import Event
from src.classes.action.event_helper import EventHelper

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar

from .mutual_action import MutualAction


class Talk(MutualAction):
    """
    攀谈：向交互范围内的某个NPC发起攀谈。
    - 接受后自动进入 Conversation
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "talk_action_name"
    DESC_ID = "talk_description"
    REQUIREMENTS_ID = "talk_requirements"
    
    # 不需要翻译的常量
    EMOJI = "👋"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS: list[str] = ["Talk", "Reject"]
    
    # 自定义反馈标签
    FEEDBACK_LABEL_IDS: dict[str, str] = {
        "Talk": "feedback_talk",
        "Reject": "feedback_reject",
    }
    
    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """攀谈无额外检查条件"""
        from src.classes.observe import is_within_observation
        if not is_within_observation(self.avatar, target):
            return False, t("Target not within interaction range")
        return True, ""
    
    def _handle_feedback_result(self, target: "Avatar", result: dict) -> ActionResult:
        """
        处理 LLM 返回的反馈结果。
        """
        feedback = str(result.get("feedback", "")).strip()
        
        events_to_return = []
        
        # 处理反馈
        if feedback == "Talk":
            # 接受攀谈，自动进入 Conversation
            content = t("{target} accepted {initiator}'s talk invitation",
                       target=target.name, initiator=self.avatar.name)
            accept_event = Event(
                self.world.month_stamp, 
                content, 
                related_avatars=[self.avatar.id, target.id]
            )
            
            events_to_return.append(accept_event)
            
            # 将 Conversation 加入计划队列并立即提交
            self.avatar.load_decide_result_chain(
                [("Conversation", {"target_avatar": target.name})],
                self.avatar.thinking,
                self.avatar.short_term_objective,
                prepend=True
            )
            # 立即提交为当前动作
            start_event = self.avatar.commit_next_plan()
            if start_event is not None:
                pass

        else:
            # 拒绝攀谈
            content = t("{target} rejected {initiator}'s talk invitation",
                       target=target.name, initiator=self.avatar.name)
            reject_event = Event(
                self.world.month_stamp, 
                content, 
                related_avatars=[self.avatar.id, target.id]
            )
            events_to_return.append(reject_event)
        
        return ActionResult(status=ActionStatus.COMPLETED, events=events_to_return)
    
    def step(self, target_avatar: "Avatar|str", **kwargs) -> ActionResult:
        """调用父类的通用异步 step 逻辑"""
        target = self._get_target_avatar(target_avatar)
        if target is None:
            return ActionResult(status=ActionStatus.FAILED, events=[])

        # 若无任务，创建异步任务
        if self._feedback_task is None and self._feedback_cached is None:
            infos = self._build_prompt_infos(target)
            import asyncio
            loop = asyncio.get_running_loop()
            self._feedback_task = loop.create_task(self._call_llm_feedback(infos))

        # 若任务已完成，消费结果
        if self._feedback_task is not None and self._feedback_task.done():
            self._feedback_cached = self._feedback_task.result()
            self._feedback_task = None

        if self._feedback_cached is not None:
            res = self._feedback_cached
            self._feedback_cached = None
            r = res.get(target.name, {})
            thinking = r.get("thinking", "")
            target.thinking = thinking
            
            return self._handle_feedback_result(target, r)

        return ActionResult(status=ActionStatus.RUNNING, events=[])
