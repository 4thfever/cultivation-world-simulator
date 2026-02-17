from __future__ import annotations

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.root import get_essence_types_for_root
from src.classes.environment.region import CultivateRegion


class Respire(TimedAction):
    """
    吐纳动作，可以增加修仙进度。
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "respire_action_name"
    DESC_ID = "respire_description"
    REQUIREMENTS_ID = "respire_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🌀"
    PARAMS = {}

    duration_months = 10
    
    # 经验常量
    BASE_EXP_PER_DENSITY = 100   # 修炼区域每点灵气密度的基础经验
    BASE_EXP_LOW_EFFICIENCY = 50 # 无匹配灵气或非修炼区域的基础经验

    def _execute(self) -> None:
        """
        吐纳
        获得的exp取决于区域类型和灵气匹配情况：
        - 修炼区域 + 匹配灵气：exp = BASE_EXP_PER_DENSITY * density
        - 修炼区域 + 无匹配灵气 或 非修炼区域：exp = BASE_EXP_LOW_EFFICIENCY
        """
        if self.avatar.cultivation_progress.is_in_bottleneck():
            return
            
        exp = self._calculate_base_exp()
        
        # 结算额外吐纳经验（来自功法/宗门/灵根等）
        extra_exp = int(self.avatar.effects.get("extra_respire_exp", 0) or 0)
        if extra_exp:
            exp += extra_exp

        # 结算额外吐纳经验倍率
        multiplier = float(self.avatar.effects.get("extra_respire_exp_multiplier", 0.0) or 0.0)
        if multiplier > 0:
            exp = int(exp * (1 + multiplier))
            
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
            return False, t("Cultivation has reached bottleneck, cannot continue cultivating")
            
        # 权限检查 (道门或散修)
        # 如果 legal_actions 不为空，且不包含 "Respire"，则禁止 (说明是其他道统，如佛/儒)
        legal = self.avatar.effects.get("legal_actions", [])
        if legal and "Respire" not in legal:
            return False, t("Your orthodoxy does not support Qi Respiration.")
        
        region = self.avatar.tile.region
        
        # 如果在修炼区域，检查洞府所有权
        if isinstance(region, CultivateRegion):
            if region.host_avatar is not None and region.host_avatar != self.avatar:
                return False, t("This cave dwelling has been occupied by {name}, cannot respire",
                               name=region.host_avatar.name)
        
        return True, ""

    def start(self) -> Event:
        # 计算吐纳时长缩减
        reduction = float(self.avatar.effects.get("respire_duration_reduction", 0.0))
        reduction = max(0.0, min(0.9, reduction))
        
        # 动态设置此次吐纳的实际duration
        base_duration = self.__class__.duration_months
        actual_duration = max(1, round(base_duration * (1.0 - reduction)))
        self.duration_months = actual_duration
        
        matched_density = self._get_matched_essence_density()
        region = self.avatar.tile.region
        
        if matched_density > 0:
            efficiency = t("excellent progress")
        elif isinstance(region, CultivateRegion) and region.essence_density > 0:
            efficiency = t("slow progress (essence mismatch)")
        else:
            efficiency = t("slow progress (sparse essence)")

        content = t("{avatar} begins respiring at {location}, {efficiency}",
                   avatar=self.avatar.name, location=self.avatar.tile.location_name, efficiency=efficiency)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    async def finish(self) -> list[Event]:
        return []
