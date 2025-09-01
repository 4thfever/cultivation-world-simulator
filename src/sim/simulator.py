import random

from src.classes.calendar import Month, Year, MonthStamp
from src.classes.avatar import Avatar, get_new_avatar_from_ordinary, Gender
from src.classes.age import Age
from src.classes.world import World
from src.classes.event import Event, is_null_event
from src.utils.names import get_random_name

class Simulator:
    def __init__(self, world: World):
        self.avatars = {} # dict of str -> Avatar
        self.world = world
        self.brith_rate = 0 # 0表示不出生新角色

    def step(self):
        """
        前进一步（每步模拟是一个月时间）
        结算这个时间内的所有情况。
        角色行为、世界变化、重大事件、etc。
        先结算多个角色间互相交互的事件。
        再去结算单个角色的事件。
        """
        events = [] # list of Event
        death_avatar_ids = [] # list of str

        # 结算角色行为
        for avatar_id, avatar in self.avatars.items():
            event = avatar.act()
            if not is_null_event(event):
                events.append(event)
            if avatar.death_by_old_age():
                death_avatar_ids.append(avatar_id)
                event = Event(self.world.month_stamp, f"{avatar.name} 老死了，时年{avatar.age.get_age()}岁")
                events.append(event)
            avatar.update_age(self.world.month_stamp)
        
        # 删除死亡的角色
        for avatar_id in death_avatar_ids:
            self.avatars.pop(avatar_id)

        # 新角色
        if random.random() < self.brith_rate:
            age = random.randint(16, 60)
            gender = random.choice(list(Gender))
            name = get_random_name(gender)
            new_avatar = get_new_avatar_from_ordinary(self.world, self.world.month_stamp, name, Age(age))
            self.avatars[new_avatar.id] = new_avatar
            event = Event(self.world.month_stamp, f"{new_avatar.name}晋升为修士了。")
            events.append(event)

        # 最后结算年月
        self.world.month_stamp = self.world.month_stamp + 1

        return events
