from src.classes.calendar import Month, Year, next_month

class Simulator:
    def __init__(self):
        self.avatars = [] # list[Avatar]
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
        # 结算角色行为
        for avatar in self.avatars:
            avatar.act()

        # 最后结算年月
        self.month, self.year = next_month(self.month, self.year)
