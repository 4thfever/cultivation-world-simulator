from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.classes.action import DefineAction, ActualActionMixin, LLMAction, StepStatus
from src.classes.battle import get_escape_success_rate
from src.classes.tile import get_avatar_distance
import random
from src.classes.event import Event
from src.utils.llm import get_prompt_and_call_llm
from src.utils.config import CONFIG
from src.classes.action import long_action
from src.classes.relation import relation_display_names, Relation, get_possible_post_relations

if TYPE_CHECKING:
    from src.classes.avatar import Avatar

class MutualAction(DefineAction, LLMAction):
    """
    互动动作：A 对 B 发起动作，B 可以给出反馈（由 LLM 决策）。
    子类需要定义：
      - ACTION_NAME: 当前动作名（给模板展示）
      - COMMENT: 动作语义说明（给模板展示）
      - FEEDBACK_ACTIONS: 反馈可选的 action name 列表（直接可执行）
      - PARAMS: 参数，需要包含 target_avatar
      - FEEDBACK_ACTIONS: 反馈可选的 action name 列表（直接可执行）
    """

    ACTION_NAME: str = "MutualAction"
    COMMENT: str = ""
    DOABLES_REQUIREMENTS: str = "同区域内可互动"
    PARAMS: dict = {"target_avatar": "Avatar"}
    FEEDBACK_ACTIONS: list[str] = []

    def _get_template_path(self) -> Path:
        return CONFIG.paths.templates / "mutual_action.txt"

    def _build_prompt_infos(self, target_avatar: "Avatar") -> dict:
        avatar_name_1 = self.avatar.name
        avatar_name_2 = target_avatar.name
        # avatar infos 仅放入与两人相关的提示，避免超长
        avatar_infos = {
            avatar_name_1: self.avatar.cultivation_progress.get_simple_info(), # avatar1只放境界信息
            avatar_name_2: target_avatar.get_prompt_info([]), # avatar2放全量信息
        }
        feedback_actions = self.FEEDBACK_ACTIONS
        comment = self.COMMENT
        action_name = self.ACTION_NAME
        return {
            "avatar_infos": avatar_infos,
            "avatar_name_1": avatar_name_1,
            "avatar_name_2": avatar_name_2,
            "action_name": action_name,
            "action_info": comment,
            "feedback_actions": feedback_actions,
        }

    def _call_llm_feedback(self, infos: dict) -> dict:
        template_path = self._get_template_path()
        res = get_prompt_and_call_llm(template_path, infos)
        return res

    def _set_target_immediate_action(self, target_avatar: "Avatar", action_name: str, action_params: dict) -> None:
        """
        将反馈决定落地为目标角色的立即动作（清空后加载单步动作链）。
        """
        # 抢占：清空后续计划并中断其当前动作
        self._preempt_avatar(target_avatar)
        # 先加载为计划
        target_avatar.load_decide_result_chain([(action_name, action_params)], target_avatar.thinking, "")
        # 立即提交为当前动作，触发开始事件
        start_event = target_avatar.commit_next_plan()
        if start_event is not None:
            # 侧边栏仅推送一次（由动作发起方承担），另一侧仅写历史
            self._add_event_pair(start_event, initiator=self.avatar, target=target_avatar)

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        """
        子类实现：把反馈映射为具体动作
        """
        pass

    def _apply_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        # 默认不额外记录，由事件系统承担
        return

    # 通用工具：按名找人
    def _find_avatar_by_name(self, name: str) -> "Avatar|None":
        for v in self.world.avatar_manager.avatars.values():
            if v.name == name:
                return v
        return None

    def _get_target_avatar(self, target_avatar: "Avatar|str") -> "Avatar|None":
        if isinstance(target_avatar, str):
            return self._find_avatar_by_name(target_avatar)
        return target_avatar

    # 通用工具：抢占 avatar 当前动作
    def _preempt_avatar(self, avatar: "Avatar") -> None:
        avatar.clear_plans()
        avatar.current_action = None

    # 通用工具：向两人推事件（侧栏只推 initiator）
    def _add_event_pair(self, event: Event, initiator: "Avatar", target: "Avatar") -> None:
        initiator.add_event(event)
        if target is not None:
            target.add_event(event, to_sidebar=False)

    def _execute(self, target_avatar: "Avatar|str") -> None:
        # 允许传入名字字符串
        target_avatar = self._get_target_avatar(target_avatar)
        if target_avatar is None:
            return
            
        infos = self._build_prompt_infos(target_avatar)
        res = self._call_llm_feedback(infos)
        # LLM 只返回 {avatar_name_2: {thinking, feedback}}
        r = res.get(infos["avatar_name_2"], {})
        thinking = r.get("thinking", "")
        feedback = r.get("feedback", "")

        # 挂到目标的thinking上（面向UI/日志），并执行反馈落地
        target_avatar.thinking = thinking
        # 1) 先清空目标后续计划（仅清空队列，不动当前动作）
        target_avatar.clear_plans()
        # 2) 再结算反馈映射为对应动作
        self._settle_feedback(target_avatar, feedback)
        # 3) 反馈事件（进入侧边栏与双方历史，中文化文案）
        fb_map = {
            "MoveAwayFromAvatar": "试图远离",
            "MoveAwayFromRegion": "试图离开区域",
            "Escape": "逃离",
            "Battle": "战斗",
        }
        fb_label = fb_map.get(str(feedback).strip(), str(feedback))
        feedback_event = Event(self.world.month_stamp, f"{target_avatar.name} 对 {self.avatar.name} 的反馈：{fb_label}")
        # 侧边栏仅推送一次，另一侧仅写入历史，避免重复
        self._add_event_pair(feedback_event, initiator=self.avatar, target=target_avatar)
        # 4) 记录历史（文本记录）
        self._apply_feedback(target_avatar, feedback)

    # 实现 ActualActionMixin 接口
    def can_start(self, target_avatar: "Avatar|str|None" = None) -> bool:
        """
        检查互动动作能否启动：两个角色距离必须小于等于2
        """
        if target_avatar is None:
            return False
        target = self._get_target_avatar(target_avatar)
        if target is None:
            return False
        distance = get_avatar_distance(self.avatar, target)
        return distance <= 2

    def start(self, target_avatar: "Avatar|str") -> Event:
        """
        启动互动动作，返回开始事件
        """
        target = self._get_target_avatar(target_avatar)
        target_name = target.name if target is not None else str(target_avatar)
        action_name = getattr(self, 'ACTION_NAME', self.name)
        event = Event(self.world.month_stamp, f"{self.avatar.name} 对 {target_name} 发起 {action_name}")
        # 仅写入历史，避免与提交阶段重复推送到侧边栏
        self.avatar.add_event(event, to_sidebar=False)
        if target is not None:
            target.add_event(event, to_sidebar=False)
        return event

    def step(self, target_avatar: "Avatar|str") -> tuple[StepStatus, list[Event]]:
        """
        执行互动动作，互动动作是即时完成的
        """
        self.execute(target_avatar=target_avatar)
        return StepStatus.COMPLETED, []

    def finish(self, target_avatar: "Avatar|str") -> list[Event]:
        """
        完成互动动作，事件已在 step 中处理，无需额外事件
        """
        return []


