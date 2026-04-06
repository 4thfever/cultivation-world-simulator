from __future__ import annotations

from src.classes.core.world import World
from src.utils.config import CONFIG

from .context import SimulationStepContext
from .finalizer import finalize_step
from .phases import actions, annual, lifecycle, sect_war, social, world as world_phases


class Simulator:
    def __init__(self, world: World):
        self.world = world
        run_config = getattr(world, "run_config_snapshot", {}) or {}
        self.awakening_rate = float(run_config.get("npc_awakening_rate_per_month", 0.01))
        self.can_interrupt_major = getattr(CONFIG.world, "can_interrupt_major_events", False)

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
        # step() 只保留“按顺序编排 phase”这一件事。
        # 具体业务细节分散到 phases/ 与 finalizer 中，方便后续继续拆分。
        ctx = SimulationStepContext.create(self.world)

        # 1. 更新感知与知识
        ctx.add_events(world_phases.phase_update_perception_and_knowledge(self.world, ctx.living_avatars))

        # 2. 长期目标思考
        ctx.add_events(await lifecycle.phase_long_term_objective_thinking(ctx.living_avatars))

        # 3. Gathering 系统
        ctx.add_events(await world_phases.phase_process_gatherings(self.world))

        # 4. AI 决策相位
        await actions.phase_decide_actions(self.world, ctx.living_avatars)

        # 5. 提交并启动下一步计划
        ctx.add_events(actions.phase_commit_next_plans(ctx.living_avatars))

        # 6. 执行当前行动
        ctx.add_events(await actions.phase_execute_actions(ctx.living_avatars))

        # 7. 处理基于事件的交互（第一轮）
        # 第一轮会把动作阶段产出的互动事件计入角色状态，
        # 让紧接着的关系演化可以在同月看到这些变化。
        social.phase_handle_interactions(self.world.avatar_manager, ctx.events, ctx.processed_event_ids)

        # 8. 关系演化
        ctx.add_events(await social.phase_evolve_relations(self.world.avatar_manager, ctx.living_avatars))

        # 9. 死亡结算（会更新 living_avatars）
        ctx.add_events(lifecycle.phase_resolve_death(self.world, ctx.living_avatars))

        # 10. 年龄更新 + 出生/觉醒
        ctx.add_events(lifecycle.phase_update_age_and_birth(self.world, ctx.living_avatars))

        # 11. 身世背景生成
        await lifecycle.phase_backstory_generation(ctx.living_avatars)

        # 12. 被动效果 + 世界性事件
        ctx.add_events(await world_phases.phase_passive_effects(self.world, ctx.living_avatars))

        # 13. 角色自主创作 + 小型随机事件 + 宗门随机事件
        ctx.add_events(await world_phases.phase_autonomous_custom_creation(self.world, ctx.living_avatars))
        ctx.add_events(await world_phases.phase_random_minor_events(self.world, ctx.living_avatars))
        ctx.add_events(await world_phases.phase_sect_random_event(self.world))

        # 13.5 宗门战争遭遇战
        ctx.add_events(await sect_war.phase_handle_sect_wars(self, ctx.living_avatars))

        # 14. 外号生成
        ctx.add_events(await lifecycle.phase_nickname_generation(ctx.living_avatars))

        # 15. 更新天象
        ctx.add_events(world_phases.phase_update_celestial_phenomenon(self.world))

        # 16. 更新城市人口
        world_phases.phase_update_city_population(self.world)

        # 16.5 更新王朝皇帝状态
        ctx.add_events(world_phases.phase_update_dynasty(self.world))
        ctx.add_events(world_phases.phase_update_official_system(self.world, ctx.living_avatars))

        # 17. 再次按事件处理交互（包含后续新事件）
        # 第二轮只处理本月后半程新增的互动事件。
        # 由于关系演化已在前面执行，这些新增互动会影响下个月的关系判定。
        social.phase_handle_interactions(self.world.avatar_manager, ctx.events, ctx.processed_event_ids)

        # 18. 计算型关系更新（二阶关系等）
        social.phase_update_calculated_relations(self.world, ctx.living_avatars)

        # 19. 每年一月：世界年度维护
        await annual.run_annual_maintenance(self, ctx)

        # 20. 最终收尾并返回本回合事件列表
        return finalize_step(ctx)
