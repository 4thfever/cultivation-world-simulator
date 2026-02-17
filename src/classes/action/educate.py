from __future__ import annotations

import random
from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.environment.region import CityRegion
from src.systems.cultivation import REALM_RANK

class Educate(TimedAction):
    """
    教化（儒门修炼）：在城市中教化世人，积累气运，提升修为。
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "educate_action_name"
    DESC_ID = "educate_description"
    REQUIREMENTS_ID = "educate_requirements"
    
    # 不需要翻译的常量
    EMOJI = "📖"
    PARAMS = {}

    duration_months = 3
    
    # 经验常量 (3个月基准)
    BASE_EXP_TOTAL = 150 # 基准总经验 (50/月 * 3)
    STANDARD_PROSPERITY = 50 # 标准繁荣度

    def _execute(self) -> None:
        """
        教化执行逻辑
        """
        # 瓶颈检查
        if self.avatar.cultivation_progress.is_in_bottleneck():
            return

        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return

        # 计算境界加成 (1, 2, 3, 4)
        realm = self.avatar.cultivation_progress.realm
        realm_multiplier = REALM_RANK.get(realm, 0) + 1
        
        # 计算繁荣度系数
        prosperity = region.prosperity
        prosperity_factor = prosperity / self.STANDARD_PROSPERITY
        
        # 计算基础经验
        exp = int(self.BASE_EXP_TOTAL * realm_multiplier * prosperity_factor)
        
        # 额外效率加成
        efficiency = float(self.avatar.effects.get("extra_educate_efficiency", 0.0))
        if efficiency > 0:
            exp = int(exp * (1 + efficiency))
            
        self.avatar.cultivation_progress.add_exp(exp)
        
        # 副作用：小概率增加城市繁荣度 (20%)
        base_prob = 0.2
        extra_prob = float(self.avatar.effects.get("extra_educate_prosperity_prob", 0.0))
        
        if random.random() < (base_prob + extra_prob):
            region.change_prosperity(0.2)
            self._prosperity_increased = True
        else:
            self._prosperity_increased = False
            
        self._last_exp = exp

    def can_start(self) -> tuple[bool, str]:
        # 1. 瓶颈检查
        if not self.avatar.cultivation_progress.can_cultivate():
            return False, t("Cultivation has reached bottleneck, cannot continue cultivating")
        
        # 2. 地点检查 (必须在城市)
        region = self.avatar.tile.region
        if not isinstance(region, CityRegion):
            return False, t("Must be in a City to educate people.")
            
        # 3. 权限检查 (必须拥有 Educate 权限)
        legal = self.avatar.effects.get("legal_actions", [])
        if "Educate" not in legal:
             return False, t("Your orthodoxy does not support Confucian Education.")
             
        return True, ""

    def start(self) -> Event:
        region = self.avatar.tile.region
        content = t("{avatar} begins educating people in {city}.", 
                   avatar=self.avatar.name, city=region.name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    async def finish(self) -> list[Event]:
        content = t("{avatar} finished educating people. Merit accumulated (+{exp}).",
                   avatar=self.avatar.name, exp=getattr(self, '_last_exp', 0))
        
        events = [Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])]
        
        if getattr(self, '_prosperity_increased', False):
            region = self.avatar.tile.region
            extra_content = t("The prosperity of {city} has increased due to {avatar}'s teachings.",
                             city=region.name, avatar=self.avatar.name)
            events.append(Event(self.world.month_stamp, extra_content, related_avatars=[self.avatar.id]))
            
        return events
