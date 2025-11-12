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
        # 温养兵器增加较多熟练度（5-10）
        proficiency_gain = random.uniform(5.0, 10.0)
        self.avatar.increase_weapon_proficiency(proficiency_gain)

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

    def finish(self) -> list[Event]:
        weapon_name = self.avatar.weapon.name if self.avatar.weapon else "兵器"
        proficiency = self.avatar.weapon_proficiency
        return [
            Event(
                self.world.month_stamp,
                f"{self.avatar.name} 完成温养{weapon_name}，熟练度提升至{proficiency:.1f}%",
                related_avatars=[self.avatar.id]
            )
        ]

