from __future__ import annotations

from src.classes.action import DefineAction, ChunkActionMixin
from src.classes.action.move_helper import clamp_manhattan_with_diagonal_priority


class Move(DefineAction, ChunkActionMixin):
    """
    最基础的移动动作，在tile之间进行切换。
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "move_action_name"
    DESC_ID = "move_description"
    
    # 不需要翻译的常量
    EMOJI = "🏃"
    PARAMS = {"delta_x": "int", "delta_y": "int"}

    def _execute(self, delta_x: int, delta_y: int) -> None:
        """
        移动到某个tile
        """
        world = self.world
        # 基于境界的移动步长：曼哈顿限制，优先斜向
        step = getattr(self.avatar, "move_step_length", 1)
        # 附加移动步长加成
        extra_raw = self.avatar.effects.get("extra_move_step", 0)
        step += int(extra_raw or 0)
        clamped_dx, clamped_dy = clamp_manhattan_with_diagonal_priority(delta_x, delta_y, step)

        new_x = self.avatar.pos_x + clamped_dx
        new_y = self.avatar.pos_y + clamped_dy

        # 边界检查：越界则不移动
        if world.map.is_in_bounds(new_x, new_y):
            self.avatar.pos_x = new_x
            self.avatar.pos_y = new_y
            target_tile = world.map.get_tile(new_x, new_y)
            self.avatar.tile = target_tile
        else:
            # 超出边界：不改变位置与tile
            pass


