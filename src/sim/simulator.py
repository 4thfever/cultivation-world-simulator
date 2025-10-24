import random

from src.classes.calendar import Month, Year, MonthStamp
from src.classes.avatar import Avatar, Gender
from src.sim.new_avatar import get_new_avatar_from_mortal
from src.classes.age import Age
from src.classes.cultivation import Realm
from src.classes.world import World
from src.classes.event import Event, is_null_event
from src.classes.ai import llm_ai, rule_ai
from src.utils.names import get_random_name
from src.utils.config import CONFIG
from src.run.log import get_logger
from src.classes.fortune import try_trigger_fortune

class Simulator:
    def __init__(self, world: World):
        self.world = world
        self.birth_rate = CONFIG.game.npc_birth_rate_per_month  # 从配置文件读取NPC每月出生率

    async def _phase_decide_actions(self):
        """
        决策阶段：仅对需要新计划的角色调用 AI（当前无动作且无计划），
        将 AI 的决策结果加载为角色的计划链。
        """
        avatars_to_decide = []
        for avatar in list(self.world.avatar_manager.avatars.values()):
            if avatar.current_action is None and not avatar.has_plans():
                avatars_to_decide.append(avatar)
        if not avatars_to_decide:
            return
        if CONFIG.ai.mode == "llm":
            ai = llm_ai
        else:
            ai = rule_ai
        decide_results = await ai.decide(self.world, avatars_to_decide)
        for avatar, result in decide_results.items():
            action_name_params_pairs, avatar_thinking, objective, _event = result
            # 仅入队计划，不在此处添加开始事件，避免与提交阶段重复
            avatar.load_decide_result_chain(action_name_params_pairs, avatar_thinking, objective)

    def _phase_commit_next_plans(self):
        """
        提交阶段：为空闲角色提交计划中的下一个可执行动作，返回开始事件集合。
        """
        events = []
        for avatar in list(self.world.avatar_manager.avatars.values()):
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
            for avatar_id, avatar in list(self.world.avatar_manager.avatars.items()):
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
        结算战斗等导致的死亡以及寿终正寝，移除死亡角色，返回死亡事件集合。
        """
        events = []
        death_avatar_ids = []
        for avatar_id, avatar in list(self.world.avatar_manager.avatars.items()):
            if avatar.hp <= 0:
                death_avatar_ids.append(avatar_id)
                event = Event(self.world.month_stamp, f"{avatar.name} 因重伤身亡", related_avatars=[avatar.id])
                events.append(event)
            if avatar.death_by_old_age():
                death_avatar_ids.append(avatar_id)
                event = Event(self.world.month_stamp, f"{avatar.name} 老死了，时年{avatar.age.get_age()}岁", related_avatars=[avatar.id])
                events.append(event)
        if death_avatar_ids:
            self.world.avatar_manager.remove_avatars(death_avatar_ids)
        return events

    def _phase_update_age_and_birth(self):
        """
        更新存活角色年龄，并以一定概率生成新修士，返回期间产生的事件集合。
        """
        events = []
        for avatar_id, avatar in self.world.avatar_manager.avatars.items():
            avatar.update_age(self.world.month_stamp)
        if random.random() < self.birth_rate:
            age = random.randint(16, 60)
            gender = random.choice(list(Gender))
            name = get_random_name(gender)
            new_avatar = get_new_avatar_from_mortal(self.world, self.world.month_stamp, name, Age(age, Realm.Qi_Refinement))
            self.world.avatar_manager.avatars[new_avatar.id] = new_avatar
            event = Event(self.world.month_stamp, f"{new_avatar.name}晋升为修士了。", related_avatars=[new_avatar.id])
            events.append(event)
        return events

    def _phase_passive_effects(self):
        """
        被动结算阶段：
        - 更新时间效果（如HP回复）
        - 触发奇遇（非动作）
        """
        events = []
        for avatar in self.world.avatar_manager.avatars.values():
            avatar.update_time_effect()
        for avatar in list(self.world.avatar_manager.avatars.values()):
            events.extend(try_trigger_fortune(avatar))
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
        events.extend(self._phase_passive_effects())

        # 7. 日志
        # 统一写入事件管理器
        if hasattr(self.world, "event_manager") and self.world.event_manager is not None:
            for e in events:
                self.world.event_manager.add_event(e)
        self._phase_log_events(events)

        # 8. 时间推进
        self.world.month_stamp = self.world.month_stamp + 1


        return events
