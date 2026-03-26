from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.i18n import t
from .mutual_action import InvitationAction
from src.classes.event import Event
from src.classes.relation.relation_delta_service import RelationDeltaService
from src.classes.story_event_service import StoryEventKind, StoryEventService
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.action_runtime import ActionResult
    from src.classes.core.world import World


class Gift(InvitationAction):
    """赠送：向目标赠送灵石或物品。

    - 支持赠送灵石、素材、装备。
    - 目标在交互范围内。
    - 目标可以感知具体赠送的物品并选择 接受 或 拒绝。
    - 若接受：物品从发起者转移给目标（装备会自动穿戴并顶替旧装备）。
    - 非灵石物品一次只能赠送1个。
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "gift_action_name"
    DESC_ID = "gift_description"
    REQUIREMENTS_ID = "gift_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🎁"
    SPIRIT_STONE_KEY = "SPIRIT_STONE"
    
    PARAMS = {
        "target_avatar": "Avatar",
        "item_id": "str", 
        "amount": "int"
    }
    
    RESPONSE_ACTIONS = ["Accept", "Reject"]

    def __init__(self, avatar: "Avatar", world: "World"):
        super().__init__(avatar, world)
        # 暂存当前赠送上下文，用于 step 跨帧和 build_prompt_infos
        self._current_gift_context: dict[str, Any] = {}
        self._gift_success = False

    def _get_template_path(self) -> Path:
        return CONFIG.paths.templates / "mutual_action.txt"

    def _resolve_gift(self, item_id_str: str, amount: int) -> tuple[Any, str, int]:
        """
        解析赠送意图，返回 (物品对象/None, 显示名称, 实际数量)。
        物品对象为 None 代表是灵石。
        """
        # 1. 灵石
        if not item_id_str or str(item_id_str).strip().upper() == self.SPIRIT_STONE_KEY:
            return None, t("spirit stones"), max(1, amount)
        
        # 非灵石强制数量为 1
        forced_amount = 1
        
        # 解析 ID
        try:
            target_id = int(item_id_str)
        except (ValueError, TypeError):
            # ID 必须是数字，否则视为无效
            return None, "", 0
        
        # 2. 检查装备 (Weapon/Auxiliary)
        if self.avatar.weapon and self.avatar.weapon.id == target_id:
            return self.avatar.weapon, self.avatar.weapon.name, forced_amount
        if self.avatar.auxiliary and self.avatar.auxiliary.id == target_id:
            return self.avatar.auxiliary, self.avatar.auxiliary.name, forced_amount
            
        # 3. 检查背包素材 (Materials)
        for mat, qty in self.avatar.materials.items():
            if mat.id == target_id:
                return mat, mat.name, forced_amount
                
        # 未找到
        return None, "", 0

    def _get_gift_description(self) -> str:
        name = self._current_gift_context.get("name", "未知物品")
        amount = self._current_gift_context.get("amount", 0)
        obj = self._current_gift_context.get("obj")
        
        from src.classes.items.weapon import Weapon
        from src.classes.items.auxiliary import Auxiliary
        
        if obj is None: # 灵石
            return f"{amount} 灵石"
        elif isinstance(obj, (Weapon, Auxiliary)):
            return f"[{name}]"
        else:
            return f"{amount} {name}"

    def step(self, target_avatar: "Avatar|str", item_id: str = "SPIRIT_STONE", amount: int = 100) -> ActionResult:
        """
        重写 step 以接收额外参数。
        将参数存入 self，然后调用父类 step 执行通用逻辑（LLM交互）。
        """
        # 每一帧都会传入参数，更新上下文
        obj, name, real_amount = self._resolve_gift(item_id, amount)
        
        self._current_gift_context = {
            "obj": obj,
            "name": name,
            "amount": real_amount,
            "original_item_id": item_id
        }
        
        # 调用父类 step，父类会调用 _build_prompt_infos -> _can_start 等
        return super().step(target_avatar)

    def _can_start(self, target: "Avatar") -> tuple[bool, str]:
        """检查赠送条件：物品是否存在且足够"""
        obj = self._current_gift_context.get("obj")
        name = self._current_gift_context.get("name")
        amount = self._current_gift_context.get("amount", 0)
        original_id = self._current_gift_context.get("original_item_id")
        
        # 修复：如果上下文未初始化（step/start 尚未执行），尝试从当前动作参数回溯
        if name is None and original_id is None:
            cur = self.avatar.current_action
            if cur and cur.action is self:
                p_item = cur.params.get("item_id", "SPIRIT_STONE")
                p_amount = cur.params.get("amount", 100)
                original_id = p_item
                obj, name, amount = self._resolve_gift(p_item, p_amount)
            else:
                return True, ""
        
        # 如果 name 为空，说明 resolve 失败
        if not name:
            return False, t("Item not found: {name}", name=original_id)

        # 1. 灵石
        spirit_stones_text = t("spirit stones")
        if obj is None and name == spirit_stones_text:
            if self.avatar.magic_stone < amount:
                return False, t("Insufficient spirit stones (current: {current}, need: {need})",
                              current=self.avatar.magic_stone, need=amount)
            return True, ""
            
        # 2. 物品 (装备/素材)
        from src.classes.items.weapon import Weapon
        from src.classes.items.auxiliary import Auxiliary
        from src.classes.items.elixir import Elixir
        
        if isinstance(obj, Elixir):
            return False, t("Elixirs cannot be gifted")
            
        if isinstance(obj, (Weapon, Auxiliary)):
            if self.avatar.weapon is not obj and self.avatar.auxiliary is not obj:
                 return False, t("Item not equipped: {name}", name=name)
        elif obj is not None:
            # Material
            qty = self.avatar.materials.get(obj, 0)
            if qty < amount:
                 return False, t("Insufficient item: {name}", name=name)
        else:
             return False, t("Item not found: {name}", name=original_id)

        # 检查交互范围 (父类 MutualAction.can_start 已经检查了，但这里是 _can_start 额外检查)
        from src.classes.observe import is_within_observation
            
        return True, ""

    def _build_prompt_infos(self, target_avatar: "Avatar") -> dict:
        """
        重写：构建传给 LLM 的 prompt 信息。
        """
        infos = super()._build_prompt_infos(target_avatar)
        
        gift_desc = self._get_gift_description()
        infos["action_info"] = t("Gift you {item}", item=gift_desc)
        
        return infos

    def start(self, target_avatar: "Avatar|str", item_id: str = "SPIRIT_STONE", amount: int = 100) -> Event:
        # start 也会接收参数，同样需要设置上下文
        obj, name, real_amount = self._resolve_gift(item_id, amount)
        self._current_gift_context = {
            "obj": obj, 
            "name": name, 
            "amount": real_amount, 
            "original_item_id": item_id
        }
        
        target = self._get_target_avatar(target_avatar)
        target_name = target.name if target is not None else str(target_avatar)
        
        gift_desc = self._get_gift_description()
        
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
        
        content = t("{initiator} attempts to gift {item} to {target}",
                   initiator=self.avatar.name, item=gift_desc, target=target_name)
        event = Event(
            self.world.month_stamp,
            content,
            related_avatars=rel_ids
        )
        
        self._gift_success = False
        return event

    def _settle_response(self, target_avatar: "Avatar", response_name: str) -> None:
        fb = str(response_name).strip()
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
            from src.classes.items.weapon import Weapon
            from src.classes.items.auxiliary import Auxiliary
            
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
                
                # 旧装备处理：直接调用 sell_X 接口
                # 这样既能获得灵石，也能自动触发 CirculationManager 记录流出物品
                if old_item:
                    if isinstance(old_item, Weapon):
                        target.sell_weapon(old_item)
                    elif isinstance(old_item, Auxiliary):
                        target.sell_auxiliary(old_item)
                    
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
            result_text = t("{initiator} successfully gifted {item} to {target}",
                          initiator=self.avatar.name, item=gift_desc, target=target.name)
            
            result_event = Event(
                self.world.month_stamp,
                result_text,
                related_avatars=[self.avatar.id, target.id]
            )
            events.append(result_event)
            a_to_b, b_to_a = await RelationDeltaService.resolve_event_text_delta(
                action_key="gift",
                avatar_a=self.avatar,
                avatar_b=target,
                event_text=result_text,
            )
            RelationDeltaService.apply_bidirectional_delta(self.avatar, target, a_to_b, b_to_a)
            story_event = await StoryEventService.maybe_create_story(
                kind=StoryEventKind.DAILY_SOCIAL,
                month_stamp=self.world.month_stamp,
                start_text=getattr(self, "_start_event_content", ""),
                result_text=result_text,
                actors=[self.avatar, target],
                related_avatar_ids=[self.avatar.id, target.id],
                allow_relation_changes=False,
            )
            if story_event is not None:
                events.append(story_event)
        else:
            gift_desc = self._get_gift_description()
            result_text = t("{target} rejected {initiator}'s gift: {item}",
                          target=target.name, initiator=self.avatar.name, item=gift_desc)
            a_to_b, b_to_a = await RelationDeltaService.resolve_event_text_delta(
                action_key="gift",
                avatar_a=self.avatar,
                avatar_b=target,
                event_text=result_text,
            )
            RelationDeltaService.apply_bidirectional_delta(self.avatar, target, a_to_b, b_to_a)
            
        return events
