import random

from src.classes.calendar import Month, Year, MonthStamp
from src.classes.avatar import Avatar, get_new_avatar_from_ordinary, Gender
from src.classes.age import Age
from src.classes.world import World
from src.classes.event import Event, is_null_event
from src.classes.ai import llm_ai, rule_ai
from src.utils.names import get_random_name
from src.utils.config import CONFIG

class Simulator:
    def __init__(self, world: World):
        self.world = world
        self.birth_rate = CONFIG.game.npc_birth_rate_per_month  # 从配置文件读取NPC每月出生率

    async def step(self):
        """
        前进一步（每步模拟是一个月时间）
        结算这个时间内的所有情况。
        角色行为、世界变化、重大事件、etc。
        先结算多个角色间互相交互的事件。
        再去结算单个角色的事件。
        """
        events = [] # list of Event
        death_avatar_ids = [] # list of str

        # 决定动作行为
        avatars_to_decide = []
        for avatar in list(self.world.avatar_manager.avatars.values()):
            if avatar.cur_action_pair is None:
                # 若有排队动作但当前不可执行：丢弃之后的所有动作
                if avatar.has_next_actions():
                    if not avatar.is_next_action_doable():
                        avatar.next_actions.clear()
                        avatars_to_decide.append(avatar)
                    else:
                        event = avatar.pop_next_action_and_set_current()
                        if event is not None and not is_null_event(event):
                            events.append(event)
                else:
                    avatars_to_decide.append(avatar)
        if CONFIG.ai.mode == "llm":
            ai = llm_ai
        else:
            ai = rule_ai
        if avatars_to_decide:   
            decide_results = await ai.decide(self.world, avatars_to_decide)
            for avatar, result in decide_results.items():
                action_name_params_pairs, avatar_thinking, objective, event = result
                avatar.load_decide_result_chain(action_name_params_pairs, avatar_thinking, objective)
                if not is_null_event(event):
                    events.append(event)
        
        # 结算角色行为
        for avatar_id, avatar in self.world.avatar_manager.avatars.items():
            new_events = await avatar.act()
            if new_events:
                events.extend(new_events)
            if avatar.death_by_old_age():
                death_avatar_ids.append(avatar_id)
                event = Event(self.world.month_stamp, f"{avatar.name} 老死了，时年{avatar.age.get_age()}岁")
                events.append(event)
            avatar.update_age(self.world.month_stamp)
        
        # 删除死亡的角色
        for avatar_id in death_avatar_ids:
            self.world.avatar_manager.avatars.pop(avatar_id)

        # 新角色
        if random.random() < self.birth_rate:
            age = random.randint(16, 60)
            gender = random.choice(list(Gender))
            name = get_random_name(gender)
            new_avatar = get_new_avatar_from_ordinary(self.world, self.world.month_stamp, name, Age(age))
            self.world.avatar_manager.avatars[new_avatar.id] = new_avatar
            event = Event(self.world.month_stamp, f"{new_avatar.name}晋升为修士了。")
            events.append(event)

        # 最后结算年月
        self.world.month_stamp = self.world.month_stamp + 1

        return events