class DriveAway(MutualAction, ActualActionMixin):
    """驱赶：试图让对方离开当前区域。"""
    ACTION_NAME = "驱赶"
    COMMENT = "以武力威慑对方离开此地。"
    DOABLES_REQUIREMENTS = "与目标处于同一区域"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS = ["MoveAwayFromRegion", "Battle"]
    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        fb = str(feedback_name).strip()
        if fb == "MoveAwayFromRegion":
            # 驱赶选择离开：必定成功，不涉及概率
            params = {"region": self.avatar.tile.region.name}
            self._set_target_immediate_action(target_avatar, fb, params)
        elif fb == "Battle":
            params = {"avatar_name": self.avatar.name}
            self._set_target_immediate_action(target_avatar, fb, params)

class Attack(MutualAction, ActualActionMixin):
    """攻击另一个NPC"""
    ACTION_NAME = "攻击"
    COMMENT = "对目标进行攻击。"
    DOABLES_REQUIREMENTS = "与目标处于同一区域"
    PARAMS = {"target_avatar": "AvatarName"}
    FEEDBACK_ACTIONS = ["Escape", "Battle"]

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        fb = str(feedback_name).strip()
        if fb == "Escape":
            params = {"avatar_name": self.avatar.name}
            self._set_target_immediate_action(target_avatar, fb, params)
        elif fb == "Battle":
            params = {"avatar_name": self.avatar.name}
            self._set_target_immediate_action(target_avatar, fb, params)


    


