"""
通用 AI 任务批处理器。
用于将串行的异步任务收集起来并行执行，优化 LLM 密集型场景的性能。
"""
import asyncio
from typing import Coroutine, Any, List

class AITaskBatch:
    """
    AI 任务批处理器。
    
    使用示例:
    ```python
    async with AITaskBatch() as batch:
        for item in items:
            batch.add(process_item(item))
    # with 块结束时，所有任务已并发执行完毕
    ```
    """
    def __init__(self):
        self.tasks: List[Coroutine[Any, Any, Any]] = []

    def add(self, coro: Coroutine[Any, Any, Any]) -> None:
        """
        添加一个协程任务到池中（不立即执行）。
        注意：传入的协程应该自行处理结果（如修改对象状态），或者通过外部变量收集结果。
        """
        self.tasks.append(coro)

    async def run(self) -> List[Any]:
        """
        并行执行池中所有任务，并等待全部完成。
        返回所有任务的结果列表（顺序与添加顺序一致）。
        """
        if not self.tasks:
            return []
        
        # 使用 gather 并发执行
        results = await asyncio.gather(*self.tasks)
        
        # 清空任务队列
        self.tasks = []
        return list(results)

    async def __aenter__(self) -> "AITaskBatch":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        # 如果 with 块内部发生异常，不执行任务，直接抛出
        if exc_type:
            return
        await self.run()

