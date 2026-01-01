from __future__ import annotations

from typing import TYPE_CHECKING

from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.event import Event
from src.classes.action.event_helper import EventHelper

if TYPE_CHECKING:
    from src.classes.avatar import Avatar

from .mutual_action import MutualAction


class Talk(MutualAction):
    """
    攀谈：向交互范围内的某个NPC发起攀谈。
    - 接受后自动进入 Conversation
    """

    ACTION_NAME = "攀谈"
    EMOJI = "👋"
    DESC = "向对方发起攀谈"
    DOABLES_REQUIREMENTS = "目标在交互范围内"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS: list[str] = ["Talk", "Reject"]
    
    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """攀谈无额外检查条件"""
        from src.classes.observe import is_within_observation
        if not is_within_observation(self.avatar, target):
            return False, "目标不在交互范围内"
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
            accept_event = Event(
                self.world.month_stamp, 
                f"{target.name} 接受了 {self.avatar.name} 的攀谈", 
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
            reject_event = Event(
                self.world.month_stamp, 
                f"{target.name} 拒绝了 {self.avatar.name} 的攀谈", 
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
