from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from src.classes.action import DefineAction, ActualActionMixin, LLMAction
from src.classes.tile import get_avatar_distance
from src.classes.event import Event
from src.utils.llm import get_prompt_and_call_llm
from src.utils.config import CONFIG
from src.classes.relation import relation_display_names, Relation, get_possible_post_relations
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.action.event_helper import EventHelper
from src.classes.action.targeting_mixin import TargetingMixin

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


class MutualAction(DefineAction, LLMAction, TargetingMixin):
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
            avatar_name_1: self.avatar.cultivation_progress.get_simple_info(),
            avatar_name_2: target_avatar.get_prompt_info([]),
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
        # 若当前已是同类同参动作，直接跳过，避免重复“发起战斗”等事件刷屏
        try:
            cur = target_avatar.current_action
            if cur is not None:
                cur_name = getattr(cur.action, "__class__", type(cur.action)).__name__
                if cur_name == action_name:
                    if getattr(cur, "params", {}) == dict(action_params):
                        return
        except Exception:
            pass
        # 抢占：清空后续计划并中断其当前动作
        self._preempt_avatar(target_avatar)
        # 先加载为计划
        target_avatar.load_decide_result_chain([(action_name, action_params)], target_avatar.thinking, "")
        # 立即提交为当前动作，触发开始事件
        start_event = target_avatar.commit_next_plan()
        if start_event is not None:
            # 侧边栏仅推送一次（由动作发起方承担），另一侧仅写历史
            EventHelper.push_pair(start_event, initiator=self.avatar, target=target_avatar, to_sidebar_once=True)

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        """
        子类实现：把反馈映射为具体动作
        """
        pass

    def _apply_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        # 默认不额外记录，由事件系统承担
        return

    def _get_target_avatar(self, target_avatar: "Avatar|str") -> "Avatar|None":
        if isinstance(target_avatar, str):
            return self.find_avatar_by_name(target_avatar)
        return target_avatar

    def _execute(self, target_avatar: "Avatar|str") -> None:
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
        EventHelper.push_pair(feedback_event, initiator=self.avatar, target=target_avatar, to_sidebar_once=True)
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

    def step(self, target_avatar: "Avatar|str") -> ActionResult:
        """
        执行互动动作，互动动作是即时完成的
        """
        self.execute(target_avatar=target_avatar)
        return ActionResult(status=ActionStatus.COMPLETED, events=[])

    def finish(self, target_avatar: "Avatar|str") -> list[Event]:
        """
        完成互动动作，事件已在 step 中处理，无需额外事件
        """
        return []


