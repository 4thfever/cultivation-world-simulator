from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING, List

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.story_event_service import StoryEventKind, StoryEventService
from src.systems.cultivation import Realm
from src.classes.event import Event
from src.classes.material import Material
from src.classes.items.weapon import get_random_weapon_by_realm
from src.classes.items.auxiliary import get_random_auxiliary_by_realm
from src.systems.single_choice import (
    ItemExchangeKind,
    ItemExchangeRequest,
    RejectMode,
    resolve_item_exchange,
)
from src.utils.resolution import resolve_query

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar

class Cast(TimedAction):
    """
    铸造动作：消耗同阶材料，尝试打造同阶宝物（兵器或辅助装备）。
    持续时间：3个月
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "cast_action_name"
    DESC_ID = "cast_description"
    REQUIREMENTS_ID = "cast_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🔥"
    PARAMS = {"target_realm": "str"}

    COST = 5
    SUCCESS_RATES = {
        Realm.Qi_Refinement: 0.5,
        Realm.Foundation_Establishment: 0.4,
        Realm.Core_Formation: 0.25,
        Realm.Nascent_Soul: 0.1,
    }

    IS_MAJOR = False

    duration_months = 3

    def __init__(self, avatar: Avatar, world):
        super().__init__(avatar, world)
        self.target_realm: Optional[Realm] = None

    def _get_cost(self) -> int:
        return self.COST

    def _count_materials(self, realm: Realm) -> int:
        """
        统计符合条件的材料数量。
        """
        count = 0
        for material, qty in self.avatar.materials.items():
            if material.realm == realm:
                count += qty
        return count

    def can_start(self, target_realm: str) -> tuple[bool, str]:
        if not target_realm:
            return False, t("Target realm not specified")
        
        res = resolve_query(target_realm, expected_types=[Realm])
        if not res.is_valid:
            return False, t("Invalid realm: {realm}", realm=target_realm)
            
        realm = res.obj

        cost = self._get_cost()
        count = self._count_materials(realm)
        
        if count < cost:
            return False, t("Insufficient materials, need {cost} {realm}-tier materials, currently have {count}",
                          cost=cost, realm=target_realm, count=count)
            
        return True, ""

    def start(self, target_realm: str) -> Event:
        res = resolve_query(target_realm, expected_types=[Realm])
        if res.is_valid:
            self.target_realm = res.obj

        cost = self._get_cost()
        
        # 扣除材料逻辑
        to_deduct = cost
        materials_to_modify = []
        
        # 再次遍历寻找材料进行扣除
        for material, qty in self.avatar.materials.items():
            if to_deduct <= 0:
                break
            if material.realm == self.target_realm:
                take = min(qty, to_deduct)
                materials_to_modify.append((material, take))
                to_deduct -= take
                
        for material, take in materials_to_modify:
            self.avatar.remove_material(material, take)

        realm_val = str(self.target_realm) if self.target_realm else target_realm
        content = t("{avatar} begins attempting to cast {realm}-tier treasure",
                   avatar=self.avatar.name, realm=realm_val)
        self._start_event_content = content
        return Event(
            self.world.month_stamp, 
            content, 
            related_avatars=[self.avatar.id]
        )

    def _execute(self) -> None:
        # 持续过程中无特殊逻辑
        pass

    async def finish(self) -> list[Event]:
        if self.target_realm is None:
            return []

        # 1. 计算成功率
        base_rate = self.SUCCESS_RATES.get(self.target_realm, 0.1)
        extra_rate = float(self.avatar.effects.get("extra_cast_success_rate", 0.0))
        success_rate = base_rate + extra_rate
        
        events = []
        
        # 2. 判定结果
        if random.random() > success_rate:
            # 失败
            content = t("{avatar} failed to cast {realm}-tier treasure, all materials turned to ash",
                       avatar=self.avatar.name, realm=str(self.target_realm))
            fail_event = Event(
                self.world.month_stamp,
                content,
                related_avatars=[self.avatar.id],
                is_major=False
            )
            events.append(fail_event)
            return events

        # 3. 成功：生成物品
        # 50% 兵器，50% 辅助装备
        is_weapon = random.random() < 0.5
        new_item = None
        item_type = ""
        item_label = ""
        
        if is_weapon:
            new_item = get_random_weapon_by_realm(self.target_realm)
            item_type = "weapon"
            item_label = t("weapon")
        else:
            new_item = get_random_auxiliary_by_realm(self.target_realm)
            item_type = "auxiliary"
            item_label = t("auxiliary")
            
        # 4. 决策：保留还是卖出
        base_desc = t("Casting succeeded! Obtained {realm} {label} '{item}'",
                     realm=str(self.target_realm), label=item_label, item=new_item.name)
        
        # 事件1：铸造成功
        content = t("{avatar} successfully cast {realm}-tier {label} '{item}'",
                   avatar=self.avatar.name, realm=str(self.target_realm), 
                   label=item_label, item=new_item.name)
        events.append(Event(
            self.world.month_stamp,
            content,
            related_avatars=[self.avatar.id],
            is_major=True
        ))

        outcome = await resolve_item_exchange(
            ItemExchangeRequest(
                avatar=self.avatar,
                new_item=new_item,
                kind=ItemExchangeKind(item_type),
                scene_intro=base_desc,
                reject_mode=RejectMode.SELL_NEW,
                auto_accept_when_empty=False,
            )
        )

        # 事件2：处置结果
        exchange_event = Event(
            self.world.month_stamp,
            outcome.result_text,
            related_avatars=[self.avatar.id],
            is_major=True
        )
        events.append(exchange_event)
        story_event = await StoryEventService.maybe_create_story(
            kind=StoryEventKind.CRAFTING,
            month_stamp=self.world.month_stamp,
            start_text=getattr(self, "_start_event_content", ""),
            result_text=f"{content} {exchange_event.content}",
            actors=[self.avatar],
            related_avatar_ids=[self.avatar.id],
            allow_relation_changes=False,
        )
        if story_event is not None:
            events.append(story_event)
        
        return events
