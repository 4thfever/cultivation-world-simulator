from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.root import get_essence_types_for_root
from src.classes.region import CultivateRegion


class Cultivate(TimedAction):
    """
    修炼动作，可以增加修仙进度。
    """

    COMMENT = "修炼，增进修为。在修炼区域（洞府）且灵气匹配时效果最佳，否则效果很差。"
    DOABLES_REQUIREMENTS = "角色未到瓶颈；若在洞府区域，则该洞府需无主或归自己所有。"
    PARAMS = {}

    duration_months = 10
    
    # 经验常量
    BASE_EXP_PER_DENSITY = 100   # 修炼区域每点灵气密度的基础经验
    BASE_EXP_LOW_EFFICIENCY = 50 # 无匹配灵气或非修炼区域的基础经验

    def _execute(self) -> None:
        """
        修炼
        获得的exp取决于区域类型和灵气匹配情况：
        - 修炼区域 + 匹配灵气：exp = BASE_EXP_PER_DENSITY * density
        - 修炼区域 + 无匹配灵气 或 非修炼区域：exp = BASE_EXP_LOW_EFFICIENCY
        """
        if self.avatar.cultivation_progress.is_in_bottleneck():
            return
            
        exp = self._calculate_base_exp()
        
        # 结算额外修炼经验（来自功法/宗门/灵根等）
        extra_exp = int(self.avatar.effects.get("extra_cultivate_exp", 0) or 0)
        if extra_exp:
            exp += extra_exp
            
        self.avatar.cultivation_progress.add_exp(exp)

    def _get_matched_essence_density(self) -> int:
        """
        获取当前区域与角色灵根匹配的灵气密度。
        若不在修炼区域或无匹配灵气，返回 0。
        """
        region = self.avatar.tile.region
        if not isinstance(region, CultivateRegion):
            return 0
        essence_types = get_essence_types_for_root(self.avatar.root)
        return max((region.essence.get_density(et) for et in essence_types), default=0)

    def _calculate_base_exp(self) -> int:
        """
        根据区域类型和灵气匹配情况计算基础经验
        """
        density = self._get_matched_essence_density()
        if density > 0:
            return self.BASE_EXP_PER_DENSITY * density
        return self.BASE_EXP_LOW_EFFICIENCY

    def can_start(self) -> tuple[bool, str]:
        # 瓶颈检查
        if not self.avatar.cultivation_progress.can_cultivate():
            return False, "修为已达瓶颈，无法继续修炼"
        
        region = self.avatar.tile.region
        
        # 如果在修炼区域，检查洞府所有权
        if isinstance(region, CultivateRegion):
            if region.host_avatar is not None and region.host_avatar != self.avatar:
                return False, f"该洞府已被 {region.host_avatar.name} 占据，无法修炼"
        
        return True, ""

    def start(self) -> Event:
        # 计算修炼时长缩减
        reduction = float(self.avatar.effects.get("cultivate_duration_reduction", 0.0))
        reduction = max(0.0, min(0.9, reduction))
        
        # 动态设置此次修炼的实际duration
        base_duration = self.__class__.duration_months
        actual_duration = max(1, round(base_duration * (1.0 - reduction)))
        self.duration_months = actual_duration
        
        efficiency = "进境颇佳" if self._get_matched_essence_density() > 0 else "进境缓慢"
        return Event(self.world.month_stamp, f"{self.avatar.name} 在 {self.avatar.tile.region.name} 开始修炼，{efficiency}", related_avatars=[self.avatar.id])

    async def finish(self) -> list[Event]:
        return []
