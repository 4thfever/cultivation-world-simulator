"""
Avatar 动作管理 Mixin
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from src.classes.core.avatar.core import Avatar

from src.classes.action import Action
from src.classes.action_runtime import ActionStatus, ActionResult, ActionPlan, ActionInstance
from src.classes.action.registry import ActionRegistry
from src.classes.event import Event
from src.classes.typings import ACTION_NAME, ACTION_NAME_PARAMS_PAIRS
from src.utils.params import filter_kwargs_for_callable
from src.run.log import get_logger


class ActionMixin:
    """动作管理相关方法"""
    
    def create_action(self: "Avatar", action_name: ACTION_NAME) -> Action:
        """
        根据动作名称创建新的action实例
        
        Args:
            action_name: 动作类的名称（如 'Respire', 'Breakthrough' 等）
        
        Returns:
            新创建的Action实例
        
        Raises:
            ValueError: 如果找不到对应的动作类
        """
        action_cls = ActionRegistry.get(action_name)
        return action_cls(self, self.world)

    def load_decide_result_chain(
        self: "Avatar",
        action_name_params_pairs: ACTION_NAME_PARAMS_PAIRS,
        avatar_thinking: str,
        short_term_objective: str,
        prepend: bool = False
    ):
        """
        加载AI的决策结果（动作链），立即设置第一个为当前动作，其余进入队列。
        
        Args:
            action_name_params_pairs: 动作名和参数对列表
            avatar_thinking: 思考内容
            short_term_objective: 短期目标
            prepend: 是否插队到最前面（默认False，即追加到末尾）
        """
        if not action_name_params_pairs:
            return
        self.thinking = avatar_thinking
        self.short_term_objective = short_term_objective
        # 转为计划并入队（不立即提交，交由提交阶段统一触发开始事件）
        plans: List[ActionPlan] = [ActionPlan(name, params) for name, params in action_name_params_pairs]
        if prepend:
            self.planned_actions[0:0] = plans
        else:
            self.planned_actions.extend(plans)

    def clear_plans(self: "Avatar") -> None:
        self.planned_actions.clear()

    def has_plans(self: "Avatar") -> bool:
        return len(self.planned_actions) > 0

    def commit_next_plan(self: "Avatar") -> Optional[Event]:
        """
        提交下一个可启动的计划为当前动作；返回开始事件（若有）。
        """
        if self.current_action is not None:
            return None
        while self.planned_actions:
            plan = self.planned_actions.pop(0)
            try:
                action = self.create_action(plan.action_name)
            except Exception as e:
                logger = get_logger().logger
                logger.warning(
                    "非法动作: Avatar(name=%s,id=%s) 的动作 %s 参数=%s 无法启动，原因=%s",
                    self.name, self.id, plan.action_name, plan.params, e
                )
                continue
            # 再验证
            if not isinstance(plan.params, dict):
                get_logger().logger.warning(
                    "非法参数: Avatar(name=%s) 动作 %s 参数类型错误: %s",
                    self.name, plan.action_name, type(plan.params)
                )
                continue

            params_for_can_start = filter_kwargs_for_callable(action.can_start, plan.params)
            try:
                can_start, reason = action.can_start(**params_for_can_start)
            except TypeError as e:
                get_logger().logger.warning(
                    "动作启动失败: Avatar(name=%s) 动作 %s 参数校验异常: %s",
                    self.name, plan.action_name, e
                )
                continue

            if not can_start:
                # 记录不合法动作
                logger = get_logger().logger
                logger.warning(
                    "非法动作: Avatar(name=%s,id=%s) 的动作 %s 参数=%s 无法启动，原因=%s",
                    self.name, self.id, plan.action_name, plan.params, reason
                )
                continue
            # 启动
            params_for_start = filter_kwargs_for_callable(action.start, plan.params)
            start_event = action.start(**params_for_start)
            self.current_action = ActionInstance(action=action, params=plan.params, status="running")
            # 标记为"本轮新设动作"，用于本月补充执行
            self._new_action_set_this_step = True
            return start_event
        return None

    async def tick_action(self: "Avatar") -> List[Event]:
        """
        推进当前动作一步；返回过程中由动作内部产生的事件（通过 add_event 收集）。
        """
        if self.current_action is None:
            return []
        # 记录当前动作实例引用，用于检测执行过程中是否发生了"抢占/切换"
        action_instance_before = self.current_action
        action = action_instance_before.action
        params = action_instance_before.params
        params_for_step = filter_kwargs_for_callable(action.step, params)
        result: ActionResult = action.step(**params_for_step)
        if result.status == ActionStatus.COMPLETED:
            params_for_finish = filter_kwargs_for_callable(action.finish, params)
            finish_events = await action.finish(**params_for_finish)
            # 仅当当前动作仍然是刚才执行的那个实例时才清空
            # 若在 step() 内部通过"抢占"机制切换了动作（如 Escape 失败立即切到 Attack），不要清空新动作
            if self.current_action is action_instance_before:
                self.current_action = None
            if finish_events:
                # 允许 finish 直接返回事件（极少用），统一并入 pending
                for e in finish_events:
                    self._pending_events.append(e)
        # 合并动作返回的事件（通常为空）
        if result.events:
            for e in result.events:
                self.add_event(e)
        events, self._pending_events = self._pending_events, []
        # 本轮已执行过，清除"新设动作"标记
        # 1. 动作结束 (None)
        # 2. 动作继续执行且未发生切换 (is action_instance_before)
        # 注意：如果动作发生了切换（如 Escape -> Attack），则视为新动作，不清除标记以便 Simulator 进行下一轮调度
        if self.current_action is None or self.current_action is action_instance_before:
            self._new_action_set_this_step = False
            
        return events

    def add_event(self: "Avatar", event: Event, *, to_sidebar: bool = True) -> None:
        """
        添加事件：
        - to_sidebar: 是否进入全局侧边栏（通过 Avatar._pending_events 暂存）
        
        注意：事件会先存入_pending_events，统一由Simulator写入event_manager，避免重复
        """
        if to_sidebar:
            self._pending_events.append(event)
        
    def process_interaction_from_event(self: "Avatar", event: "Event") -> None:
        """
        根据事件更新与其他角色的交互计数。
        该方法由 Simulator 统一调用。
        """
        if not event.related_avatars:
            return

        for aid in event.related_avatars:
            if str(aid) == str(self.id):
                continue
            
            # self.id 与 aid 有交互
            # relation_interaction_states 是 defaultdict，会自动初始化新条目
            self.relation_interaction_states[aid]["count"] += 1

    def get_planned_actions_str(self: "Avatar") -> str:
        """
        获取易读的计划动作列表字符串。
        """
        from src.i18n import t
        if not self.planned_actions:
            return t("None")
        
        lines = []
        for i, plan in enumerate(self.planned_actions, 1):
            try:
                action_cls = ActionRegistry.get(plan.action_name)
                # 优先取 ACTION_NAME，否则用类名
                display_name = getattr(action_cls, "ACTION_NAME", plan.action_name)
            except Exception:
                display_name = plan.action_name
            
            # 简化参数显示，只保留基本类型
            simple_params = {k: v for k, v in plan.params.items() if isinstance(v, (str, int, float, bool))}
            info = f"{i}. {display_name}"
            if simple_params:
                info += f" {simple_params}"
            
            lines.append(info)
            
        return "\n".join(lines)

    @property
    def can_join_gathering(self: "Avatar") -> bool:
        """是否可以参加聚会"""
        if self.current_action and self.current_action.action:
            return getattr(self.current_action.action, 'ALLOW_GATHERING', True)
        return True # 空闲状态默认可以

    @property
    def can_trigger_world_event(self: "Avatar") -> bool:
        """是否可以触发奇遇/霉运"""
        if self.current_action and self.current_action.action:
            return getattr(self.current_action.action, 'ALLOW_WORLD_EVENTS', True)
        return True


