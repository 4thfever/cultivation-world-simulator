"""
Avatar 效果计算 Mixin

负责角色效果的计算和应用。
"""
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.avatar.core import Avatar

from src.classes.effect import _merge_effects, _evaluate_conditional_effect
from src.classes.hp_and_mp import HP_MAX_BY_REALM


class EffectsMixin:
    """效果计算相关方法"""
    
    @property
    def effects(self: "Avatar") -> dict[str, object]:
        """
        合并所有来源的效果：宗门、功法、灵根、特质、兵器、辅助装备、灵兽、天地灵机
        """
        merged: dict[str, object] = defaultdict(str)
        # 来自宗门
        if self.sect is not None:
            evaluated = _evaluate_conditional_effect(self.sect.effects, self)
            merged = _merge_effects(merged, evaluated)
        # 来自功法
        evaluated = _evaluate_conditional_effect(self.technique.effects, self)
        merged = _merge_effects(merged, evaluated)
        # 来自灵根
        evaluated = _evaluate_conditional_effect(self.root.effects, self)
        merged = _merge_effects(merged, evaluated)
        # 来自特质（persona）
        for persona in self.personas:
            evaluated = _evaluate_conditional_effect(persona.effects, self)
            merged = _merge_effects(merged, evaluated)
        # 来自兵器
        if self.weapon is not None:
            evaluated = _evaluate_conditional_effect(self.weapon.effects, self)
            merged = _merge_effects(merged, evaluated)
        # 来自辅助装备
        if self.auxiliary is not None:
            evaluated = _evaluate_conditional_effect(self.auxiliary.effects, self)
            merged = _merge_effects(merged, evaluated)
        # 来自灵兽
        if self.spirit_animal is not None:
            evaluated = _evaluate_conditional_effect(self.spirit_animal.effects, self)
            merged = _merge_effects(merged, evaluated)
        # 来自天地灵机（世界级buff/debuff）
        if self.world.current_phenomenon is not None:
            evaluated = _evaluate_conditional_effect(self.world.current_phenomenon.effects, self)
            merged = _merge_effects(merged, evaluated)
        # 评估动态效果表达式：值以 "eval(...)" 形式给出
        final: dict[str, object] = {}
        for k, v in merged.items():
            if isinstance(v, str):
                s = v.strip()
                if s.startswith("eval(") and s.endswith(")"):
                    expr = s[5:-1]
                    final[k] = eval(expr, {"__builtins__": {}}, {"avatar": self})
                    continue
            final[k] = v
        return final

    def recalc_effects(self: "Avatar") -> None:
        """
        重新计算所有长期效果
        在装备更换、突破境界等情况下调用
        
        当前包括：
        - HP 最大值
        - 寿命最大值
        """
        # 计算基础最大值（基于境界）
        base_max_hp = HP_MAX_BY_REALM.get(self.cultivation_progress.realm, 100)
        
        # 访问 self.effects 会触发 @property，重新 merge 所有 effects
        effects = self.effects
        extra_max_hp = int(effects.get("extra_max_hp", 0))
        extra_max_lifespan = int(effects.get("extra_max_lifespan", 0))
        
        # 计算新的最大值
        new_max_hp = base_max_hp + extra_max_hp
        
        # 更新最大值
        self.hp.max = new_max_hp
        
        # 更新寿命
        if self.age:
            self.age.max_lifespan = self.age.base_max_lifespan + extra_max_lifespan
        
        # 调整当前值（不超过新的最大值）
        if self.hp.cur > new_max_hp:
            self.hp.cur = new_max_hp

    def update_time_effect(self: "Avatar") -> None:
        """
        随时间更新的被动效果。
        当前实现：当 HP 未满时，回复最大生命值的 1%（受HP恢复速率加成影响）。
        """
        if self.hp.cur < self.hp.max:
            base_recover = self.hp.max * 0.01
            
            # 应用HP恢复速率加成
            recovery_rate_raw = self.effects.get("extra_hp_recovery_rate", 0.0)
            recovery_rate_multiplier = 1.0 + float(recovery_rate_raw or 0.0)
            
            recover_amount = int(base_recover * recovery_rate_multiplier)
            self.hp.recover(recover_amount)

    @property
    def move_step_length(self: "Avatar") -> int:
        """获取角色的移动步长"""
        return self.cultivation_progress.get_move_step()

