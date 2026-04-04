from __future__ import annotations

import random
from typing import TYPE_CHECKING

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.story_event_service import StoryEventKind, StoryEventService
from src.classes.environment.region import NormalRegion
from src.classes.spirit_animal import SpiritAnimal
from src.systems.cultivation import Realm

if TYPE_CHECKING:
    from src.classes.animal import Animal


BEAST_SECT_ID = 2
BEAST_SECT_NAME_ID = "SECT_2_NAME"


def _is_beast_taming_sect(sect) -> bool:
    if sect is None:
        return False
    if int(getattr(sect, "id", 0) or 0) == BEAST_SECT_ID:
        return True
    if str(getattr(sect, "name_id", "") or "") == BEAST_SECT_NAME_ID:
        return True
    # Legacy fallback for old runtime objects or saves.
    return str(getattr(sect, "name", "") or "") == "百兽宗"


class Catch(TimedAction):
    """
    御兽：仅百兽宗弟子可用。
    条件：
    - 当前处于普通区域，且该区域有动物分布
    - 目标动物境界 <= Avatar 境界
    结果：
    - 按动物境界映射成功率尝试捕捉，成功则成为灵兽（覆盖旧灵兽）。
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "catch_action_name"
    DESC_ID = "catch_description"
    REQUIREMENTS_ID = "catch_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🕸️"
    PARAMS = {}

    duration_months = 4

    def __init__(self, avatar, world):
        super().__init__(avatar, world)
        self._caught_result: tuple[str, Realm] | None = None

    def _calc_success_rate_by_realm(self, animal_realm: Realm) -> float:
        mapping: dict[Realm, float] = {
            Realm.Qi_Refinement: 0.8,
            Realm.Foundation_Establishment: 0.6,
            Realm.Core_Formation: 0.4,
            Realm.Nascent_Soul: 0.2,
        }
        return mapping.get(animal_realm, 0.1)

    def can_possibly_start(self) -> bool:
        if not _is_beast_taming_sect(self.avatar.sect):
            return False
        return True

    def _execute(self) -> None:
        region = self.avatar.tile.region
        animals = region.animals
        if not animals:
            return
        # 若已成功捕捉过一次，本次动作内不再重复尝试
        if self._caught_result is not None:
            return
        target = random.choice(animals)
        base = self._calc_success_rate_by_realm(target.realm)
        extra = float(self.avatar.effects.get("extra_catch_success_rate", 0) or 0)
        rate = max(0.0, min(1.0, base + extra))
        if random.random() < rate:
            # 覆盖为新的灵兽
            self.avatar.spirit_animal = SpiritAnimal(name=target.name, realm=target.realm)
            # 记录结果供 finish 生成事件
            self._caught_result = (str(target.name), target.realm, "success")
        else:
            self._caught_result = (None, None, "fail")

    def can_start(self) -> tuple[bool, str]:
        region = self.avatar.tile.region
        if not isinstance(region, NormalRegion):
            return False, t("Not currently in normal area")
        animals = region.animals
        if len(animals) == 0:
            return False, t("Current area {region} has no animals", region=region.name)
        # 动物境界是否可御
        available_animals = [animal for animal in animals if self.avatar.cultivation_progress.realm >= animal.realm]
        if len(available_animals) == 0:
            return False, t("Animal realms in current area exceed character realm")
        return True, ""

    def start(self) -> Event:
        # 清理状态
        self._caught_result = None
        region = self.avatar.tile.region
        content = t("{avatar} attempts to tame spirit beast at {location}",
                   avatar=self.avatar.name, location=self.avatar.tile.location_name)
        self._start_event_content = content
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    async def finish(self) -> list[Event]:
        res = self._caught_result
        if not (isinstance(res, tuple) and len(res) == 3):
            return []
        target_name, target_realm, result = res[0], res[1], res[2]
        if result == "fail":
            content = t("{avatar} failed to tame spirit beast", avatar=self.avatar.name)
            return [Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])]
        else:
            realm_label = str(target_realm)
            content = t("{avatar} successfully tamed spirit beast, {realm} realm {beast} became their spirit beast",
                       avatar=self.avatar.name, realm=realm_label, beast=target_name)
            result_event = Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])
            story_event = await StoryEventService.maybe_create_story(
                kind=StoryEventKind.CRAFTING,
                month_stamp=self.world.month_stamp,
                start_text=getattr(self, "_start_event_content", ""),
                result_text=content,
                actors=[self.avatar],
                related_avatar_ids=[self.avatar.id],
                allow_relation_changes=False,
            )
            events = [result_event]
            if story_event is not None:
                events.append(story_event)
            return events


