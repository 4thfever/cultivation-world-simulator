from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING, List

from src.classes.action import TimedAction
from src.classes.cultivation import Realm
from src.classes.event import Event
from src.classes.item import Item
from src.classes.weapon import get_random_weapon_by_realm
from src.classes.auxiliary import get_random_auxiliary_by_realm
from src.classes.single_choice import handle_item_exchange
from src.utils.config import CONFIG

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
    DOABLES_REQUIREMENTS = f"拥有{getattr(CONFIG.action.cast, 'cost', 10)}个同阶材料"
    PARAMS = {"target_realm": "目标境界名称（'练气'、'筑基'、'金丹'、'元婴'）"}
    IS_MAJOR = False

    duration_months = 3

    def __init__(self, avatar: Avatar, world):
        super().__init__(avatar, world)
        self.target_realm: Optional[Realm] = None

    def _get_cost(self) -> int:
        # 从配置读取消耗数量，默认为10
        return getattr(CONFIG.action.cast, "cost", 10)

    def _count_materials(self, realm: Realm) -> int:
        """
        统计符合条件的材料数量。
        注意：仅统计 Item 类的直接实例，不统计 Weapon/Auxiliary 等子类（它们也是 Item，但通常不作为铸造原材料）。
        """
        count = 0
        for item, qty in self.avatar.items.items():
            # 这里使用 type(item) is Item 来严格限制必须是基础材料
            # 如果项目里有其他继承自 Item 的材料类，可能需要放宽这个限制
            if type(item).__name__ == "Item" and item.realm == realm:
                count += qty
        return count

    def can_start(self, target_realm: str = "") -> tuple[bool, str]:
        if not target_realm:
            return False, "未指定目标境界"
        
        try:
            realm = Realm(target_realm)
        except ValueError:
            return False, f"无效的境界: {target_realm}"

        cost = self._get_cost()
        count = self._count_materials(realm)
        
        if count < cost:
            return False, f"材料不足，需要 {cost} 个{target_realm}阶材料，当前拥有 {count} 个"
            
        return True, ""

    def start(self, target_realm: str = "") -> Event:
        self.target_realm = Realm(target_realm)
        cost = self._get_cost()
        
        # 扣除材料逻辑
        to_deduct = cost
        items_to_modify = []
        
        # 再次遍历寻找材料进行扣除
        for item, qty in self.avatar.items.items():
            if to_deduct <= 0:
                break
            if type(item).__name__ == "Item" and item.realm == self.target_realm:
                take = min(qty, to_deduct)
                items_to_modify.append((item, take))
                to_deduct -= take
                
        for item, take in items_to_modify:
            self.avatar.remove_item(item, take)

        return Event(
            self.world.month_stamp, 
            f"{self.avatar.name} 开始尝试铸造{target_realm}阶法宝。", 
            related_avatars=[self.avatar.id]
        )

    def _execute(self) -> None:
        # 持续过程中无特殊逻辑
        pass

    async def finish(self) -> list[Event]:
        if self.target_realm is None:
            return []

        # 1. 计算成功率
        base_rate = float(getattr(CONFIG.action.cast, "base_success_rate", 0.3))
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
