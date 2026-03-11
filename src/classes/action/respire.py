from __future__ import annotations

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.root import get_essence_types_for_root
from src.classes.environment.region import CultivateRegion
from src.classes.environment.sect_region import SectRegion


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

    def can_possibly_start(self) -> bool:
        legal = self.avatar.effects.get("legal_actions", [])
        if legal and "Respire" not in legal:
            return False
        return True

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
        - 洞府/秘境 (CultivateRegion)：按原有逻辑根据单一灵气类型计算；
        - 宗门总部 (SectRegion)：仅本门弟子视为修炼环境，五行等效密度为 5；
        - 其它区域：返回 0。
        """
        region = self.avatar.tile.region
        essence_types = get_essence_types_for_root(self.avatar.root)

        # 洞府/遗迹
        if isinstance(region, CultivateRegion):
            return max((region.essence.get_density(et) for et in essence_types), default=0)

        # 宗门总部：仅本门弟子享受「五行皆为 5」的兜底修炼环境
        if isinstance(region, SectRegion):
            sect = getattr(self.avatar, "sect", None)
            if sect is None or sect.id != region.sect_id:
                return 0
            return max((region.essence.get_density(et) for et in essence_types), default=0)

        return 0

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

        # 宗门总部：仅本门弟子可以在此吐纳
        if isinstance(region, SectRegion):
            sect = getattr(self.avatar, "sect", None)
            if sect is None or sect.id != region.sect_id:
                return False, t("respire_sect_hq_members_only")
        
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

        # 在本门宗门总部吐纳：使用专用效率文案，体现「兜底但不如秘境」
        if isinstance(region, SectRegion):
            sect = getattr(self.avatar, "sect", None)
            if sect is not None and sect.id == region.sect_id and matched_density > 0:
                efficiency = t("respire_efficiency_sect_hq")
            elif matched_density > 0:
                # 理论上非本门无法在总部开始吐纳，但兜底处理为普通优秀进展
                efficiency = t("excellent progress")
            else:
                efficiency = t("slow progress (sparse essence)")
        else:
            if matched_density > 0:
                efficiency = t("excellent progress")
            elif isinstance(region, CultivateRegion) and getattr(region, "essence_density", 0) > 0:
                efficiency = t("slow progress (essence mismatch)")
            else:
                efficiency = t("slow progress (sparse essence)")

        content = t("{avatar} begins respiring at {location}, {efficiency}",
                   avatar=self.avatar.name, location=self.avatar.tile.location_name, efficiency=efficiency)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    async def finish(self) -> list[Event]:
        return []
