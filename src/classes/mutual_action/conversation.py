from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .mutual_action import MutualAction
from src.classes.relation import relation_display_names, Relation, get_possible_post_relations
from src.classes.event import Event
from src.utils.config import CONFIG
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.action.event_helper import EventHelper

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


class Conversation(MutualAction):
    """交谈：两名角色在同一区域进行交流。

    - 可由“攀谈”触发，或直接发起
    - 仅当双方处于同一 Region 时可启动
    - 当 can_into_relation=True 且 LLM 决策返回 into_relation 时，根据返回建立关系
    - 会将对话内容写入事件系统
    """

    ACTION_NAME = "交谈"
    COMMENT = "两人需在同一地区，进行一段交流对话"
    DOABLES_REQUIREMENTS = "与目标处于同一区域"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS: list[str] = ["Talk", "Reject"]
    STORY_PROMPT: str = ""

    def _get_template_path(self) -> Path:
        # 使用 talk.txt 模板，以获取是否接受与对话内容
        return CONFIG.paths.templates / "talk.txt"

    def _build_prompt_infos(self, target_avatar: "Avatar", *, can_into_relation: bool) -> dict:
        avatar_name_1 = self.avatar.name
        avatar_name_2 = target_avatar.name
        # 交谈：使用详细信息，便于生成更丰富对话
        avatar_infos = {
            avatar_name_1: self.avatar.get_info(detailed=True),
            avatar_name_2: target_avatar.get_info(detailed=True),
        }
        # 可能的后天关系（转中文名，给模板阅读）
        possible_relations = [relation_display_names[r] for r in get_possible_post_relations(self.avatar, target_avatar)]
        return {
            "avatar_infos": avatar_infos,
            "avatar_name_1": avatar_name_1,
            "avatar_name_2": avatar_name_2,
            "can_into_relation": bool(can_into_relation),
            "possible_relations": possible_relations,
        }

    def can_start(self, target_avatar: "Avatar|str|None" = None, **kwargs) -> bool:
        if target_avatar is None:
            return False
        target = self._get_target_avatar(target_avatar)
        if target is None or target.tile is None or self.avatar.tile is None:
            return False
        return target.tile.region == self.avatar.tile.region

    def start(self, target_avatar: "Avatar|str", **kwargs) -> Event:
        target = self._get_target_avatar(target_avatar)
        target_name = target.name if target is not None else str(target_avatar)
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
        event = Event(self.world.month_stamp, f"{self.avatar.name} 与 {target_name} 开始交谈", related_avatars=rel_ids)
        # 写入历史即可，内容事件稍后生成
        self.avatar.add_event(event, to_sidebar=False)
        if target is not None:
            target.add_event(event, to_sidebar=False)
        return event

    def step(self, target_avatar: "Avatar|str", can_into_relation: bool = False) -> ActionResult:
        target = self._get_target_avatar(target_avatar)
        if target is None:
            return ActionResult(status=ActionStatus.COMPLETED, events=[])

        infos = self._build_prompt_infos(target, can_into_relation=can_into_relation)
        res = self._call_llm_feedback(infos)
        r = res.get(infos["avatar_name_2"], {})
        thinking = r.get("thinking", "")
        feedback = str(r.get("feedback", "")).strip()
        talk_content = str(r.get("talk_content", "")).strip()
        into_relation_str = str(r.get("into_relation", "")).strip()

        target.thinking = thinking

        fb = feedback.strip()
        # 仅当明确接受时才记录对话与关系；其余一律视为拒绝
        if fb == "Talk":
            if talk_content:
                content_event = Event(self.world.month_stamp, f"{self.avatar.name} 与 {target.name} 的交谈：{talk_content}", related_avatars=[self.avatar.id, target.id])
                # 进入侧栏一次，并写入双方历史
                EventHelper.push_pair(content_event, initiator=self.avatar, target=target, to_sidebar_once=True)

            if can_into_relation and into_relation_str:
                rel = Relation.from_chinese(into_relation_str)
                if rel is not None:
                    self.avatar.set_relation(target, rel)
                    set_event = Event(self.world.month_stamp, f"{self.avatar.name} 与 {target.name} 的关系变为：{relation_display_names.get(rel, str(rel))}", related_avatars=[self.avatar.id, target.id])
                    EventHelper.push_pair(set_event, initiator=self.avatar, target=target, to_sidebar_once=True)

            return ActionResult(status=ActionStatus.COMPLETED, events=[])
        else:
            feedback_event = Event(self.world.month_stamp, f"{target.name} 拒绝与 {self.avatar.name} 交谈", related_avatars=[self.avatar.id, target.id])
            EventHelper.push_pair(feedback_event, initiator=self.avatar, target=target, to_sidebar_once=True)
            return ActionResult(status=ActionStatus.COMPLETED, events=[])

    def finish(self, target_avatar: "Avatar|str", **kwargs) -> list[Event]:
        return []


