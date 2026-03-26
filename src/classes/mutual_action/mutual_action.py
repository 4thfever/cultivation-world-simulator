from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
import asyncio

from src.i18n import t
from src.classes.action.action import DefineAction, ActualActionMixin, LLMAction
from src.classes.event import Event, NULL_EVENT
from src.utils.llm import call_llm_with_task_name
from src.utils.config import CONFIG
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.action.event_helper import EventHelper
from src.classes.action.targeting_mixin import TargetingMixin

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.core.world import World


class MutualAction(DefineAction, LLMAction, ActualActionMixin, TargetingMixin):
    """
    互动动作：A 对 B 发起动作，B 可以给出响应（由 LLM 决策）。
    子类需要定义：
      - ACTION_NAME_ID: 当前动作名的 msgid
      - DESC_ID: 动作语义说明的 msgid
      - REQUIREMENTS_ID: 可执行条件的 msgid
      - RESPONSE_ACTIONS: 响应可选的 action name 列表（直接可执行）
      - PARAMS: 参数，需要包含 target_avatar
    """
    
    # 多语言 ID（子类覆盖）
    ACTION_NAME_ID: str = "mutual_action_name"
    DESC_ID: str = ""
    REQUIREMENTS_ID: str = "mutual_action_requirements"
    STORY_PROMPT_ID: str = ""
    
    # 不需要翻译的常量
    EMOJI: str = "💬"
    PARAMS: dict = {"target_avatar": "Avatar"}
    RESPONSE_ACTIONS: list[str] = []
    RESPONSE_EVENT_STYLE: str = "reply"
    SHOW_RESPONSE_EVENT: bool = False
    
    # 响应动作 -> msgid 的映射（子类可覆盖）
    RESPONSE_LABEL_IDS: dict[str, str] = {
        "Accept": "feedback_accept",
        "Reject": "feedback_reject",
        "MoveAwayFromAvatar": "feedback_move_away_from_avatar",
        "MoveAwayFromRegion": "feedback_move_away_from_region",
        "Escape": "feedback_escape",
        "Attack": "feedback_attack",
    }
    
    @classmethod
    def get_action_name(cls) -> str:
        """获取动作名称的翻译"""
        if cls.ACTION_NAME_ID:
            return t(cls.ACTION_NAME_ID)
        return cls.__name__
    
    @classmethod
    def get_desc(cls) -> str:
        """获取动作描述的翻译"""
        if cls.DESC_ID:
            return t(cls.DESC_ID)
        return ""
    
    @classmethod
    def get_requirements(cls) -> str:
        """获取可执行条件的翻译"""
        if cls.REQUIREMENTS_ID:
            return t(cls.REQUIREMENTS_ID)
        return ""
    
    @classmethod
    def get_response_label(cls, response_name: str) -> str:
        """获取响应标签的翻译"""
        msgid = cls.RESPONSE_LABEL_IDS.get(response_name, "")
        if msgid:
            return t(msgid)
        return response_name
    
    @classmethod
    def get_story_prompt(cls) -> str:
        """获取故事提示词的翻译"""
        if cls.STORY_PROMPT_ID:
            return t(cls.STORY_PROMPT_ID)
        return ""

    def __init__(self, avatar: "Avatar", world: "World"):
        super().__init__(avatar, world)
        # 异步响应任务句柄与缓存结果
        self._response_task: asyncio.Task | None = None
        self._response_cached: dict | None = None
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
        
        world_info = self.world.static_info

        response_actions = self.RESPONSE_ACTIONS
        desc = self.get_desc()  # 使用 classmethod 获取翻译
        action_name = self.get_action_name()  # 使用 classmethod 获取翻译
        return {
            "world_info": world_info,
            "avatar_infos": avatar_infos,
            "avatar_name_1": avatar_name_1,
            "avatar_name_2": avatar_name_2,
            "action_name": action_name,
            "action_info": desc,
            "response_actions": response_actions,
            # 保留模板兼容字段，避免修改 prompt 渲染链路时出现双端不一致
            "feedback_actions": response_actions,
        }

    async def _call_llm_response(self, infos: dict) -> dict:
        """异步调用 LLM 获取响应"""
        template_path = self._get_template_path()
        return await call_llm_with_task_name("interaction_feedback", template_path, infos)

    def _set_target_immediate_action(
        self,
        target_avatar: "Avatar",
        action_name: str,
        action_params: dict,
        *,
        push_start_event: bool = True,
    ) -> None:
        """
        将响应决定落地为目标角色的立即动作（清空后加载单步动作链）。
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
        if push_start_event and start_event is not None and start_event != NULL_EVENT:
            # 侧边栏仅推送一次（由动作发起方承担），另一侧仅写历史
            EventHelper.push_pair(start_event, initiator=self.avatar, target=target_avatar, to_sidebar_once=True)

    def _settle_response(self, target_avatar: "Avatar", response_name: str) -> None:
        """
        子类实现：把响应映射为具体动作
        """
        pass

    def _apply_response(self, target_avatar: "Avatar", response_name: str) -> None:
        # 默认不额外记录，由事件系统承担
        return

    def _build_response_event_content(self, target_avatar: "Avatar", response_name: str) -> str:
        response_label = self.get_response_label(str(response_name).strip())
        return t(
            "{target} feedback to {initiator}: {feedback}",
            target=target_avatar.name,
            initiator=self.avatar.name,
            feedback=response_label,
        )

    def _build_response_event(self, target_avatar: "Avatar", response_name: str) -> Event | None:
        if self.RESPONSE_EVENT_STYLE == "none" or not self.SHOW_RESPONSE_EVENT:
            return None

        month_stamp = self._start_month_stamp if self._start_month_stamp is not None else self.world.month_stamp
        content = self._build_response_event_content(target_avatar, response_name)
        event = Event(month_stamp, content, related_avatars=[self.avatar.id, target_avatar.id])
        self._last_response_event_content = content
        return event

    def _get_target_avatar(self, target_avatar: "Avatar|str") -> "Avatar|None":
        if isinstance(target_avatar, str):
            return self.find_avatar_by_name(target_avatar)
        return target_avatar
    
    async def _execute(self, target_avatar: "Avatar|str") -> None:
        """异步执行互动动作 (deprecated, use step instead)"""
        # 仅为兼容 DefineAction 接口，实际逻辑在 step 中
        pass

    # 实现 ActualActionMixin 接口
    def can_start(self, target_avatar: "Avatar|str") -> tuple[bool, str]:
        """
        检查互动动作能否启动：目标需在发起者的交互范围内。
        子类通过实现 _can_start 来添加额外检查。

        注意：此方法未使用 TargetingMixin.validate_target_avatar()，
        因为需要额外检查 target == self.avatar 和调用子类的 _can_start()。
        """
        target = self._get_target_avatar(target_avatar)
        if target is None:
            return False, t("Target does not exist")
        if target == self.avatar:
            return False, t("Cannot initiate interaction with self")
        if target.is_dead:
            return False, t("Target is already dead")
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
        target = self._get_target_avatar(target_avatar)
        if target is not None and target.is_dead:
            return NULL_EVENT

        # 记录开始时间
        self._start_month_stamp = self.world.month_stamp
        target_name = target.name if target is not None else str(target_avatar)
        action_name = self.get_action_name()
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
        # 根据IS_MAJOR类变量设置事件类型
        is_major = self.__class__.IS_MAJOR if hasattr(self.__class__, 'IS_MAJOR') else False
        
        content = t("{initiator} initiates {action} with {target}",
                   initiator=self.avatar.name, action=action_name, target=target_name)
        event = Event(self._start_month_stamp, content, related_avatars=rel_ids, is_major=is_major)
        self._start_event_content = event.content
        return event

    def step(self, target_avatar: "Avatar|str") -> ActionResult:
        """
        异步化：首帧发起LLM任务并返回RUNNING；任务完成后在后续帧落地响应并完成。
        """
        target = self._get_target_avatar(target_avatar)
        if target is None or target.is_dead:
            return ActionResult(status=ActionStatus.FAILED, events=[])

        # 若无任务，创建异步任务
        if self._response_task is None and self._response_cached is None:
            infos = self._build_prompt_infos(target)
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
            response = r.get("response", r.get("feedback", ""))

            target.thinking = thinking
            self._settle_response(target, response)

            response_event = self._build_response_event(target, response)
            self._apply_response(target, response)

            events = [response_event] if response_event is not None else []
            return ActionResult(status=ActionStatus.COMPLETED, events=events)

        return ActionResult(status=ActionStatus.RUNNING, events=[])

    async def finish(self, target_avatar: "Avatar|str") -> list[Event]:
        """
        完成互动动作，事件已在 step 中处理，无需额外事件
        """
        return []


class InvitationAction(MutualAction):
    """邀请/请求型互动，目标主要做出接受或拒绝的回应。"""

    RESPONSE_EVENT_STYLE = "reply"
    SHOW_RESPONSE_EVENT = False


class PressureAction(MutualAction):
    """施压/敌对型互动，目标主要做出逃离、应战等应对。"""

    RESPONSE_EVENT_STYLE = "reply"
    SHOW_RESPONSE_EVENT = False
