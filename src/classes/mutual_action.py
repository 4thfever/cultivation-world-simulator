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

if TYPE_CHECKING:
    from src.classes.avatar import Avatar

# 默认所有的互动都是1个月时间
@long_action(step_month=1)
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
        feedback_actions = getattr(self, "FEEDBACK_ACTIONS", [])
        return {
            "avatar_infos": avatar_infos,
            "avatar_name_1": avatar_name_1,
            "avatar_name_2": avatar_name_2,
            "action_name": getattr(self, "ACTION_NAME", self.name),
            "action_info": getattr(self, "COMMENT", ""),
            "FEEDBACK_ACTIONS": feedback_actions,
        }

    def _call_llm_feedback(self, infos: dict) -> dict:
        template_path = self._get_template_path()
        res = get_prompt_and_call_llm(template_path, infos)
        return res

    def _set_target_immediate_action(self, target_avatar: "Avatar", action_name: str, action_params: dict) -> None:
        """
        将反馈决定落地为目标角色的立即动作（清空后加载单步动作链）。
        """
        # 先加载为计划
        target_avatar.load_decide_result_chain([(action_name, action_params)], target_avatar.thinking, "")
        # 立即提交为当前动作，触发开始事件
        start_event = target_avatar.commit_next_plan()
        if start_event is not None:
            # 侧边栏仅推送一次（由动作发起方承担），另一侧仅写历史
            self.avatar.add_event(start_event)
            target_avatar.add_event(start_event, to_sidebar=False)

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        """
        子类实现：把反馈映射为具体动作
        """
        pass

    def _apply_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        # 默认不额外记录，由事件系统承担
        return

    def _get_target_avatar(self, target_avatar: "Avatar|str") -> "Avatar|None":
        """
        获取目标角色，支持传入角色对象或名字字符串
        
        Returns:
            目标角色，如果找不到返回 None
        """
        if isinstance(target_avatar, str):
            name = target_avatar
            for v in self.world.avatar_manager.avatars.values():
                if v.name == name:
                    return v
            return None
        return target_avatar

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
        if hasattr(target_avatar, "clear_plans"):
            target_avatar.clear_plans()
        # 2) 再结算反馈映射为对应动作
        self._settle_feedback(target_avatar, feedback)
        # 3) 反馈事件（进入侧边栏与双方历史，中文化文案）
        fb_map = {
            "MoveAwayFromAvatar": "试图远离",
            "MoveAwayFromRegion": "试图离开区域",
            "Battle": "战斗",
        }
        fb_label = fb_map.get(str(feedback).strip(), str(feedback))
        feedback_event = Event(self.world.month_stamp, f"{target_avatar.name} 对 {self.avatar.name} 的反馈：{fb_label}")
        # 侧边栏仅推送一次，另一侧仅写入历史，避免重复
        self.avatar.add_event(feedback_event)
        target_avatar.add_event(feedback_event, to_sidebar=False)
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
    FEEDBACK_ACTIONS = ["MoveAwayFromAvatar", "Battle"]

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        fb = str(feedback_name).strip()
        if fb == "MoveAwayFromAvatar":
            params = {"avatar_name": self.avatar.name}
            self._set_target_immediate_action(target_avatar, fb, params)
        elif fb == "Battle":
            params = {"avatar_name": self.avatar.name}
            self._set_target_immediate_action(target_avatar, fb, params)


# 轻量实现三个动作类，供互动动作反馈直接使用
class MoveAwayFromAvatar(DefineAction, ActualActionMixin):
    COMMENT = "远离指定角色"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "AvatarName"}
    def _execute(self, avatar_name: str) -> None:
        target = None
        for v in self.world.avatar_manager.avatars.values():
            if v.name == avatar_name:
                target = v
                break
        if target is None:
            return
        # 被攻击时逃跑的成功率：从 battle 模块获取（暂时固定值）
        escape_rate = float(get_escape_success_rate(target, self.avatar))
        if random.random() < escape_rate:
            dx = 1 if self.avatar.pos_x >= target.pos_x else -1
            dy = 1 if self.avatar.pos_y >= target.pos_y else -1
            nx = self.avatar.pos_x + dx
            ny = self.avatar.pos_y + dy
            if self.world.map.is_in_bounds(nx, ny):
                self.avatar.pos_x = nx
                self.avatar.pos_y = ny
                self.avatar.tile = self.world.map.get_tile(nx, ny)
        else:
            # 逃跑失败：进入战斗（立即动作）
            self.avatar.clear_plans()
            # 入队并提交
            self.avatar.load_decide_result_chain([("Battle", {"avatar_name": avatar_name})], self.avatar.thinking, "")
            start_event = self.avatar.commit_next_plan()
            if start_event is not None:
                # 仅在本方推送到侧边栏；对方仅写历史
                self.avatar.add_event(start_event)
                if target is not None:
                    target.add_event(start_event, to_sidebar=False)


class MoveAwayFromRegion(DefineAction, ActualActionMixin):
    COMMENT = "离开指定区域"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"region": "RegionName"}
    def _execute(self, region: str) -> None:
        # 驱赶离开：若选择离开，必定成功。简化为向地图边缘移动一步
        dx = 1 if self.avatar.pos_x < self.world.map.width - 1 else -1
        dy = 1 if self.avatar.pos_y < self.world.map.height - 1 else -1
        nx = max(0, min(self.world.map.width - 1, self.avatar.pos_x + dx))
        ny = max(0, min(self.world.map.height - 1, self.avatar.pos_y + dy))
        if self.world.map.is_in_bounds(nx, ny):
            self.avatar.pos_x = nx
            self.avatar.pos_y = ny
            self.avatar.tile = self.world.map.get_tile(nx, ny)