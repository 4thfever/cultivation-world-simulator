from __future__ import annotations


def clamp_manhattan_with_diagonal_priority(dx: int, dy: int, step: int) -> tuple[int, int]:
    """
    在不超过给定曼哈顿步长 step 的前提下，对 (dx, dy) 进行裁剪，且优先斜向移动。

    规则：
    - 返回的 (mx, my) 满足 |mx| + |my| <= step
    - 每轴不超过原目标量：|mx| <= |dx|, |my| <= |dy|
    - 优先分配斜向步（即同时占用 x 与 y 各 1 步），其后再把剩余步数分配给剩余距离更大的轴
    - 保持原方向（符号）
    """
    if step <= 0 or (dx == 0 and dy == 0):
        return 0, 0

    abs_dx = abs(dx)
    abs_dy = abs(dy)
    sign_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
    sign_y = 1 if dy > 0 else (-1 if dy < 0 else 0)

    # 实际可用预算不超过所需的曼哈顿距离
    budget = min(step, abs_dx + abs_dy)

    # 先分配尽量多的斜向步：每个斜向步消耗 2 点预算
    diagonal_steps = min(min(abs_dx, abs_dy), budget // 2)
    move_x = diagonal_steps
    move_y = diagonal_steps

    remaining = budget - 2 * diagonal_steps

    # 若还有剩余预算，分配给剩余距离更大的轴
    rem_x = abs_dx - move_x
    rem_y = abs_dy - move_y
    if remaining > 0:
        if rem_x >= rem_y:
            add_x = min(remaining, rem_x)
            move_x += add_x
            remaining -= add_x
        if remaining > 0:
            add_y = min(remaining, rem_y)
            move_y += add_y

    return move_x * sign_x, move_y * sign_y


