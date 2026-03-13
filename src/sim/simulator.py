import random
import asyncio
from typing import TYPE_CHECKING

from src.systems.time import Month, Year, MonthStamp
from src.classes.core.avatar import Avatar, Gender
from src.sim.avatar_awake import process_awakening
from src.classes.age import Age
from src.systems.cultivation import Realm
from src.classes.core.world import World
from src.classes.event import Event, is_null_event
from src.classes.ai import llm_ai
from src.utils.name_generator import get_random_name
from src.utils.config import CONFIG
from src.run.log import get_logger
from src.systems.fortune import try_trigger_fortune
from src.systems.fortune import try_trigger_misfortune
from src.systems.random_minor_event import try_trigger_random_minor_event
from src.systems.sect_random_event import try_trigger_sect_random_event
from src.classes.celestial_phenomenon import get_random_celestial_phenomenon
from src.classes.long_term_objective import process_avatar_long_term_objective
from src.classes.death import handle_death
from src.classes.death_reason import DeathReason, DeathType
from src.i18n import t
from src.classes.observe import get_avatar_observation_radius
from src.classes.environment.region import CultivateRegion, CityRegion
from src.classes.birth import process_births
from src.classes.nickname import process_avatar_nickname
from src.classes.backstory import process_avatar_backstory
from src.classes.relation.relation_resolver import RelationResolver
from src.classes.relation.relations import update_second_degree_relations
from src.classes.sect_decider import SectDecider

SECT_THINKING_INTERVAL_YEARS = 5

