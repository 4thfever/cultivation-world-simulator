from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.region import NormalRegion
from src.classes.spirit_animal import SpiritAnimal
from src.classes.cultivation import Realm

if TYPE_CHECKING:
    from src.classes.animal import Animal


class Catch(TimedAction):
    """
    御兽：仅百兽宗弟子可用。
    条件：
    - 当前处于普通区域，且该区域有动物分布
    - 目标动物境界 <= Avatar 境界
    结果：
    - 按动物境界映射成功率尝试捕捉，成功则成为灵兽（覆盖旧灵兽）。
    """

    COMMENT = "尝试驯服一只灵兽，成为自身灵兽。只能有一只灵兽，但是可以高级替换低级。"
    DOABLES_REQUIREMENTS = "仅百兽宗；在有动物的普通区域；目标动物境界不高于角色"
    PARAMS = {}

    duration_months = 4

    def _calc_success_rate_by_realm(self, animal_realm: Realm) -> float:
        mapping: dict[Realm, float] = {
            Realm.Qi_Refinement: 0.8,
            Realm.Foundation_Establishment: 0.6,
            Realm.Core_Formation: 0.4,
            Realm.Nascent_Soul: 0.2,
        }
        return mapping.get(animal_realm, 0.1)

    def _execute(self) -> None:
        region = self.avatar.tile.region
        animals = region.animals
        if not animals:
            return
        target = random.choice(animals)
        base = self._calc_success_rate_by_realm(target.realm)
        extra = float(self.avatar.effects.get("extra_catch_success_rate", 0) or 0)
        rate = max(0.0, min(1.0, base + extra))
        if random.random() < rate:
            # 覆盖为新的灵兽
            self.avatar.spirit_animal = SpiritAnimal(name=target.name, realm=target.realm)

    def can_start(self) -> tuple[bool, str]:
        # 仅百兽宗
        sect = getattr(self.avatar, "sect", None)
        if sect is None or getattr(sect, "name", "") != "百兽宗":
            return False, "仅百兽宗弟子可用"
        region = self.avatar.tile.region
        if not isinstance(region, NormalRegion):
            return False, "当前不在普通区域"
        animals = region.animals
        if len(animals) == 0:
            return False, "当前区域没有动物"
        # 动物境界是否可御
        available_animals = [animal for animal in animals if self.avatar.cultivation_progress.realm >= animal.realm]
        if len(available_animals) == 0:
            return False, "当前区域的动物境界于角色境界"
        return True, ""

    def start(self) -> Event:
        region = self.avatar.tile.region
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {region.name} 尝试御兽")

    def finish(self) -> list[Event]:
        return []


