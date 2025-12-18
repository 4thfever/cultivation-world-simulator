from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
import asyncio

from src.classes.action.action import DefineAction, ActualActionMixin, LLMAction
from src.classes.tile import get_avatar_distance
from src.classes.event import Event
from src.utils.llm import call_llm_with_template, LLMMode
from src.utils.config import CONFIG
from src.classes.relation import relation_display_names, Relation
from src.classes.relations import get_possible_new_relations
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.action.event_helper import EventHelper
from src.classes.action.targeting_mixin import TargetingMixin

if TYPE_CHECKING:
    from src.classes.avatar import Avatar
    from src.classes.world import World


class MutualAction(DefineAction, LLMAction, ActualActionMixin, TargetingMixin):
    """
    互动动作：A 对 B 发起动作，B 可以给出反馈（由 LLM 决策）。
    子类需要定义：
      - ACTION_NAME: 当前动作名（给模板展示）
      - DESC: 动作语义说明（给模板展示）
      - FEEDBACK_ACTIONS: 反馈可选的 action name 列表（直接可执行）
      - PARAMS: 参数，需要包含 target_avatar
      - FEEDBACK_ACTIONS: 反馈可选的 action name 列表（直接可执行）
    """

    ACTION_NAME: str = "MutualAction"
    DESC: str = ""
    DOABLES_REQUIREMENTS: str = "交互范围内可互动"
    PARAMS: dict = {"target_avatar": "Avatar"}
    FEEDBACK_ACTIONS: list[str] = []
    # 反馈动作 -> 中文标签 的映射，供事件展示复用
    FEEDBACK_LABELS: dict[str, str] = {
        "Accept": "接受",
        "Reject": "拒绝",
        "MoveAwayFromAvatar": "试图远离",
        "MoveAwayFromRegion": "试图离开区域",
        "Escape": "逃离",
        "Attack": "战斗",
    }
    # 若该互动动作可能生成小故事，可在子类中覆盖该提示词
    STORY_PROMPT: str | None = None

    def __init__(self, avatar: "Avatar", world: "World"):
        super().__init__(avatar, world)
        # 异步反馈任务句柄与缓存结果
        self._feedback_task: asyncio.Task | None = None
        self._feedback_cached: dict | None = None
        # 记录动作开始时间，用于生成事件的时间戳
        self._start_month_stamp: int | None = None

    def _get_template_path(self) -> Path:
        return CONFIG.paths.templates / "mutual_action.txt"

    def _build_prompt_infos(self, target_avatar: "Avatar") -> dict:
        avatar_name_1 = self.avatar.name
        avatar_name_2 = target_avatar.name
        
        # avatar1 使用 expanded_info（包含非详细信息和共同事件），避免重复
        expanded_info = self.avatar.get_expanded_info(other_avatar=target_avatar, detailed=False)
        
        avatar_infos = {
            avatar_name_1: expanded_info,
            avatar_name_2: target_avatar.get_info(detailed=False),
        }
        
        feedback_actions = self.FEEDBACK_ACTIONS
        desc = self.DESC
        action_name = self.ACTION_NAME
        return {
            "avatar_infos": avatar_infos,
            "avatar_name_1": avatar_name_1,
            "avatar_name_2": avatar_name_2,
            "action_name": action_name,
            "action_info": desc,
            "feedback_actions": feedback_actions,
        }

    async def _call_llm_feedback(self, infos: dict) -> dict:
        """异步调用 LLM 获取反馈"""
        template_path = self._get_template_path()
        return await call_llm_with_template(template_path, infos, LLMMode.FAST)

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
        self.preempt_avatar(target_avatar)
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
    
    async def _execute(self, target_avatar: "Avatar|str") -> None:
        """异步执行互动动作 (deprecated, use step instead)"""
        # 仅为兼容 DefineAction 接口，实际逻辑在 step 中
        pass

    # 实现 ActualActionMixin 接口
    def can_start(self, target_avatar: "Avatar|str|None" = None) -> tuple[bool, str]:
        """
        检查互动动作能否启动：目标需在发起者的交互范围内。
        子类通过实现 _can_start 来添加额外检查。
        """
        if target_avatar is None:
            return False, "缺少参数 target_avatar"
        target = self._get_target_avatar(target_avatar)
        if target is None:
            return False, "目标不存在"
        # 调用子类的额外检查
        return self._can_start(target)

    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """
        子类实现此方法来添加特定的启动条件检查。
        参数 target 已经过基类验证（存在且在交互范围内）。
        默认返回 True。
        """
        return True, ""

    def start(self, target_avatar: "Avatar|str") -> Event:
        """
        启动互动动作，返回开始事件
        """
        # 记录开始时间
        self._start_month_stamp = self.world.month_stamp

        target = self._get_target_avatar(target_avatar)
        target_name = target.name if target is not None else str(target_avatar)
        action_name = self.ACTION_NAME
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
        # 根据IS_MAJOR类变量设置事件类型
        is_major = self.__class__.IS_MAJOR if hasattr(self.__class__, 'IS_MAJOR') else False
        event = Event(self._start_month_stamp, f"{self.avatar.name} 对 {target_name} 发起 {action_name}", related_avatars=rel_ids, is_major=is_major)
        
        # 仅手动添加给 Target，Self的部分由ActionMixin通过返回值处理
        # 默认不推Target侧边栏，因为发起事件通常只在发起者侧重要，或者作为"收到发起"的通知
        if target is not None:
            target.add_event(event, to_sidebar=False)
            
        return event

    def step(self, target_avatar: "Avatar|str") -> ActionResult:
        """
        异步化：首帧发起LLM任务并返回RUNNING；任务完成后在后续帧落地反馈并完成。
        """
        target = self._get_target_avatar(target_avatar)
        if target is None:
            return ActionResult(status=ActionStatus.FAILED, events=[])

        # 若无任务，创建异步任务
        if self._feedback_task is None and self._feedback_cached is None:
            infos = self._build_prompt_infos(target)
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
            feedback = r.get("feedback", "")

            target.thinking = thinking
            self._settle_feedback(target, feedback)
            fb_label = self.FEEDBACK_LABELS.get(str(feedback).strip(), str(feedback))
            
            # 使用开始时间戳
            month_stamp = self._start_month_stamp if self._start_month_stamp is not None else self.world.month_stamp
            feedback_event = Event(month_stamp, f"{target.name} 对 {self.avatar.name} 的反馈：{fb_label}", related_avatars=[self.avatar.id, target.id])
            
            self._apply_feedback(target, feedback)
            return ActionResult(status=ActionStatus.COMPLETED, events=[feedback_event])

        return ActionResult(status=ActionStatus.RUNNING, events=[])

    async def finish(self, target_avatar: "Avatar|str") -> list[Event]:
        """
        完成互动动作，事件已在 step 中处理，无需额外事件
        """
        return []
