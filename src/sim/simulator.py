import random
import asyncio

from src.classes.calendar import Month, Year, MonthStamp
from src.classes.avatar import Avatar, Gender
from src.sim.new_avatar import create_random_mortal
from src.classes.age import Age
from src.classes.cultivation import Realm
from src.classes.world import World
from src.classes.event import Event, is_null_event
from src.classes.ai import llm_ai
from src.classes.name import get_random_name
from src.utils.config import CONFIG
from src.run.log import get_logger
from src.classes.fortune import try_trigger_fortune
from src.classes.celestial_phenomenon import get_random_celestial_phenomenon
from src.classes.long_term_objective import process_avatar_long_term_objective
from src.classes.death import handle_death
from src.classes.death_reason import DeathReason

class Simulator:
    def __init__(self, world: World):
        self.world = world
        self.birth_rate = CONFIG.game.npc_birth_rate_per_month  # 从配置文件读取NPC每月出生率

    def _phase_update_perception_and_knowledge(self):
        """
        感知更新阶段：
        1. 基于感知范围更新 known_regions
        2. 自动占据无主洞府（如果自己没有洞府）
        """
        from src.classes.observe import get_avatar_observation_radius
        from src.classes.region import CultivateRegion

        # 1. 缓存当前有洞府的角色ID
        avatars_with_home = set()
        # 注意：这里我们只关心 CultivateRegion 的 host
        # map.cultivate_regions 可能需要确保被正确初始化，如果没有，可以回退到遍历所有 regions
        # 为了稳妥，遍历所有 Region 筛选
        cultivate_regions = [
            r for r in self.world.map.regions.values() 
            if isinstance(r, CultivateRegion)
        ]
        
        for r in cultivate_regions:
            if r.host_avatar:
                avatars_with_home.add(r.host_avatar.id)

        # 2. 遍历所有存活角色
        for avatar in self.world.avatar_manager.get_living_avatars():
            # 计算感知半径（曼哈顿距离）
            radius = get_avatar_observation_radius(avatar)
            
            # 扫描范围内的坐标
            # 优化：只扫描半径内的坐标可能比遍历所有region快，也可能慢，取决于地图大小和半径
            # 地图可能很大，半径通常很小（<10），所以基于坐标扫描更优
            
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
                            region.host_avatar = avatar
                            avatars_with_home.add(avatar.id)
                            # 记录事件
                            event = Event(
                                self.world.month_stamp,
                                f"{avatar.name} 路过 {region.name}，发现无主，将其占据。",
                                related_avatars=[avatar.id]
                            )
                            avatar.add_event(event)
                            
    async def _phase_decide_actions(self):
        """
        决策阶段：仅对需要新计划的角色调用 AI（当前无动作且无计划），
        将 AI 的决策结果加载为角色的计划链。
        """
        avatars_to_decide = []
        for avatar in self.world.avatar_manager.get_living_avatars():
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

    def _phase_commit_next_plans(self):
        """
        提交阶段：为空闲角色提交计划中的下一个可执行动作，返回开始事件集合。
        """
        events = []
        for avatar in self.world.avatar_manager.get_living_avatars():
            if avatar.current_action is None:
                start_event = avatar.commit_next_plan()
                if start_event is not None and not is_null_event(start_event):
                    events.append(start_event)
        return events

    async def _phase_execute_actions(self):
        """
        执行阶段：推进当前动作，支持同月链式抢占即时结算，返回期间产生的事件。
        """
        events = []
        MAX_LOCAL_ROUNDS = 3
        for _ in range(MAX_LOCAL_ROUNDS):
            new_action_happened = False
            for avatar in self.world.avatar_manager.get_living_avatars():
                # 本轮执行前若标记为新设，则清理，执行后由 Avatar 再统一清除
                if getattr(avatar, "_new_action_set_this_step", False):
                    new_action_happened = True
                new_events = await avatar.tick_action()
                if new_events:
                    events.extend(new_events)
                # 若在本次执行后产生了新的动作（被别人抢占设立），则标志位会在 commit_next_plan 时被置 True
                if getattr(avatar, "_new_action_set_this_step", False):
                    new_action_happened = True
            # 若本轮未检测到新动作产生，则结束本地循环
            if not new_action_happened:
                break
        return events

    def _phase_resolve_death(self):
        """
        结算死亡：
        - 战斗死亡已在 Action 中结算
        - 此时剩下的 avatars 都是存活的，只需检查非战斗因素（如老死、被动掉血）
        """
        events = []
        for avatar in self.world.avatar_manager.get_living_avatars():
            is_dead = False
            reason_str = ""
            death_reason = DeathReason.UNKNOWN
            
            # 优先判定重伤（可能是被动效果导致）
            if avatar.hp.cur <= 0: # 注意：这里应该是 avatar.hp.cur 或者 avatar.hp <= 0 取决于 HP 类的实现，原代码是 avatar.hp <= 0
                is_dead = True
                reason_str = f"{avatar.name} 因重伤不治身亡"
                death_reason = DeathReason.SERIOUS_INJURY
            # 其次判定寿元
            elif avatar.death_by_old_age():
                is_dead = True
                reason_str = f"{avatar.name} 老死了，时年{avatar.age.get_age()}岁"
                death_reason = DeathReason.OLD_AGE
                
            if is_dead:
                event = Event(self.world.month_stamp, reason_str, related_avatars=[avatar.id])
                events.append(event)
                handle_death(self.world, avatar, death_reason)
                
        return events

    def _phase_update_age_and_birth(self):
        """
        更新存活角色年龄，并以一定概率生成新修士，返回期间产生的事件集合。
        """
        events = []
        for avatar in self.world.avatar_manager.get_living_avatars():
            avatar.update_age(self.world.month_stamp)
        if random.random() < self.birth_rate:
            age = random.randint(16, 60)
            gender = random.choice(list(Gender))
            name = get_random_name(gender)
            # create_random_mortal 内部会获取 existing_avatars，需要确保它处理活人
            new_avatar = create_random_mortal(self.world, self.world.month_stamp, name, Age(age, Realm.Qi_Refinement))
            self.world.avatar_manager.avatars[new_avatar.id] = new_avatar
            event = Event(self.world.month_stamp, f"{new_avatar.name}晋升为修士了。", related_avatars=[new_avatar.id])
            events.append(event)
        return events

    async def _phase_passive_effects(self):
        """
        被动结算阶段：
        - 更新时间效果（如HP回复）
        - 触发奇遇（非动作）
        """
        events = []
        living_avatars = self.world.avatar_manager.get_living_avatars()
        for avatar in living_avatars:
            avatar.update_time_effect()
        
        # 使用 gather 并行触发奇遇
        tasks = [try_trigger_fortune(avatar) for avatar in living_avatars]
        results = await asyncio.gather(*tasks)
        for res in results:
            if res:
                events.extend(res)
                
        return events
    
    async def _phase_nickname_generation(self):
        """
        绰号生成阶段
        """
        from src.classes.nickname import process_avatar_nickname
        
        # 并发执行
        living_avatars = self.world.avatar_manager.get_living_avatars()
        tasks = [process_avatar_nickname(avatar) for avatar in living_avatars]
        results = await asyncio.gather(*tasks)
        
        events = [e for e in results if e]
        return events
    
    async def _phase_long_term_objective_thinking(self):
        """
        长期目标思考阶段
        检查角色是否需要生成/更新长期目标
        """
        # 并发执行
        living_avatars = self.world.avatar_manager.get_living_avatars()
        tasks = [process_avatar_long_term_objective(avatar) for avatar in living_avatars]
        results = await asyncio.gather(*tasks)
        
        events = [e for e in results if e]
        return events
    
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
                    desc = f"世界初开，天降异象！{new_phenomenon.name}：{new_phenomenon.desc}。"
                else:
                    desc = f"{old_phenomenon.name}消散，天地异象再现！{new_phenomenon.name}：{new_phenomenon.desc}。"
                
                event = Event(
                    self.world.month_stamp,
                    desc,
                    related_avatars=None
                )
                events.append(event)
        
        return events

    def _phase_log_events(self, events):
        """
        将事件写入日志。
        """
        logger = get_logger().logger
        for event in events:
            logger.info("EVENT: %s", str(event))


    async def step(self):
        """
        前进一步（每步模拟是一个月时间）
        结算这个时间内的所有情况。
        角色行为、世界变化、重大事件、etc。
        先结算多个角色间互相交互的事件。
        再去结算单个角色的事件。
        """
        events = [] # list of Event

        # 0. 感知与认知更新阶段（包括自动占据洞府）
        #    在思考和决策之前，先让角色感知世界
        self._phase_update_perception_and_knowledge()

        # 0.5 长期目标思考阶段（在决策之前）
        events.extend(await self._phase_long_term_objective_thinking())

        # 1. 决策阶段
        await self._phase_decide_actions()

        # 2. 提交阶段
        events.extend(self._phase_commit_next_plans())

        # 3. 执行阶段
        events.extend(await self._phase_execute_actions())

        # 4. 结算死亡
        events.extend(self._phase_resolve_death())

        # 5. 年龄与新生
        events.extend(self._phase_update_age_and_birth())

        # 6. 被动结算（时间效果+奇遇）
        events.extend(await self._phase_passive_effects())

        # 7. 绰号生成
        events.extend(await self._phase_nickname_generation())

        # 8. 更新天地灵机
        events.extend(self._phase_update_celestial_phenomenon())

        # 9. 日志
        # 统一写入事件管理器
        if hasattr(self.world, "event_manager") and self.world.event_manager is not None:
            for e in events:
                self.world.event_manager.add_event(e)
        self._phase_log_events(events)

        # 9. 时间推进
        self.world.month_stamp = self.world.month_stamp + 1


        return events
