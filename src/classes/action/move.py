from __future__ import annotations

from src.classes.action import DefineAction, ChunkActionMixin


class Move(DefineAction, ChunkActionMixin):
    """
    最基础的移动动作，在tile之间进行切换。
    """

    COMMENT = "移动到某个相对位置"
    PARAMS = {"delta_x": "int", "delta_y": "int"}

    def _execute(self, delta_x: int, delta_y: int) -> None:
        """
        移动到某个tile
        """
        world = self.world
        # 基于境界的移动步长：每轴最多移动 move_step_length 格
        step = getattr(self.avatar, "move_step_length", 1)
        clamped_dx = max(-step, min(step, delta_x))
        clamped_dy = max(-step, min(step, delta_y))

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


