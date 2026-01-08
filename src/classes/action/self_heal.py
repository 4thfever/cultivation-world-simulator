from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.sect_region import SectRegion


class SelfHeal(TimedAction):
    """
    静养疗伤。
    单月动作。非宗门总部恢复一定比例HP，在宗门总部则回满HP。
    """

    ACTION_NAME = "疗伤"
    EMOJI = "💚"
    DESC = "运功疗伤，宗门总部可完全恢复"
    DOABLES_REQUIREMENTS = "当前HP未满"
    PARAMS = {}

    # 单月动作
    duration_months = 1

    def _execute(self) -> None:
        hp_obj = self.avatar.hp
        
        # 基础回复比例 (10%)
        base_ratio = 0.1
        
        # 特质/效果加成
        # extra_self_heal_efficiency 为小数，例如 0.5 代表 +50% 效率
        effect_bonus = float(self.avatar.effects.get("extra_self_heal_efficiency", 0.0))
        
        # 地点加成
        # 宗门总部：直接回满 (覆盖基础值，视为极大加成)
        is_hq = self._is_in_own_sect_headquarter()
        
        if is_hq:
            # 宗门总部：直接回满
            heal_amount = max(0, hp_obj.max - hp_obj.cur)
        else:
            # 普通区域：基础 + 加成
            # 计算总比例：基础 * (1 + 效率加成)
            total_ratio = base_ratio * (1.0 + effect_bonus)
            heal_amount = int(hp_obj.max * total_ratio)
            
        # 确保不溢出且至少为1（如果HP不满）
        heal_amount = min(heal_amount, hp_obj.max - hp_obj.cur)
        if hp_obj.cur < hp_obj.max:
            heal_amount = max(1, heal_amount)
        else:
            heal_amount = 0
        
        if heal_amount > 0:
            hp_obj.recover(heal_amount)
            
        self._healed_total = heal_amount

    def _is_in_own_sect_headquarter(self) -> bool:
        sect = getattr(self.avatar, "sect", None)
        if sect is None:
            return False
        tile = getattr(self.avatar, "tile", None)
        region = getattr(tile, "region", None)
        if not isinstance(region, SectRegion):
            return False
        hq_name = getattr(getattr(sect, "headquarter", None), "name", None) or getattr(sect, "name", None)
        return bool(hq_name) and region and region.name == hq_name

    def can_start(self) -> tuple[bool, str]:
        # 任何人任何地方都可疗伤，只要HP未满
        
        hp_obj = getattr(self.avatar, "hp", None)
        if hp_obj is None:
            return False, "缺少HP信息"
        if not (hp_obj.cur < hp_obj.max):
            return False, "当前HP已满"
        return True, ""

    def start(self) -> Event:
        region = getattr(getattr(self.avatar, "tile", None), "region", None)
        region_name = getattr(region, "name", "荒郊野外")
        # 重置累计量
        self._healed_total = 0
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {region_name} 开始静养疗伤", related_avatars=[self.avatar.id])

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        healed_total = int(getattr(self, "_healed_total", 0))
        # 统一用一次事件简要反馈
        return [Event(self.world.month_stamp, f"{self.avatar.name} 疗伤完成（本次恢复{healed_total}点，当前HP {self.avatar.hp}）", related_avatars=[self.avatar.id])]
