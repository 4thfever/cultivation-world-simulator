from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Optional


def schedule_background(coro: Awaitable, *, fallback: Optional[Callable[[], None]] = None) -> None:
    """
    在有事件循环时将协程投递为后台任务；否则执行同步回退。

    - coro: 需要异步执行的协程对象
    - fallback: 无事件循环时的回退执行函数（可为空）
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        if fallback is not None:
            fallback()
        else:
            # 无回退则静默返回，调用方自行决定后续行为
            return


