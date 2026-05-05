from __future__ import annotations

from src.i18n import t
from src.classes.action import DefineAction, ActualActionMixin
from src.classes.action.param_options import ParamOptionSource
from src.classes.event import Event
from src.classes.action import Move
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.action.move_helper import clamp_manhattan_with_diagonal_priority
from src.utils.resolution import resolve_query


class MoveToAvatar(DefineAction, ActualActionMixin):
    """
    朝另一个角色当前位置移动。
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "move_to_avatar_action_name"
    DESC_ID = "move_to_avatar_description"
    REQUIREMENTS_ID = "move_to_avatar_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🏃"
    PARAMS = {"avatar_name": "str"}
    PARAM_OPTION_SOURCES = {"avatar_name": ParamOptionSource.OBSERVABLE_AVATAR_NAME}

    def _get_target(self, avatar_name: str):
        """
        根据名字或 ID 查找目标角色；找不到返回 None。
        """
        from src.classes.core.avatar import Avatar

        return resolve_query(avatar_name, self.world, expected_types=[Avatar]).obj

    def _execute(self, avatar_name: str) -> None:
        target = self._get_target(avatar_name)
        if target is None:
            return
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        target_loc = (target.pos_x, target.pos_y)
        raw_dx = target_loc[0] - cur_loc[0]
        raw_dy = target_loc[1] - cur_loc[1]
        step = getattr(self.avatar, "move_step_length", 1)
        dx, dy = clamp_manhattan_with_diagonal_priority(raw_dx, raw_dy, step)
        Move(self.avatar, self.world).execute(dx, dy)

    def can_start(self, avatar_name: str) -> tuple[bool, str]:
        return True, ""

    def start(self, avatar_name: str) -> Event:
        target = self._get_target(avatar_name)
        target_name = target.name if target is not None else avatar_name
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
        content = t("{avatar} begins moving toward {target}",
                   avatar=self.avatar.name, target=target_name)
        return Event(self.world.month_stamp, content, related_avatars=rel_ids)

    def step(self, avatar_name: str) -> ActionResult:
        self.execute(avatar_name=avatar_name)
        target = self._get_target(avatar_name)
        if target is None:
            return ActionResult(status=ActionStatus.COMPLETED, events=[])
        done = self.avatar.tile == target.tile
        return ActionResult(status=(ActionStatus.COMPLETED if done else ActionStatus.RUNNING), events=[])

    async def finish(self, avatar_name: str) -> list[Event]:
        return []


