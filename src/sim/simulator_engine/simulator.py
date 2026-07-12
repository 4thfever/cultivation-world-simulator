from __future__ import annotations

from src.classes.event import Event
from src.classes.core.world import World
from src.config.providers import StaticConfigProvider

from .phase_runner import SimulationPhaseRunner


class Simulator:
    def __init__(self, world: World):
        self.world = world
        run_config = getattr(world, "run_config_snapshot", {}) or {}
        self.awakening_rate = float(run_config.get("npc_awakening_rate_per_month", 0.01))
        self.config_provider = StaticConfigProvider.current()
        self.can_interrupt_major = self.config_provider.can_interrupt_major_events()

        from src.sim.managers.sect_manager import SectManager

        self.sect_manager = SectManager(world)

    async def step(self) -> list[Event]:
        """
        模拟器单步主流程（一个月的推进）。

        相位顺序：
        1.  更新角色感知与已知区域
        2.  长期目标思考
        3.  Gathering 系统（聚会/大会）处理
        4.  AI 决策（为无计划角色生成行动链）
        5.  提交并启动下一步计划
        6.  执行当前行动（多轮 Tick，直到稳定或达到上限）
        7.  按事件处理交互（第一轮）
        8.  关系演化相位
        9.  死亡结算
        10. 年龄更新与出生/觉醒处理
        11. 身世背景生成
        12. 被动效果与世界性随机事件
        13. 小型随机事件 + 宗门随机事件
        14. 外号生成
        15. 天象（大环境气候）更新
        16. 城市人口更新
        17. 按事件处理交互（第二轮，包含后续新事件）
        18. 计算型关系（如二阶关系）更新
        19. 每年一月：世界年度维护
        20. 最终整理事件、入库、写日志并推进月份
        """
        return await SimulationPhaseRunner(self).run()
