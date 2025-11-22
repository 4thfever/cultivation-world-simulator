from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .mutual_action import MutualAction
from src.classes.relation import relation_display_names, Relation
from src.classes.relations import (
    get_possible_new_relations,
    get_possible_cancel_relations,
    set_relation,
    cancel_relation,
)
from src.classes.event import Event
from src.utils.config import CONFIG
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.action.event_helper import EventHelper

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
    COMMENT = "与对方进行一段交流对话"
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
        
        # 可能的后天关系（转中文名，给模板阅读）
        # 注意：这里计算的是 target 相对于 avatar 的可能关系
        possible_new_relations = [relation_display_names[r] for r in get_possible_new_relations(self.avatar, target_avatar)]
        # 可能取消的关系
        possible_cancel_relations = [relation_display_names[r] for r in get_possible_cancel_relations(target_avatar, self.avatar)]
        
        return {
            "avatar_infos": avatar_infos,
            "avatar_name_1": avatar_name_1,
            "avatar_name_2": avatar_name_2,
            "possible_new_relations": possible_new_relations,
            "possible_cancal_relations": possible_cancel_relations,  # 保持模板中的拼写
        }

    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """交谈无额外检查条件"""
        return True, ""

    # 覆盖 start：自定义事件消息
    def start(self, target_avatar: "Avatar|str", **kwargs) -> Event:
        target = self._get_target_avatar(target_avatar)
        target_name = target.name if target is not None else str(target_avatar)
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
        event = Event(self.world.month_stamp, f"{self.avatar.name} 与 {target_name} 开始交谈", related_avatars=rel_ids)
        self.avatar.add_event(event, to_sidebar=False)
        if target is not None:
            target.add_event(event, to_sidebar=False)
        return event

    def _handle_feedback_result(self, target: "Avatar", result: dict) -> ActionResult:
        """
        处理 LLM 返回的对话结果，包括对话内容和关系变化。
        Conversation 不需要反馈（FEEDBACK_ACTIONS 为空），直接生成内容。
        """
        conversation_content = str(result.get("conversation_content", "")).strip()
        new_relation_str = str(result.get("new_relation", "")).strip()
        cancel_relation_str = str(result.get("cancal_relation", "")).strip()  # 保持模板中的拼写

        # 记录对话内容
        if conversation_content:
            content_event = Event(
                self.world.month_stamp, 
                f"{self.avatar.name} 与 {target.name} 的交谈：{conversation_content}", 
                related_avatars=[self.avatar.id, target.id]
            )
            EventHelper.push_pair(content_event, initiator=self.avatar, target=target, to_sidebar_once=True)

        # 处理进入新关系
        if new_relation_str:
            rel = Relation.from_chinese(new_relation_str)
            if rel is not None:
                set_relation(target, self.avatar, rel)
                set_event = Event(
                    self.world.month_stamp, 
                    f"{target.name} 与 {self.avatar.name} 的关系变为：{relation_display_names.get(rel, str(rel))}", 
                    related_avatars=[self.avatar.id, target.id],
                    is_major=True
                )
                EventHelper.push_pair(set_event, initiator=self.avatar, target=target, to_sidebar_once=True)

        # 处理取消关系
        if cancel_relation_str:
            rel = Relation.from_chinese(cancel_relation_str)
            if rel is not None:
                success = cancel_relation(target, self.avatar, rel)
                if success:
                    cancel_event = Event(
                        self.world.month_stamp, 
                        f"{target.name} 与 {self.avatar.name} 取消了关系：{relation_display_names.get(rel, str(rel))}", 
                        related_avatars=[self.avatar.id, target.id],
                        is_major=True
                    )
                    EventHelper.push_pair(cancel_event, initiator=self.avatar, target=target, to_sidebar_once=True)

        return ActionResult(status=ActionStatus.COMPLETED, events=[])

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
