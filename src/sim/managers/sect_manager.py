import math
from typing import TYPE_CHECKING
from src.classes.event import Event

if TYPE_CHECKING:
    from src.classes.core.world import World

class SectManager:
    """
    宗门管理器。
    负责宗门的战力计算、势力范围更新、灵石结算。
    """
    def __init__(self, world: "World"):
        self.world = world

    def update_sects(self) -> list[Event]:
        """
        每年底（或初）结算一次。
        更新总战力，势力半径，并增加灵石，生成事件。
        返回产生的事件列表。
        """
        events = []
        
        # 遍历世界现存的宗门
        for sect in getattr(self.world, "existed_sects", []):
            if not sect.is_active:
                continue
                
            # 直接通过宗门的 members 属性获取存活的成员
            # members 是一个 dict: Avatar ID -> Avatar
            members = []
            for m in sect.members.values():
                if not m.is_dead:
                    members.append(m)
            
            # 计算总战力: log(sum(exp(成员战力)))
            # 为了数值稳定，使用 max trick
            total_strength = 0.0
            if members:
                strengths = [float(getattr(m, "base_battle_strength", 0)) for m in members]
                if strengths:
                    max_str = max(strengths)
                    # 防止 exp 溢出，限制上限
                    sum_exp = sum(math.exp(max(-500.0, min(s - max_str, 500.0))) for s in strengths)
                    total_strength = max_str + math.log(sum_exp)
            
            sect.total_battle_strength = max(0.0, total_strength)
            
            # 计算势力半径
            # 半径 = int(宗门战力) // 10 + 1
            sect.influence_radius = int(sect.total_battle_strength) // 10 + 1
            
            # 计算势力面积
            # 面积 = 2 * R^2 + 2 * R + 1
            r = sect.influence_radius
            area = 2 * (r ** 2) + 2 * r + 1
            
            # 结算灵石
            income = area * 100
            sect.magic_stone += income
            
            import src.i18n
            from src.i18n import t
            content = t(
                "game.sect_update_event",
                sect_name=sect.name,
                strength=int(sect.total_battle_strength),
                radius=sect.influence_radius,
                income=income
            )
            
            # 兼容：如果未找到配置则回退到默认英文字符串形式
            if content == "game.sect_update_event":
                content = f"[{sect.name}] this year's total battle strength reached {int(sect.total_battle_strength)}, territory radius became {sect.influence_radius}, gaining {income} magic stones from the territory."
            
            event = Event(
                month_stamp=self.world.month_stamp,
                content=content,
                related_sects=[sect.id]
            )
            events.append(event)
            
        return events
