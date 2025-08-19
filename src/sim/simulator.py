

class Simulator:
    def __init__(self):
        self.avatars = [] # list[Avatar]

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