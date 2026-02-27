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

class Simulator:
    def __init__(self, world: World):
        self.world = world
        self.awakening_rate = CONFIG.game.npc_awakening_rate_per_month  # 从配置文件读取NPC每月觉醒率（凡人晋升修士）

    def _phase_update_perception_and_knowledge(self, living_avatars: list[Avatar]):
        """
        感知更新阶段：
        1. 基于感知范围更新 known_regions
        2. 自动占据无主洞府（如果自己没有洞府）
        """
        events = []
        # 1. 缓存当前有洞府的角色ID
        avatars_with_home = set()
        # ...
        cultivate_regions = [
            r for r in self.world.map.regions.values() 
            if isinstance(r, CultivateRegion)
        ]
        
        for r in cultivate_regions:
            if r.host_avatar:
                avatars_with_home.add(r.host_avatar.id)

        # 2. 遍历所有存活角色
        for avatar in living_avatars:
            # ...
            # 计算感知半径（曼哈顿距离）
            radius = get_avatar_observation_radius(avatar)
            
            # ...
            # 获取范围内的有效坐标
            start_x = max(0, avatar.pos_x - radius)
            end_x = min(self.world.map.width - 1, avatar.pos_x + radius)
            start_y = max(0, avatar.pos_y - radius)
            end_y = min(self.world.map.height - 1, avatar.pos_y + radius)

            # 收集感知到的区域
            observed_regions = set()
            for x in range(start_x, end_x + 1):
                for y in range(start_y, end_y + 1):
                    # 距离判定：曼哈顿距离
                    if abs(x - avatar.pos_x) + abs(y - avatar.pos_y) <= radius:
                        tile = self.world.map.get_tile(x, y)
                        if tile.region:
                            observed_regions.add(tile.region)

            # 更新认知与自动占据
            for region in observed_regions:
                # 更新 known_regions
                avatar.known_regions.add(region.id)
                
                # 自动占据逻辑
                # 只有当：是修炼区域 + 无主 + 自己无洞府 时触发
                if isinstance(region, CultivateRegion):
                    if region.host_avatar is None:
                        if avatar.id not in avatars_with_home:
                            # 占据
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
        决策阶段：仅对需要新计划的角色调用 AI（当前无动作且无计划），
        将 AI 的决策结果加载为角色的计划链。
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
            # 仅入队计划，不在此处添加开始事件，避免与提交阶段重复
            avatar.load_decide_result_chain(action_name_params_pairs, avatar_thinking, short_term_objective)

    def _phase_commit_next_plans(self, living_avatars: list[Avatar]):
        """
        提交阶段：为空闲角色提交计划中的下一个可执行动作，返回开始事件集合。
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
        执行阶段：推进当前动作，支持同月链式抢占即时结算，返回期间产生的事件。
        """
        events = []
        MAX_LOCAL_ROUNDS = CONFIG.game.max_action_rounds_per_turn
        
        # Round 1: 全员执行一次
        avatars_needing_retry = set()
        for avatar in living_avatars:
            try:
                new_events = await avatar.tick_action()
                if new_events:
                    events.extend(new_events)
                
                # 检查是否有新动作产生（抢占/连招），如果有则加入下一轮
                # 注意：tick_action 内部已处理标记清除逻辑，仅当动作发生切换时才会保留 True
                if getattr(avatar, "_new_action_set_this_step", False):
                    avatars_needing_retry.add(avatar)
            except Exception as e:
                # 记录详细错误日志
                get_logger().logger.error(f"Avatar {avatar.name}({avatar.id}) tick_action failed: {e}", exc_info=True)
                # 确保不会进入重试逻辑
                if hasattr(avatar, "_new_action_set_this_step"):
                     avatar._new_action_set_this_step = False

        # Round 2+: 仅执行有新动作的角色，避免无辜角色重复执行
        round_count = 1
        while avatars_needing_retry and round_count < MAX_LOCAL_ROUNDS:
            current_avatars = list(avatars_needing_retry)
            avatars_needing_retry.clear()
            
            for avatar in current_avatars:
                try:
                    new_events = await avatar.tick_action()
                    if new_events:
                        events.extend(new_events)
                    
                    # 再次检查
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
        结算死亡：
        - 战斗死亡已在 Action 中结算
        - 此时剩下的 avatars 都是存活的，只需检查非战斗因素（如老死、被动掉血）
        
        注意：如果发现死亡，会从传入的 living_avatars 列表中移除，避免后续阶段继续处理。
        """
        events = []
        dead_avatars = []
        
        for avatar in living_avatars:
            is_dead = False
            death_reason: DeathReason | None = None
            
            # 优先判定重伤（可能是被动效果导致）
            if avatar.hp.cur <= 0:
                is_dead = True
                death_reason = DeathReason(DeathType.SERIOUS_INJURY)
            # 其次判定寿元
            elif avatar.death_by_old_age():
                is_dead = True
                death_reason = DeathReason(DeathType.OLD_AGE)
                
            if is_dead and death_reason:
                event = Event(self.world.month_stamp, f"{avatar.name}{death_reason}", related_avatars=[avatar.id])
                events.append(event)
                handle_death(self.world, avatar, death_reason)
                dead_avatars.append(avatar)
        
        # 从当前引用的列表中移除，确保后续 Phase 不再处理
        for dead in dead_avatars:
            if dead in living_avatars:
                living_avatars.remove(dead)
                
        return events

    def _phase_update_age_and_birth(self, living_avatars: list[Avatar]):
        """
        更新存活角色年龄，并以一定概率生成新修士，返回期间产生的事件集合。
        """
        events = []
        for avatar in living_avatars:
            avatar.update_age(self.world.month_stamp)
            
        # 1. 凡人管理：清理老死凡人
        self.world.mortal_manager.cleanup_dead_mortals(self.world.month_stamp)
        
        # 2. 凡人觉醒 (血脉 + 野生)
        awakening_events = process_awakening(self.world)
        if awakening_events:
            events.extend(awakening_events)
            
        # 3. 道侣生子
        birth_events = process_births(self.world)
        if birth_events:
            events.extend(birth_events)
            
        return events

    async def _phase_passive_effects(self, living_avatars: list[Avatar]):
        """
        被动结算阶段：
        - 处理丹药过期
        - 更新时间效果（如HP回复）
        - 触发奇遇（非动作）
        """
        events = []
        for avatar in living_avatars:
            # 1. 处理丹药过期
            avatar.process_elixir_expiration(int(self.world.month_stamp))
            # 2. 更新被动效果 (如HP回复)
            avatar.update_time_effect()
        
        # 使用 gather 并行触发奇遇和霉运
        tasks_fortune = [try_trigger_fortune(avatar) for avatar in living_avatars]
        tasks_misfortune = [try_trigger_misfortune(avatar) for avatar in living_avatars]
        results = await asyncio.gather(*(tasks_fortune + tasks_misfortune))
        
        events.extend([e for res in results if res for e in res])
                
        return events
    
    async def _phase_nickname_generation(self, living_avatars: list[Avatar]):
        """
        绰号生成阶段
        """
        # 并发执行
        tasks = [process_avatar_nickname(avatar) for avatar in living_avatars]
        results = await asyncio.gather(*tasks)
        
        events = [e for e in results if e]
        return events
    
    async def _phase_backstory_generation(self, living_avatars: list[Avatar]):
        """
        身世生成阶段：
        找出所有尚未生成身世的存活角色，并发阻塞调用 LLM 生成。
        """
        avatars_to_process = [av for av in living_avatars if av.backstory is None]
        if not avatars_to_process:
            return
            
        tasks = [process_avatar_backstory(avatar) for avatar in avatars_to_process]
        await asyncio.gather(*tasks)

    async def _phase_long_term_objective_thinking(self, living_avatars: list[Avatar]):
        """
        长期目标思考阶段
        检查角色是否需要生成/更新长期目标
        """
        # 并发执行
        tasks = [process_avatar_long_term_objective(avatar) for avatar in living_avatars]
        results = await asyncio.gather(*tasks)
        
        events = [e for e in results if e]
        return events
    
    async def _phase_process_gatherings(self):
        """
        Gathering 结算阶段：
        检查并执行注册的多人聚集事件（如拍卖会、大比等）。
        """
        # 第一年不触发聚集事件，给予发育缓冲
        if self.world.month_stamp.get_year() <= self.world.start_year:
            return []

        return await self.world.gathering_manager.check_and_run_all(self.world)
    
    def _phase_update_celestial_phenomenon(self):
        """
        更新天地灵机：
        - 检查当前天象是否到期
        - 如果到期，则随机选择新天象
        - 生成世界事件记录天象变化
        
        天象变化时机：
        - 初始年份（如100年）1月立即开始第一个天象
        - 每N年（当前天象指定的持续时间）变化一次
        """
        events = []
        current_year = self.world.month_stamp.get_year()
        current_month = self.world.month_stamp.get_month()
        
        # 检查是否需要初始化或更新天象
        # 1. 如果没有天象 (初始化)
        # 2. 如果有天象且到期 (每年一月检查)
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
        每月城市繁荣度自然恢复
        """
        for region in self.world.map.regions.values():
            if isinstance(region, CityRegion):
                region.change_prosperity(1)

    def _phase_log_events(self, events):
        """
        将事件写入日志。
        """
        logger = get_logger().logger
        for event in events:
            logger.info("EVENT: %s", str(event))

    def _phase_process_interactions(self, events: list[Event]):
        """
        处理事件中的交互逻辑：
        遍历所有事件，如果事件涉及多个角色，自动更新这些角色之间的交互计数。
        """
        for event in events:
            if not event.related_avatars or len(event.related_avatars) < 2:
                continue
            
            # 只有当事件涉及 >=2 个角色时才视为交互
            for aid in event.related_avatars:
                avatar = self.world.avatar_manager.get_avatar(aid)
                if avatar:
                    avatar.process_interaction_from_event(event)

    def _phase_handle_interactions(self, events: list[Event], processed_ids: set[str]):
        """
        从事件列表中提取尚未处理过的交互事件，并更新交互计数。
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
        关系演化阶段：检查并处理满足条件的角色关系变化
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

                # 判定是否触发
                threshold = CONFIG.social.relation_check_threshold
                if state["count"] >= threshold:
                    # 确保唯一性
                    id1, id2 = sorted([str(avatar.id), str(target.id)])
                    pair_key = (id1, id2)
                    
                    if pair_key not in processed_pairs:
                        processed_pairs.add(pair_key)
                        pairs_to_resolve.append((avatar, target))
                        
                        # 重置双方的计数器，防止重复触发
                        # 1. 重置 A 侧
                        state["count"] = 0
                        state["checked_times"] += 1
                        
                        # 2. 重置 B 侧
                        t_state = target.relation_interaction_states[str(avatar.id)]
                        t_state["count"] = 0
                        t_state["checked_times"] += 1
        
        events = []
        if pairs_to_resolve:
            # 批量并发处理，并直接收集返回的事件
            relation_events = await RelationResolver.run_batch(pairs_to_resolve)
            if relation_events:
                events.extend(relation_events)
            
        return events

    async def step(self):
        """
        前进一个时间步（一个月）：
        1.  感知与认知更新（及自动占据洞府）
        2.  长期目标思考
        3.  Gathering 多人聚集结算
        4.  决策阶段 (AI 选择动作)
        5.  提交阶段 (开始执行动作)
        6.  执行阶段 (动作 Tick)
        7.  处理初步交互计数 (用于后续关系演化)
        8.  关系演化阶段
        9.  结算死亡
        10. 年龄与新生
        11. 身世生成
        12. 被动结算 (丹药、时间效果、奇遇)
        13. 绰号生成
        14. 天地灵机更新
        15. 城市繁荣度更新
        16. 处理剩余交互计数 (如奇遇产生的交互)
        17. (每年1月) 更新计算关系 (二阶关系)
        18. (每年1月) 更新榜单
        19. (每年1月) 清理由于时间久远而被遗忘的死者
        20. 归档与时间推进
        """
        # 0. 缓存本月存活角色列表 (在后续阶段中复用，并在死亡阶段维护)
        living_avatars = self.world.avatar_manager.get_living_avatars()

        events: list[Event] = []
        processed_event_ids: set[str] = set()

        # 1. 感知与认知更新
        events.extend(self._phase_update_perception_and_knowledge(living_avatars))

        # 2. 长期目标思考
        events.extend(await self._phase_long_term_objective_thinking(living_avatars))

        # 3. Gathering 结算
        events.extend(await self._phase_process_gatherings())

        # 4. 决策阶段
        await self._phase_decide_actions(living_avatars)

        # 5. 提交阶段
        events.extend(self._phase_commit_next_plans(living_avatars))

        # 6. 执行阶段
        events.extend(await self._phase_execute_actions(living_avatars))

        # 7. 处理初步交互计数
        self._phase_handle_interactions(events, processed_event_ids)

        # 8. 关系演化
        events.extend(await self._phase_evolve_relations(living_avatars))

        # 9. 结算死亡 (注意：此处会修改 living_avatars 列表)
        events.extend(self._phase_resolve_death(living_avatars))

        # 10. 年龄与新生
        events.extend(self._phase_update_age_and_birth(living_avatars))

        # 11. 身世生成
        await self._phase_backstory_generation(living_avatars)

        # 12. 被动结算
        events.extend(await self._phase_passive_effects(living_avatars))

        # 13. 绰号生成
        events.extend(await self._phase_nickname_generation(living_avatars))

        # 14. 更新天地灵机
        events.extend(self._phase_update_celestial_phenomenon())

        # 15. 更新城市繁荣度
        self._phase_update_region_prosperity()

        # 16. 处理剩余阶段的交互计数
        self._phase_handle_interactions(events, processed_event_ids)

        # 17. (每年1月) 更新计算关系 (二阶关系)
        self._phase_update_calculated_relations(living_avatars)

        ###########
        # 每年执行的行为
        ###########
        
        # 18. (每年1月) 更新榜单
        if self.world.month_stamp.get_month() == Month.JANUARY:
            self.world.ranking_manager.update_rankings(living_avatars)
        
        # 19. (每年1月) 清理由于时间久远而被遗忘的死者
        if self.world.month_stamp.get_month() == Month.JANUARY:
            cleaned_count = self.world.avatar_manager.cleanup_long_dead_avatars(
                self.world.month_stamp, 
                CONFIG.game.long_dead_cleanup_years
            )
            if cleaned_count > 0:
                # 记录日志，但不产生游戏内事件
                get_logger().logger.info(f"Cleaned up {cleaned_count} long-dead avatars.")

        # 20. 归档与时间推进
        return self._finalize_step(events)

    def _phase_update_calculated_relations(self, living_avatars: list[Avatar]):
        """
        每年 1 月刷新全服角色的二阶关系缓存
        """
        # 仅在 1 月执行
        if self.world.month_stamp.get_month() != Month.JANUARY:
            return

        for avatar in living_avatars:
            update_second_degree_relations(avatar)

    def _finalize_step(self, events: list[Event]) -> list[Event]:
        """
        本轮步进的最终归档：去重、入库、打日志、推进时间。
        """
        # 0. 为启用追踪的 Avatar 记录每月快照
        for avatar in self.world.avatar_manager.avatars.values():
            if avatar.enable_metrics_tracking:
                avatar.record_metrics()

        # 1. 基于 ID 去重（防止同一个事件对象被多次添加）
        unique_events: dict[str, Event] = {}
        for e in events:
            if e.id not in unique_events:
                unique_events[e.id] = e
        final_events = list(unique_events.values())

        # 2. 统一写入事件管理器
        if self.world.event_manager:
            for e in final_events:
                self.world.event_manager.add_event(e)
        
        # 3. 记录日志
        self._phase_log_events(final_events)

        # 4. 时间推进
        self.world.month_stamp = self.world.month_stamp + 1
        
        return final_events
