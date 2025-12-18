from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .mutual_action import MutualAction
from src.classes.relations import (
    process_relation_changes,
    get_relation_change_context,
)
from src.classes.event import Event, NULL_EVENT
from src.utils.config import CONFIG
from src.classes.action_runtime import ActionResult, ActionStatus

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


class Conversation(MutualAction):
    """交谈：两名角色在同一区域进行交流。

    - 可由"攀谈"触发，或直接发起
    - 仅当双方处于同一 Region 时可启动
    - LLM 可决策是否进入新关系或取消旧关系
    - 会将对话内容写入事件系统
    """

    ACTION_NAME = "交谈"
    DESC = "与对方进行一段交流对话"
    DOABLES_REQUIREMENTS = "目标在交互范围内"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS: list[str] = []  # Conversation 自动触发，不需要对方决策
    STORY_PROMPT: str = ""

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
        
        # 获取关系上下文
        possible_new_relations, possible_cancel_relations = get_relation_change_context(self.avatar, target_avatar)
        
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
            "possible_new_relations": possible_new_relations,
            "possible_cancel_relations": possible_cancel_relations,
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

    def _handle_feedback_result(self, target: "Avatar", result: dict) -> ActionResult:
        """
        处理 LLM 返回的对话结果，包括对话内容和关系变化。
        Conversation 不需要反馈（FEEDBACK_ACTIONS 为空），直接生成内容。
        """
        conversation_content = str(result.get("conversation_content", "")).strip()

        # 使用开始时间戳
        month_stamp = self._start_month_stamp if self._start_month_stamp is not None else self.world.month_stamp

        events_to_return = []

        # 记录对话内容
        if conversation_content:
            content_event = Event(
                month_stamp, 
                f"{self.avatar.name} 与 {target.name} 的交谈：{conversation_content}", 
                related_avatars=[self.avatar.id, target.id]
            )
            events_to_return.append(content_event)

        # 处理关系变化 (调用通用逻辑)
        # 注意：process_relation_changes 可能会生成关系变化的事件
        # 这部分逻辑需要确认是否也遵循新模式。
        # 假设 process_relation_changes 内部使用了 add_event，则需要留意是否存在双重添加风险。
        # 目前看来 process_relation_changes 是通过 EventHelper 或直接 add_event 操作的。
        # 如果它内部逻辑完备（如使用了 EventHelper 去重），则无需改动。
        process_relation_changes(self.avatar, target, result, month_stamp)

        return ActionResult(status=ActionStatus.COMPLETED, events=events_to_return)

    def step(self, target_avatar: "Avatar|str", **kwargs) -> ActionResult:
        """调用通用异步 step 逻辑"""
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