class Conversation(MutualAction, ActualActionMixin):
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

    def _get_template_path(self) -> Path:
        # 使用 talk.txt 模板，以获取是否接受与对话内容
        return CONFIG.paths.templates / "talk.txt"

    def _build_prompt_infos(self, target_avatar: "Avatar", *, can_into_relation: bool) -> dict:
        avatar_name_1 = self.avatar.name
        avatar_name_2 = target_avatar.name
        # 目标的 get_prompt_info 已含 personas、关系等，信息更充分
        avatar_infos = {
            avatar_name_1: self.avatar.get_prompt_info([]),
            avatar_name_2: target_avatar.get_prompt_info([]),
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

    # 关系解析由 Relation 提供类方法，仅接受中文关系名，无法解析则跳过

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
        event = Event(self.world.month_stamp, f"{self.avatar.name} 与 {target_name} 开始交谈")
        # 写入历史即可，内容事件稍后生成
        self.avatar.add_event(event, to_sidebar=False)
        if target is not None:
            target.add_event(event, to_sidebar=False)
        return event

    def step(self, target_avatar: "Avatar|str", can_into_relation: bool = False) -> tuple[StepStatus, list[Event]]:
        target = self._get_target_avatar(target_avatar)
        if target is None:
            return StepStatus.COMPLETED, []

        infos = self._build_prompt_infos(target, can_into_relation=can_into_relation)
        res = self._call_llm_feedback(infos)
        r = res.get(infos["avatar_name_2"], {})
        thinking = r.get("thinking", "")
        feedback = str(r.get("feedback", "")).strip()
        talk_content = str(r.get("talk_content", "")).strip()
        into_relation_str = str(r.get("into_relation", "")).strip()

        target.thinking = thinking

        # 拒绝则只记录反馈
        if feedback and feedback != "Talk":
            feedback_event = Event(self.world.month_stamp, f"{target.name} 拒绝与 {self.avatar.name} 交谈")
            self._add_event_pair(feedback_event, initiator=self.avatar, target=target)
            return StepStatus.COMPLETED, []

        # 接受并记录对话内容
        if talk_content:
            content_event = Event(self.world.month_stamp, f"{self.avatar.name} 与 {target.name} 的交谈：{talk_content}")
            # 进入侧栏一次，并写入双方历史
            self._add_event_pair(content_event, initiator=self.avatar, target=target)

        # 仅当 can_into_relation=True 时，根据返回尝试建立关系
        if can_into_relation and into_relation_str:
            rel = Relation.from_chinese(into_relation_str)
            if rel is not None:
                self.avatar.set_relation(target, rel)
                set_event = Event(self.world.month_stamp, f"{self.avatar.name} 与 {target.name} 的关系变为：{relation_display_names.get(rel, str(rel))}")
                self._add_event_pair(set_event, initiator=self.avatar, target=target)

        return StepStatus.COMPLETED, []

    def finish(self, target_avatar: "Avatar|str", **kwargs) -> list[Event]:
        return []