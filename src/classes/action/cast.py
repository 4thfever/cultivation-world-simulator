from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING, List

from src.classes.action import TimedAction
from src.classes.cultivation import Realm
from src.classes.event import Event
from src.classes.material import Material
from src.classes.weapon import get_random_weapon_by_realm
from src.classes.auxiliary import get_random_auxiliary_by_realm
from src.classes.single_choice import handle_item_exchange
from src.utils.resolution import resolve_query

if TYPE_CHECKING:
    from src.classes.avatar import Avatar

class Cast(TimedAction):
    """
    铸造动作：消耗同阶材料，尝试打造同阶宝物（兵器或辅助装备）。
    持续时间：3个月
    """
    ACTION_NAME = "铸造"
    EMOJI = "🔥"
    DESC = "消耗材料尝试铸造法宝"

    COST = 5
    SUCCESS_RATES = {
        Realm.Qi_Refinement: 0.5,
        Realm.Foundation_Establishment: 0.4,
        Realm.Core_Formation: 0.25,
        Realm.Nascent_Soul: 0.1,
    }

    DOABLES_REQUIREMENTS = f"拥有{COST}个同境界材料"
    PARAMS = {"target_realm": "目标境界名称（'练气'、'筑基'、'金丹'、'元婴'）"}
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
            return False, "未指定目标境界"
        
        res = resolve_query(target_realm, expected_types=[Realm])
        if not res.is_valid:
            return False, f"无效的境界: {target_realm}"
            
        realm = res.obj

        cost = self._get_cost()
        count = self._count_materials(realm)
        
        if count < cost:
            return False, f"材料不足，需要 {cost} 个{target_realm}阶材料，当前拥有 {count} 个"
            
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

        realm_val = self.target_realm.value if self.target_realm else target_realm
        return Event(
            self.world.month_stamp, 
            f"{self.avatar.name} 开始尝试铸造{realm_val}阶法宝。", 
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
            fail_event = Event(
                self.world.month_stamp,
                f"{self.avatar.name} 铸造{self.target_realm.value}阶法宝失败，所有材料化为灰烬。",
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
            item_label = "兵器"
        else:
            new_item = get_random_auxiliary_by_realm(self.target_realm)
            item_type = "auxiliary"
            item_label = "辅助装备"
            
        # 4. 决策：保留还是卖出
        base_desc = f"铸造成功！获得了{self.target_realm.value}{item_label}『{new_item.name}』。"
        
        # 事件1：铸造成功
        events.append(Event(
            self.world.month_stamp,
            f"{self.avatar.name} 成功铸造{self.target_realm.value}{item_label}『{new_item.name}』。",
            related_avatars=[self.avatar.id],
            is_major=True
        ))

        _, result_text = await handle_item_exchange(
            avatar=self.avatar, 
            new_item=new_item,
            item_type=item_type,
            context_intro=base_desc,
            can_sell_new=True
        )

        # 事件2：处置结果
        events.append(Event(
            self.world.month_stamp,
            result_text,
            related_avatars=[self.avatar.id],
            is_major=True
        ))
        
        return events
