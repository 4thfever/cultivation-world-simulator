from __future__ import annotations

import random
from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event
from src.systems.cultivation import REALM_RANK

class Meditate(TimedAction):
    """
    禅定（佛门修炼）：不依赖灵气，通过坐禅平复心境，概率顿悟获得大量修为。
    """
    
    # 多语言 ID
    ACTION_NAME_ID = "meditate_action_name"
    DESC_ID = "meditate_description"
    REQUIREMENTS_ID = "meditate_requirements"
    
    # 不需要翻译的常量
    EMOJI = "🧘"
    PARAMS = {}

    duration_months = 3
    
    # 经验常量
    BASE_EXP = 10       # 普通禅定经验（极少）
    EPIPHANY_EXP = 1500 # 顿悟经验（极多，期望值约 50/月）
    BASE_PROB = 0.1     # 基础顿悟概率 10%

    def can_possibly_start(self) -> bool:
        legal = self.avatar.effects.get("legal_actions", [])
        if "Meditate" not in legal:
            return False
        return True

    def _execute(self) -> None:
        """
        禅定执行逻辑
        """
        # 瓶颈检查
        if self.avatar.cultivation_progress.is_in_bottleneck():
            return

        # 计算境界加成 (1, 2, 3, 4)
        realm = self.avatar.cultivation_progress.realm
        realm_multiplier = REALM_RANK.get(realm, 0) + 1
        
        # 计算顿悟概率
        prob = self.BASE_PROB + float(self.avatar.effects.get("extra_meditate_prob", 0.0))
        
        # 判定是否顿悟
        is_epiphany = random.random() < prob
        
        base_exp = self.EPIPHANY_EXP if is_epiphany else self.BASE_EXP
        
        # 计算最终经验
        exp = int(base_exp * realm_multiplier)
        
        # 额外加成
        multiplier = float(self.avatar.effects.get("extra_meditate_exp_multiplier", 0.0))
        if multiplier > 0:
            exp = int(exp * (1 + multiplier))
            
        self.avatar.cultivation_progress.add_exp(exp)
        
        # 记录本次结果供事件使用
        self._last_is_epiphany = is_epiphany
        self._last_exp = exp

    def can_start(self) -> tuple[bool, str]:
        # 1. 瓶颈检查
        if not self.avatar.cultivation_progress.can_cultivate():
            return False, t("Cultivation has reached bottleneck, cannot continue cultivating")
        
        # 2. 权限检查 (必须拥有 Meditate 权限)
        legal = self.avatar.effects.get("legal_actions", [])
        if "Meditate" not in legal:
             return False, t("Your orthodoxy does not support Zen Meditation.")
             
        return True, ""

    def start(self) -> Event:
        # 记录开始时间
        content = t("{avatar} begins Zen Meditation.", avatar=self.avatar.name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    async def finish(self) -> list[Event]:
        # 结束时根据是否顿悟生成不同的日志
        if getattr(self, '_last_is_epiphany', False):
            content = t("{avatar} had an epiphany during meditation! Cultivation increased significantly (+{exp}).", 
                       avatar=self.avatar.name, exp=getattr(self, '_last_exp', 0))
        else:
            content = t("{avatar} completed meditation with a peaceful mind.", 
                       avatar=self.avatar.name)
            
        return [Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])]
