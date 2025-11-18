from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event
import random


class NurtureWeapon(TimedAction):
    """
    温养兵器：花时间温养兵器，可以较多增加熟练度
    """

    COMMENT = "温养兵器，增加兵器熟练度"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {}

    duration_months = 3

    def _execute(self) -> None:
        from src.classes.equipment_grade import EquipmentGrade
        from src.classes.weapon import get_treasure_weapon
        
        # 温养兵器增加较多熟练度（5-10）
        proficiency_gain = random.uniform(5.0, 10.0)
        self.avatar.increase_weapon_proficiency(proficiency_gain)
        
        # 如果是普通兵器，有概率升级为宝物
        if self.avatar.weapon and self.avatar.weapon.grade == EquipmentGrade.COMMON:
            # 基础5%概率 + 来自effects的额外概率
            base_upgrade_chance = 0.05
            extra_chance_raw = self.avatar.effects.get("extra_weapon_upgrade_chance", 0.0)
            extra_chance = max(0.0, min(1.0, float(extra_chance_raw or 0.0)))
            total_chance = min(1.0, base_upgrade_chance + extra_chance)
            
            if random.random() < total_chance:
                treasure_weapon = get_treasure_weapon(self.avatar.weapon.weapon_type)
                if treasure_weapon:
                    import copy
                    old_weapon_name = self.avatar.weapon.name
                    old_proficiency = self.avatar.weapon_proficiency
                    # 深拷贝宝物兵器并更换（会重新计算长期效果）
                    new_weapon = copy.deepcopy(treasure_weapon)
                    self.avatar.change_weapon(new_weapon)
                    # 恢复熟练度（change_weapon 会归零，需要手动恢复）
                    self.avatar.weapon_proficiency = old_proficiency
                    # 记录升华事件
                    from src.classes.event import Event
                    self.avatar.add_event(Event(
                        self.world.month_stamp,
                        f"{self.avatar.name} 温养{old_weapon_name}时，兵器灵性大增，升华为{treasure_weapon.name}！",
                        related_avatars=[self.avatar.id]
                    ))

    def can_start(self) -> tuple[bool, str]:
        # 任何时候都可以温养兵器
        return (True, "")

    def start(self) -> Event:
        weapon_name = self.avatar.weapon.name if self.avatar.weapon else "兵器"
        return Event(
            self.world.month_stamp,
            f"{self.avatar.name} 开始温养{weapon_name}",
            related_avatars=[self.avatar.id]
        )

    async def finish(self) -> list[Event]:
        weapon_name = self.avatar.weapon.name if self.avatar.weapon else "兵器"
        proficiency = self.avatar.weapon_proficiency
        # 注意：升华事件已经在_execute中添加，这里只添加完成事件
        return [
            Event(
                self.world.month_stamp,
                f"{self.avatar.name} 完成温养{weapon_name}，熟练度提升至{proficiency:.1f}%",
                related_avatars=[self.avatar.id]
            )
        ]

