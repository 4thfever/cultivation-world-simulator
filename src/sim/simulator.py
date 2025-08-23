from src.classes.calendar import Month, Year, next_month
from src.classes.avatar import Avatar
from src.sim.event import Event

class Simulator:
    def __init__(self):
        self.avatars = {} # dict of int -> Avatar
        self.year = Year(1)
        self.month = Month.JANUARY

    def step(self):
        """
        前进一步（每步模拟是一个月时间）
        结算这个时间内的所有情况。
        角色行为、世界变化、重大事件、etc。
        先结算多个角色间互相交互的事件。
        再去结算单个角色的事件。
        """
        events = [] # list of Event
        death_avatar_ids = [] # list of int

        # 结算角色行为
        for avatar_id, avatar in self.avatars.items():
            avatar.act()
            if avatar.death_by_old_age():
                death_avatar_ids.append(avatar_id)
                event = Event(self.year, self.month, f"{avatar.name} 老死了，时年{avatar.age.get_age()}岁")
                events.append(event)
        
        for avatar_id in death_avatar_ids:
            self.avatars.pop(avatar_id)

        # 最后结算年月
        self.month, self.year = next_month(self.month, self.year)

        return events