class Simulator:
    def __init__(self, world: World):
        self.world = world
        # 每月 NPC 觉醒比例（由凡人转为修真者的概率）
        self.awakening_rate = CONFIG.game.npc_awakening_rate_per_month
        self.can_interrupt_major = getattr(CONFIG.game, 'can_interrupt_major_events', False)
        
        from src.sim.managers.sect_manager import SectManager
        self.sect_manager = SectManager(world)

    def _phase_update_perception_and_knowledge(self, living_avatars: list[Avatar]):
        """
        更新角色的感知与知识。

        1. 根据角色当前位置与视野半径，刷新其 `known_regions`
        2. 对尚未拥有洞府/修炼地的角色，尝试占据经过的空闲修炼区域
        """
        events = []
        # 1. 预先记录已有洞府的角色 ID
        avatars_with_home = set()
        # ...
        cultivate_regions = [
            r for r in self.world.map.regions.values() 
            if isinstance(r, CultivateRegion)
        ]
        
        for r in cultivate_regions:
            if r.host_avatar:
                avatars_with_home.add(r.host_avatar.id)

        # 2. 遍历所有在世角色，按各自视野范围进行探索
        for avatar in living_avatars:
            # ...
            # 计算角色的感知半径（观测范围）
            radius = get_avatar_observation_radius(avatar)
            
            # ...
            # 按菱形范围（曼哈顿距离）遍历可见坐标
            start_x = max(0, avatar.pos_x - radius)
            end_x = min(self.world.map.width - 1, avatar.pos_x + radius)
            start_y = max(0, avatar.pos_y - radius)
            end_y = min(self.world.map.height - 1, avatar.pos_y + radius)

            # 收集本次观察到的全部区域
            observed_regions = set()
            for x in range(start_x, end_x + 1):
                for y in range(start_y, end_y + 1):
                    # 只在视野半径内（曼哈顿距离）时，才算作真正观察到
                    if abs(x - avatar.pos_x) + abs(y - avatar.pos_y) <= radius:
                        tile = self.world.map.get_tile(x, y)
                        if tile.region:
                            observed_regions.add(tile.region)

            # 将区域加入角色的已知区域，并处理可能的占据逻辑
            for region in observed_regions:
                # 更新角色 known_regions
                avatar.known_regions.add(region.id)
                
                # 对空闲的修炼区域，允许无洞府的角色占据
                # 条件：区域是修炼区 + 当前无人占据 + 角色目前没有自己的修炼地
                if isinstance(region, CultivateRegion):
                    if region.host_avatar is None:
                        if avatar.id not in avatars_with_home:
                            # 角色占据该区域
                            avatar.occupy_region(region)
                            avatars_with_home.add(avatar.id)
                            # 记录事件
                            event = Event(
                                self.world.month_stamp,
                                t("{avatar_name} passed by {region_name}, found it ownerless, and occupied it.", 
                                  avatar_name=avatar.name, region_name=region.name),
                                related_avatars=[avatar.id]
                            )
                            events.append(event)
        return events

    async def _phase_decide_actions(self, living_avatars: list[Avatar]):
        """
        为没有当前行动且没有计划的角色决定下一步行动。

        由 LLM AI 统一决策：为每个角色生成行动链、思考内容和短期目标，并写入其内部计划队列。
        """
        avatars_to_decide = []
        for avatar in living_avatars:
            if avatar.current_action is None and not avatar.has_plans():
                avatars_to_decide.append(avatar)
        if not avatars_to_decide:
            return
        ai = llm_ai
        decide_results = await ai.decide(self.world, avatars_to_decide)
        for avatar, result in decide_results.items():
            action_name_params_pairs, avatar_thinking, short_term_objective, _event = result
            # 将 AI 决策结果写回角色：行动链 + 思考内容 + 短期目标
            avatar.load_decide_result_chain(action_name_params_pairs, avatar_thinking, short_term_objective)

    def _phase_commit_next_plans(self, living_avatars: list[Avatar]):
        """
        提交并启动角色的下一步计划。

        对当前没有正在执行行动的角色，从其计划队列中取出下一个计划并开始执行，产生的开始事件会被收集。
        """
        events = []
        for avatar in living_avatars:
            if avatar.current_action is None:
                start_event = avatar.commit_next_plan()
                if start_event is not None and not is_null_event(start_event):
                    events.append(start_event)
        return events

    async def _phase_execute_actions(self, living_avatars: list[Avatar]):
        """
        执行所有角色当前行动。

        - 先进行一轮 `tick_action`
        - 如果在 `tick_action` 中设置了新的行动（如连携动作），会在同一回合内继续补充执行，直到达到上限或队列稳定
        """
        events = []
        MAX_LOCAL_ROUNDS = CONFIG.game.max_action_rounds_per_turn
        
        # Round 1: 首轮执行所有角色当前行动
        avatars_needing_retry = set()
        for avatar in living_avatars:
            try:
                new_events = await avatar.tick_action()
                if new_events:
                    events.extend(new_events)
                
                # 如果在 `tick_action` 内为角色设置了新的行动
                # （例如当前行动结束后无缝衔接另一行动），需要在本回合内再次执行
                if getattr(avatar, "_new_action_set_this_step", False):
                    avatars_needing_retry.add(avatar)
            except Exception as e:
                # 记录执行错误日志，避免整个模拟中断
                get_logger().logger.error(f"Avatar {avatar.name}({avatar.id}) tick_action failed: {e}", exc_info=True)
                # 若已标记“本步设置过新行动”，这里显式复位，避免死循环
                if hasattr(avatar, "_new_action_set_this_step"):
                     avatar._new_action_set_this_step = False

        # Round 2+: 针对需要重试的角色，继续在同一回合内补充执行
        round_count = 1
        while avatars_needing_retry and round_count < MAX_LOCAL_ROUNDS:
            current_avatars = list(avatars_needing_retry)
            avatars_needing_retry.clear()
            
            for avatar in current_avatars:
                try:
                    new_events = await avatar.tick_action()
                    if new_events:
                        events.extend(new_events)
                    
                    # 同上：若本步又设置了新行动，则加入重试队列
                    if getattr(avatar, "_new_action_set_this_step", False):
                        avatars_needing_retry.add(avatar)
                except Exception as e:
                    get_logger().logger.error(f"Avatar {avatar.name}({avatar.id}) retry tick_action failed: {e}", exc_info=True)
                    if hasattr(avatar, "_new_action_set_this_step"):
                        avatar._new_action_set_this_step = False
            
            round_count += 1
            
        return events

    def _phase_resolve_death(self, living_avatars: list[Avatar]):
        """
        处理角色死亡结算。

        - 根据当前生命值与寿元判断是否死亡
        - 将死亡角色从 `living_avatars` 中移除，并调用 `handle_death` 进行收尾处理

        注意：该阶段会原地修改 `living_avatars`，后续相位不应再处理这些已死亡角色。
        """
        events = []
        dead_avatars = []
        
        for avatar in living_avatars:
            is_dead = False
            death_reason: DeathReason | None = None
            
            # 生命值归零视为重伤死亡
            if avatar.hp.cur <= 0:
                is_dead = True
                death_reason = DeathReason(DeathType.SERIOUS_INJURY)
            # 寿元耗尽视为寿终
            elif avatar.death_by_old_age():
                is_dead = True
                death_reason = DeathReason(DeathType.OLD_AGE)
                
            if is_dead and death_reason:
                event = Event(self.world.month_stamp, f"{avatar.name}{death_reason}", related_avatars=[avatar.id])
                events.append(event)
                handle_death(self.world, avatar, death_reason)
                dead_avatars.append(avatar)
        
        # 从 living_avatars 中移除已死亡角色，后续 Phase 不再处理
        for dead in dead_avatars:
            if dead in living_avatars:
                living_avatars.remove(dead)
                
        return events

    def _phase_update_age_and_birth(self, living_avatars: list[Avatar]):
        """
        更新年龄并处理出生/觉醒相关逻辑。

        - 为所有在世角色刷新年龄
        - 清理凡人管理器中的已死亡凡人
        - 处理新一轮觉醒与出生事件
        """
        events = []
        for avatar in living_avatars:
            avatar.update_age(self.world.month_stamp)
            
        # 1. 清理已死亡凡人（从凡人管理器中移除）
        self.world.mortal_manager.cleanup_dead_mortals(self.world.month_stamp)
        
        # 2. 凡人觉醒为修真者（觉醒 + 入世）
        awakening_events = process_awakening(self.world)
        if awakening_events:
            events.extend(awakening_events)
            
        # 3. 处理新出生事件
        birth_events = process_births(self.world)
        if birth_events:
            events.extend(birth_events)
            
        return events

    async def _phase_passive_effects(self, living_avatars: list[Avatar]):
        """
        处理各种被动效果与世界性随机事件。

        - 处理丹药过期
        - 刷新持续性状态效果（如增减 HP、属性等）
        - 触发福缘/劫难等世界性事件
        """
        events = []
        for avatar in living_avatars:
        # 1. 丹药过期处理
            avatar.process_elixir_expiration(int(self.world.month_stamp))
            # 2. 更新时间相关被动效果（包括 HP 等）
            avatar.update_time_effect()
        
        # 从中筛选可以触发世界事件的角色
        target_avatars = [
            avatar for avatar in living_avatars 
            if avatar.can_trigger_world_event
        ]
        
        # 使用 asyncio.gather 并发触发福缘/劫难检查
        tasks_fortune = [try_trigger_fortune(avatar) for avatar in target_avatars]
        tasks_misfortune = [try_trigger_misfortune(avatar) for avatar in target_avatars]
        results = await asyncio.gather(*(tasks_fortune + tasks_misfortune))
        
        events.extend([e for res in results if res for e in res])
                
        return events
    
    async def _phase_random_minor_events(self, living_avatars: list[Avatar]):
        """
        小型随机事件相位：为可触发世界事件的角色尝试触发随机小事件。
        """
        target_avatars = [av for av in living_avatars if av.can_trigger_world_event]
        tasks = [try_trigger_random_minor_event(av, self.world) for av in target_avatars]
        results = await asyncio.gather(*tasks)
        return [e for e in results if e]

    async def _phase_sect_random_event(self):
        event = await try_trigger_sect_random_event(self.world)
        return [event] if event else []

    async def _phase_sect_yearly_thinking(self):
        """
        宗门年度思考。

        每隔一段年份（默认 5 年），在每年一月为所有启用的宗门生成年度思考 `yearly_thinking`，
        并写入事件流，供前端展示。
        """
        if self.world.month_stamp.get_month() != Month.JANUARY:
            return []
        current_year = int(self.world.month_stamp.get_year())
        start_year = int(getattr(self.world, "start_year", current_year))
        if current_year < start_year:
            return []
        if (current_year - start_year) % SECT_THINKING_INTERVAL_YEARS != 0:
            return []

        sect_context = getattr(self.world, "sect_context", None)
        active_sects = (
            sect_context.get_active_sects()
            if sect_context is not None
            else (getattr(self.world, "existed_sects", []) or [])
        )
        if not active_sects:
            return []

        event_storage = getattr(getattr(self.world, "event_manager", None), "_storage", None)
        if event_storage is None:
            return []

        from src.classes.core.sect import get_sect_decision_context
        events: list[Event] = []

        async def _decide_one(sect):
            try:
                ctx = get_sect_decision_context(
                    sect=sect,
                    world=self.world,
                    event_storage=event_storage,
                )
                sect.yearly_thinking = await SectDecider.decide(sect, ctx, self.world)
                events.append(
                    Event(
                        self.world.month_stamp,
                        t("game.sect_thinking_event", sect_name=sect.name, thinking=sect.yearly_thinking),
                        related_sects=[int(sect.id)],
                    )
                )
            except Exception as e:
                get_logger().logger.error(
                    "Sect yearly thinking failed for %s(%s): %s",
                    getattr(sect, "name", "unknown"),
                    getattr(sect, "id", "unknown"),
                    e,
                    exc_info=True,
                )

        await asyncio.gather(*[_decide_one(sect) for sect in active_sects])
        return events

    async def _phase_nickname_generation(self, living_avatars: list[Avatar]):
        """
        处理外号/绰号生成相位。
        """
        # 并发处理所有在世角色
        tasks = [process_avatar_nickname(avatar) for avatar in living_avatars]
        results = await asyncio.gather(*tasks)
        
        events = [e for e in results if e]
        return events
    
    async def _phase_backstory_generation(self, living_avatars: list[Avatar]):
        """
        处理角色身世背景生成相位。

        只为尚未拥有背景的角色生成身世描述，调用 LLM 生成内容，并写回到角色上。
        """
        avatars_to_process = [av for av in living_avatars if av.backstory is None]
        if not avatars_to_process:
            return
            
        tasks = [process_avatar_backstory(avatar) for avatar in avatars_to_process]
        await asyncio.gather(*tasks)

    async def _phase_long_term_objective_thinking(self, living_avatars: list[Avatar]):
        """
        处理长期目标思考相位。

        让每个角色根据当前状态更新或生成长期目标，并返回产生的事件。
        """
        # 并发处理所有在世角色
        tasks = [process_avatar_long_term_objective(avatar) for avatar in living_avatars]
        results = await asyncio.gather(*tasks)
        
        events = [e for e in results if e]
        return events
    
    async def _phase_process_gatherings(self):
        """
        处理 Gathering（聚会/大会）系统相位。

        当年份条件满足时，由 `gathering_manager` 统一检查并运行所有聚会逻辑，返回产生的事件。
        """
        # 开局年份内不触发聚会，避免世界尚未稳定时产生无意义事件
        if self.world.month_stamp.get_year() <= self.world.start_year:
            return []

        return await self.world.gathering_manager.check_and_run_all(self.world)
    
    def _phase_update_celestial_phenomenon(self):
        """
        更新世界天象（大环境修行气候）。

        - 根据当前年份与上一个天象持续时间，决定是否切换天象
        - 初始化世界时会生成第一个天象
        - 切换或生成新天象时，会写入对应的世界事件

        说明：
        - 天象数据由 `get_random_celestial_phenomenon()` 提供，包含名称、描述和持续年数
        - 只有在一月才会检查是否需要结束旧天象并切换到新天象
        """
        events = []
        current_year = self.world.month_stamp.get_year()
        current_month = self.world.month_stamp.get_month()
        
        # 判断是否需要更新当前天象
        # 1. 当前没有天象（世界初始化时）
        # 2. 到了一月且当前天象已持续满预定年数
        should_update = False
        is_init = False
        
        if self.world.current_phenomenon is None:
            should_update = True
            is_init = True
        elif current_month == Month.JANUARY:
            elapsed_years = current_year - self.world.phenomenon_start_year
            if elapsed_years >= self.world.current_phenomenon.duration_years:
                should_update = True

        if should_update:
            old_phenomenon = self.world.current_phenomenon
            new_phenomenon = get_random_celestial_phenomenon()
            
            if new_phenomenon:
                self.world.current_phenomenon = new_phenomenon
                self.world.phenomenon_start_year = current_year
                
                desc = ""
                if is_init:
                    desc = t("world_creation_phenomenon", name=new_phenomenon.name, desc=new_phenomenon.desc)
                else:
                    desc = t("phenomenon_change", old_name=old_phenomenon.name, new_name=new_phenomenon.name, new_desc=new_phenomenon.desc)
                
                event = Event(
                    self.world.month_stamp,
                    desc,
                    related_avatars=None
                )
                events.append(event)
        
        return events

    def _phase_update_region_prosperity(self):
        """
        更新区域繁荣度。
        """
        for region in self.world.map.regions.values():
            if isinstance(region, CityRegion):
                region.change_prosperity(1)

    def _phase_log_events(self, events):
        """
        将本回合产生的事件写入日志。
        """
        logger = get_logger().logger
        for event in events:
            logger.info("EVENT: %s", str(event))

    def _phase_process_interactions(self, events: list[Event]):
        """
        根据事件处理角色间的交互影响。

        只处理 `related_avatars` 数量不少于 2 的事件，并将交互效果分发到每个相关角色。
        """
        for event in events:
            if not event.related_avatars or len(event.related_avatars) < 2:
                continue
            
            # 遍历 related_avatars（>=2 时），让每个相关角色处理该交互
            for aid in event.related_avatars:
                avatar = self.world.avatar_manager.get_avatar(aid)
                if avatar:
                    avatar.process_interaction_from_event(event)

    def _phase_handle_interactions(self, events: list[Event], processed_ids: set[str]):
        """
        过滤并调度需要处理的交互事件。

        - 使用 `processed_ids` 避免同一事件被多次处理
        - 把新的交互事件统一交给 `_phase_process_interactions`
        """
        new_interactions = []
        for e in events:
            if e.id not in processed_ids:
                if e.related_avatars and len(e.related_avatars) >= 2:
                    new_interactions.append(e)
                processed_ids.add(e.id)
        
        if new_interactions:
            self._phase_process_interactions(new_interactions)

    async def _phase_evolve_relations(self, living_avatars: list[Avatar]):
        """
        处理角色关系演化相位。

        - 汇总达到检查阈值的互动对
        - 通过 `RelationResolver.run_batch` 统一决议关系变化
        """
        pairs_to_resolve = []
        processed_pairs = set() # (id1, id2) id1 < id2
        
        for avatar in living_avatars:
            target_ids = list(avatar.relation_interaction_states.keys())
            
            for target_id in target_ids:
                state = avatar.relation_interaction_states[target_id]
                target = self.world.avatar_manager.get_avatar(target_id)
                
                if target is None or target.is_dead:
                    continue

                # 使用配置中的互动计数阈值
                threshold = CONFIG.social.relation_check_threshold
                if state["count"] >= threshold:
                    # 将 ID 排序后组成唯一 key，避免双方互相重复处理
                    id1, id2 = sorted([str(avatar.id), str(target.id)])
                    pair_key = (id1, id2)
                    
                    if pair_key not in processed_pairs:
                        processed_pairs.add(pair_key)
                        pairs_to_resolve.append((avatar, target))
                        
                        # 重置双方的计数，避免短时间内重复判定
                        # 1. 重置 A 侧计数
                        state["count"] = 0
                        state["checked_times"] += 1
                        
                        # 2. 重置 B 侧计数
                        t_state = target.relation_interaction_states[str(avatar.id)]
                        t_state["count"] = 0
                        t_state["checked_times"] += 1
        
        events = []
        if pairs_to_resolve:
            # 对收集到的配对关系进行批量决议
            relation_events = await RelationResolver.run_batch(pairs_to_resolve)
            if relation_events:
                events.extend(relation_events)
            
        return events

    async def step(self):
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
        16. 区域繁荣度更新
        17. 按事件处理交互（第二轮，包含后续新事件）
        18. 计算型关系（如二阶关系）更新
        19. 每年一月：更新世界排行榜与宗门状态 + 宗门年度思考
        20. 每年一月：清理长久死亡的角色
        21. 最终整理事件、入库、写日志并推进月份
        """
        # 0. 获取当前在世角色列表（本回合缓存）
        living_avatars = self.world.avatar_manager.get_living_avatars()

        events: list[Event] = []
        processed_event_ids: set[str] = set()

        # 1. 更新感知与知识
        events.extend(self._phase_update_perception_and_knowledge(living_avatars))

        # 2. 长期目标思考
        events.extend(await self._phase_long_term_objective_thinking(living_avatars))

        # 3. Gathering 系统
        events.extend(await self._phase_process_gatherings())

        # 4. AI 决策相位
        await self._phase_decide_actions(living_avatars)

        # 5. 提交并启动下一步计划
        events.extend(self._phase_commit_next_plans(living_avatars))

        # 6. 执行当前行动
        events.extend(await self._phase_execute_actions(living_avatars))

        # 7. 处理基于事件的交互（第一轮）
        self._phase_handle_interactions(events, processed_event_ids)

        # 8. 关系演化
        events.extend(await self._phase_evolve_relations(living_avatars))

        # 9. 死亡结算（会更新 living_avatars）
        events.extend(self._phase_resolve_death(living_avatars))

        # 10. 年龄更新 + 出生/觉醒
        events.extend(self._phase_update_age_and_birth(living_avatars))

        # 11. 身世背景生成
        await self._phase_backstory_generation(living_avatars)

        # 12. 被动效果 + 世界性事件
        events.extend(await self._phase_passive_effects(living_avatars))

        # 13. 小型随机事件 + 宗门随机事件
        events.extend(await self._phase_random_minor_events(living_avatars))
        events.extend(await self._phase_sect_random_event())

        # 14. 外号生成
        events.extend(await self._phase_nickname_generation(living_avatars))

        # 15. 更新天象
        events.extend(self._phase_update_celestial_phenomenon())

        # 16. 更新区域繁荣度
        self._phase_update_region_prosperity()

        # 17. 再次按事件处理交互（包含后续新事件）
        self._phase_handle_interactions(events, processed_event_ids)

        # 18. 计算型关系更新（二阶关系等）
        self._phase_update_calculated_relations(living_avatars)

        ###########
        # ===== 以下为每年一月才会触发的阶段 =====
        ###########
        
        # 19. 每年一月：更新排行榜与宗门状态 + 宗门年度思考
        if self.world.month_stamp.get_month() == Month.JANUARY:
            # 同步世界排行榜（包含主角与重要角色）
            self.world.ranking_manager.update_rankings_with_world(self.world, living_avatars)

            # 宗门年度维护（宗门状态、势力等）
            sect_events = self.sect_manager.update_sects()
            if sect_events:
                events.extend(sect_events)
            events.extend(await self._phase_sect_yearly_thinking())
        
        # 20. 每年一月：清理长久死亡的角色
        if self.world.month_stamp.get_month() == Month.JANUARY:
            cleaned_count = self.world.avatar_manager.cleanup_long_dead_avatars(
                self.world.month_stamp, 
                CONFIG.game.long_dead_cleanup_years
            )
            if cleaned_count > 0:
                # 记录清理数量，方便调试观察世界规模变化
                get_logger().logger.info(f"Cleaned up {cleaned_count} long-dead avatars.")

        # 21. 最终收尾并返回本回合事件列表
        return self._finalize_step(events)

    def _phase_update_calculated_relations(self, living_avatars: list[Avatar]):
        """
        处理基于规则计算的关系（如二阶关系）更新。
        """
        # 仅在每年一月执行一次
        if self.world.month_stamp.get_month() != Month.JANUARY:
            return

        for avatar in living_avatars:
            update_second_degree_relations(avatar)

    def _finalize_step(self, events: list[Event]) -> list[Event]:
        """
        本回合最后的统一收尾。

        - 记录角色指标（如调试用的统计信息）
        - 事件去重与入库
        - 写入日志
        - 推进世界时间（月份 +1）
        """
        # 0. 记录角色调试指标（若启用）
        for avatar in self.world.avatar_manager.avatars.values():
            if avatar.enable_metrics_tracking:
                avatar.record_metrics()

        # 1. 按事件 ID 去重，同一事件只保留一条
        unique_events: dict[str, Event] = {}
        for e in events:
            if e.id not in unique_events:
                unique_events[e.id] = e
        final_events = list(unique_events.values())

        # 2. 将事件写入事件管理器（入库）
        if self.world.event_manager:
            for e in final_events:
                self.world.event_manager.add_event(e)
        
        # 3. 写日志
        self._phase_log_events(final_events)

        # 4. 推进月份
        self.world.month_stamp = self.world.month_stamp + 1
        
        return final_events
