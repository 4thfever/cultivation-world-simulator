from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.i18n import t
from .mutual_action import MutualAction
from src.classes.event import Event, NULL_EVENT
from src.utils.config import CONFIG
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.relation.relation_delta_service import RelationDeltaService
from src.classes.story_event_service import StoryEventKind, StoryEventService

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


class Conversation(MutualAction):
    """交谈：两名角色在同一区域进行交流。

    - 可由"攀谈"触发，或直接发起
    - 仅当双方处于同一 Region 时可启动
    - LLM 负责生成对话内容
    - 会将对话内容与后续故事写入事件系统
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "conversation_action_name"
    DESC_ID = "conversation_description"
    REQUIREMENTS_ID = "conversation_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🗣️"
    PARAMS = {"target_avatar": "AvatarName"}
    RESPONSE_ACTIONS: list[str] = []  # Conversation 自动触发，不需要对方决策
    RESPONSE_EVENT_STYLE = "none"

    def _get_template_path(self) -> Path:
        # 使用专门的 conversation.txt 模板
        return CONFIG.paths.templates / "conversation.txt"

    def _build_prompt_infos(self, target_avatar: "Avatar") -> dict:
        avatar_name_1 = self.avatar.name
        avatar_name_2 = target_avatar.name
        
        # avatar1 使用 expanded_info（包含详细信息和共同事件），避免重复
        expanded_info = self.avatar.get_expanded_info(other_avatar=target_avatar, detailed=True)
        
        avatar_infos = {
            avatar_name_1: expanded_info,
            avatar_name_2: target_avatar.get_info(detailed=True),
        }
        
        # 获取后续计划
        p1 = self.avatar.get_planned_actions_str()
        p2 = target_avatar.get_planned_actions_str()
        planned_actions_str = {
            avatar_name_1: p1,
            avatar_name_2: p2,
        }
        return {
            "avatar_infos": avatar_infos,
            "avatar_name_1": avatar_name_1,
            "avatar_name_2": avatar_name_2,
            "planned_actions": planned_actions_str,
        }

    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """交谈无额外检查条件"""
        return True, ""

    # 覆盖 start：自定义事件消息
    def start(self, target_avatar: "Avatar|str", **kwargs) -> Event:
        # 记录开始时间
        self._start_month_stamp = self.world.month_stamp
        
        # Conversation 动作不仅返回 NULL_EVENT 以避免生成“开始交谈”的冗余事件（防止与对话内容事件时序显示混乱），
        # 同时也无需手动 add_event，因为我们希望侧边栏和历史记录都只显示最终的对话内容。
        
        return NULL_EVENT

    def _handle_response_result(self, target: "Avatar", result: dict) -> ActionResult:
        """
        处理 LLM 返回的对话结果，包括对话内容和关系变化。
        Conversation 不需要响应事件（RESPONSE_ACTIONS 为空），直接生成内容。
        """
        conversation_content = str(result.get("conversation_content", "")).strip()

        # 使用开始时间戳
        month_stamp = self._start_month_stamp if self._start_month_stamp is not None else self.world.month_stamp

        events_to_return = []

        # 记录对话内容
        if conversation_content:
            content = t("{avatar1} conversation with {avatar2}: {content}",
                       avatar1=self.avatar.name, avatar2=target.name, content=conversation_content)
            content_event = Event(
                month_stamp, 
                content, 
                related_avatars=[self.avatar.id, target.id]
            )
            self._conversation_result_text = content
            self._conversation_target = target
            events_to_return.append(content_event)
        return ActionResult(status=ActionStatus.COMPLETED, events=events_to_return)

    def step(self, target_avatar: "Avatar|str", **kwargs) -> ActionResult:
        """调用通用异步 step 逻辑"""
        target = self._get_target_avatar(target_avatar)
        if target is None:
            return ActionResult(status=ActionStatus.FAILED, events=[])

        # 若无任务，创建异步任务
        if self._response_task is None and self._response_cached is None:
            infos = self._build_prompt_infos(target)
            import asyncio
            loop = asyncio.get_running_loop()
            self._response_task = loop.create_task(self._call_llm_response(infos))

        # 若任务已完成，消费结果
        if self._response_task is not None and self._response_task.done():
            self._response_cached = self._response_task.result()
            self._response_task = None

        if self._response_cached is not None:
            res = self._response_cached
            self._response_cached = None
            r = res.get(target.name, {})
            thinking = r.get("thinking", "")
            target.thinking = thinking
            
            return self._handle_response_result(target, r)

        return ActionResult(status=ActionStatus.RUNNING, events=[])

    async def finish(self, target_avatar: "Avatar|str") -> list[Event]:
        target = getattr(self, "_conversation_target", None) or self._get_target_avatar(target_avatar)
        result_text = getattr(self, "_conversation_result_text", "")
        if target is None or not result_text:
            return []

        a_to_b, b_to_a = await RelationDeltaService.resolve_event_text_delta(
            action_key="conversation",
            avatar_a=self.avatar,
            avatar_b=target,
            event_text=result_text,
        )
        RelationDeltaService.apply_bidirectional_delta(self.avatar, target, a_to_b, b_to_a)

        story_event = await StoryEventService.maybe_create_story(
            kind=StoryEventKind.DAILY_SOCIAL,
            month_stamp=self.world.month_stamp,
            start_text=result_text,
            result_text=result_text,
            actors=[self.avatar, target],
            related_avatar_ids=[self.avatar.id, target.id],
            allow_relation_changes=False,
        )
        return [story_event] if story_event is not None else []
