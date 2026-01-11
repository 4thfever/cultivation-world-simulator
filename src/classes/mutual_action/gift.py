from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from .mutual_action import MutualAction
from src.classes.event import Event
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.avatar import Avatar
    from src.classes.action_runtime import ActionResult
    from src.classes.world import World


class Gift(MutualAction):
    """赠送：向目标赠送灵石或物品。

    - 支持赠送灵石、素材、装备。
    - 目标在交互范围内。
    - 目标可以感知具体赠送的物品并选择 接受 或 拒绝。
    - 若接受：物品从发起者转移给目标（装备会自动穿戴并顶替旧装备）。
    - 非灵石物品一次只能赠送1个。
    """

    ACTION_NAME = "赠送"
    EMOJI = "🎁"
    DESC = "向对方赠送灵石或物品"
    DOABLES_REQUIREMENTS = "发起者持有该物品；目标在交互范围内"
    
    PARAMS = {
        "target_avatar": "Avatar",
        "item_name": "str", 
        "amount": "int"
    }
    
    FEEDBACK_ACTIONS = ["Accept", "Reject"]

    def __init__(self, avatar: "Avatar", world: "World"):
        super().__init__(avatar, world)
        # 暂存当前赠送上下文，用于 step 跨帧和 build_prompt_infos
        self._current_gift_context: dict[str, Any] = {}
        self._gift_success = False

    def _get_template_path(self) -> Path:
        return CONFIG.paths.templates / "mutual_action.txt"

    def _resolve_gift(self, item_name: str, amount: int) -> tuple[Any, str, int]:
        """
        解析赠送意图，返回 (物品对象/None, 显示名称, 实际数量)。
        物品对象为 None 代表是灵石。
        """
        # 1. 灵石
        if item_name == "灵石" or not item_name:
            return None, "灵石", max(1, amount)
        
        # 非灵石强制数量为 1
        forced_amount = 1
        
        # 2. 检查装备 (Weapon/Auxiliary)
        if self.avatar.weapon and self.avatar.weapon.name == item_name:
            return self.avatar.weapon, self.avatar.weapon.name, forced_amount
        if self.avatar.auxiliary and self.avatar.auxiliary.name == item_name:
            return self.avatar.auxiliary, self.avatar.auxiliary.name, forced_amount
            
        # 3. 检查背包素材 (Materials)
        for mat, qty in self.avatar.materials.items():
            if mat.name == item_name:
                return mat, mat.name, forced_amount
                
        # 未找到
        return None, "", 0

    def _get_gift_description(self) -> str:
        name = self._current_gift_context.get("name", "未知物品")
        amount = self._current_gift_context.get("amount", 0)
        obj = self._current_gift_context.get("obj")
        
        from src.classes.weapon import Weapon
        from src.classes.auxiliary import Auxiliary
        
        if obj is None: # 灵石
            return f"{amount} 灵石"
        elif isinstance(obj, (Weapon, Auxiliary)):
            return f"[{name}]"
        else:
            return f"{amount} {name}"

    def step(self, target_avatar: "Avatar|str", item_name: str = "灵石", amount: int = 100) -> ActionResult:
        """
        重写 step 以接收额外参数。
        将参数存入 self，然后调用父类 step 执行通用逻辑（LLM交互）。
        """
        # 每一帧都会传入参数，更新上下文
        obj, name, real_amount = self._resolve_gift(item_name, amount)
        
        self._current_gift_context = {
            "obj": obj,
            "name": name,
            "amount": real_amount,
            "original_item_name": item_name
        }
        
        # 调用父类 step，父类会调用 _build_prompt_infos -> _can_start 等
        return super().step(target_avatar)

    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """检查赠送条件：物品是否存在且足够"""
        obj = self._current_gift_context.get("obj")
        name = self._current_gift_context.get("name")
        amount = self._current_gift_context.get("amount", 0)
        original_name = self._current_gift_context.get("original_item_name")
        
        # 如果 name 为空，说明 resolve 失败
        if not name:
             if original_name and original_name != "灵石":
                 return False, f"未找到物品：{original_name}"
             # 如果是灵石但没解析出来（不应该发生，除非amount有问题，但max(1)了），或者是默认情况

        # 1. 灵石
        if obj is None and name == "灵石":
            if self.avatar.magic_stone < amount:
                return False, f"灵石不足（当前：{self.avatar.magic_stone}，需要：{amount}）"
            return True, ""
            
        # 2. 物品 (装备/素材)
        from src.classes.weapon import Weapon
        from src.classes.auxiliary import Auxiliary
        
        if isinstance(obj, (Weapon, Auxiliary)):
            if self.avatar.weapon is not obj and self.avatar.auxiliary is not obj:
                 return False, f"未装备该物品：{name}"
        elif obj is not None:
            # Material
            qty = self.avatar.materials.get(obj, 0)
            if qty < amount:
                 return False, f"物品不足：{name}"
        else:
             return False, f"未找到物品：{original_name}"

        # 检查交互范围 (父类 MutualAction.can_start 已经检查了，但这里是 _can_start 额外检查)
        from src.classes.observe import is_within_observation
        if not is_within_observation(self.avatar, target):
            return False, "目标不在交互范围内"
            
        return True, ""

    def _build_prompt_infos(self, target_avatar: "Avatar") -> dict:
        """
        重写：构建传给 LLM 的 prompt 信息。
        """
        infos = super()._build_prompt_infos(target_avatar)
        
        gift_desc = self._get_gift_description()
        infos["action_info"] = f"向你赠送 {gift_desc}"
        
        return infos

    def start(self, target_avatar: "Avatar|str", item_name: str = "灵石", amount: int = 100) -> Event:
        # start 也会接收参数，同样需要设置上下文
        obj, name, real_amount = self._resolve_gift(item_name, amount)
        self._current_gift_context = {
            "obj": obj, 
            "name": name, 
            "amount": real_amount, 
            "original_item_name": item_name
        }
        
        target = self._get_target_avatar(target_avatar)
        target_name = target.name if target is not None else str(target_avatar)
        
        gift_desc = self._get_gift_description()
        
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
            
        event = Event(
            self.world.month_stamp,
            f"{self.avatar.name} 试图向 {target_name} 赠送 {gift_desc}",
            related_avatars=rel_ids
        )
        
        # 写入历史
        self.avatar.add_event(event, to_sidebar=False)
        if target is not None:
            target.add_event(event, to_sidebar=False)
            
        self._gift_success = False
        return event

    def _settle_feedback(self, target_avatar: "Avatar", feedback_name: str) -> None:
        fb = str(feedback_name).strip()
        if fb == "Accept":
            self._apply_gift(target_avatar)
            self._gift_success = True
        else:
            self._gift_success = False

    def _apply_gift(self, target: "Avatar") -> None:
        """执行物品转移"""
        obj = self._current_gift_context.get("obj")
        amount = self._current_gift_context.get("amount", 0)
        
        if obj is None:
            # 灵石
            if self.avatar.magic_stone >= amount:
                self.avatar.magic_stone -= amount
                target.magic_stone += amount
        else:
            from src.classes.weapon import Weapon
            from src.classes.auxiliary import Auxiliary
            
            if isinstance(obj, (Weapon, Auxiliary)):
                # 装备：发起者卸下 -> 目标装备（旧装备自动处理）
                if self.avatar.weapon is obj:
                    self.avatar.weapon = None
                elif self.avatar.auxiliary is obj:
                    self.avatar.auxiliary = None
                else:
                    return # 已经不在身上了
                
                # 目标装备
                new_equip = obj 
                
                old_item = None
                if isinstance(new_equip, Weapon):
                    old_item = target.weapon
                    target.weapon = new_equip
                else: # Auxiliary
                    old_item = target.auxiliary
                    target.auxiliary = new_equip
                
                # 旧装备简单处理：折价变成灵石加给目标
                if old_item:
                    refund = int(getattr(old_item, "price", 0) * 0.5)
                    if refund > 0:
                        target.magic_stone += refund
                    
            else:
                # 素材：发起者移除 -> 目标添加
                if self.avatar.remove_material(obj, amount):
                    target.add_material(obj, amount)

    async def finish(self, target_avatar: "Avatar|str") -> list[Event]:
        target = self._get_target_avatar(target_avatar)
        events: list[Event] = []
        if target is None:
            return events

        if self._gift_success:
            gift_desc = self._get_gift_description()
            result_text = f"{self.avatar.name} 成功赠送了 {gift_desc} 给 {target.name}"
            
            result_event = Event(
                self.world.month_stamp,
                result_text,
                related_avatars=[self.avatar.id, target.id]
            )
            events.append(result_event)
            
        return events
