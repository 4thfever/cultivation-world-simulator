"""
Avatar 效果计算 Mixin

负责角色效果的计算和应用。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.classes.core.avatar.core import Avatar

from .process import _merge_effects, _evaluate_conditional_effect
from src.classes.hp import HP_MAX_BY_REALM


class EffectsMixin:
    """效果计算相关方法"""
    
    def get_active_temporary_effects(self: "Avatar") -> list[dict[str, Any]]:
        """获取当前生效的临时效果列表"""
        current_month = int(self.world.month_stamp)
        return [
            eff for eff in getattr(self, "temporary_effects", [])
            if current_month < eff.get("start_month", 0) + eff.get("duration", 0)
        ]

    def _evaluate_values(self, effects: dict[str, Any]) -> dict[str, Any]:
        """
        评估效果字典中的动态值（字符串表达式）。
        支持明确的 'eval(...)' 格式，以及包含 'avatar.' 的隐式表达式。
        """
        result = {}
        # 安全的 eval 上下文
        context = {
            "__builtins__": {},
            "avatar": self,
            "max": max,
            "min": min,
            "int": int,
            "float": float,
            "round": round,
        }

        for k, v in effects.items():
            if isinstance(v, str):
                s = v.strip()
                expr = None
                
                # 检查是否为表达式
                if s.startswith("eval(") and s.endswith(")"):
                    expr = s[5:-1]
                elif "avatar." in s: # 启发式：包含 avatar. 则视为表达式
                    expr = s
                
                if expr:
                    try:
                        result[k] = eval(expr, context)
                    except Exception:
                        # 评估失败，保留原值（可能是普通字符串，或者表达式有误）
                        result[k] = v
                else:
                    result[k] = v
            else:
                result[k] = v
        return result

    @property
    def effects(self: "Avatar") -> dict[str, object]:
        """
        合并所有来源的效果：宗门、功法、灵根、特质、兵器、辅助装备、灵兽、天地灵机、丹药
        直接复用 get_effect_breakdown 的逻辑，确保显示与实际效果一致。
        """
        merged: dict[str, object] = {}
        
        # get_effect_breakdown 已经完成了条件评估(when)和动态值计算(expressions)
        # 我们只需要合并结果即可
        for _, effect_dict in self.get_effect_breakdown():
            merged = _merge_effects(merged, effect_dict)

        return merged

    def get_effect_breakdown(self: "Avatar") -> list[tuple[str, dict[str, Any]]]:
        """
        获取效果明细，返回 [(来源名称, 生效的效果字典), ...]
        用于 get_desc 展示。
        """
        from src.i18n import t
        breakdown = []
        
        def _collect(name: str, source_obj=None, explicit_effects=None):
            """
            收集效果。
            source_obj: 包含 .effects 的对象
            explicit_effects: 直接传入的 effects (dict or list)
            """
            raw_effects = explicit_effects
            if raw_effects is None and source_obj is not None:
                raw_effects = getattr(source_obj, "effects", {})
                
            if not raw_effects:
                return

            # 1. 评估条件 (when)
            evaluated = _evaluate_conditional_effect(raw_effects, self)
            # 2. 评估动态值 (expressions)
            evaluated = self._evaluate_values(evaluated)
            
            if evaluated:
                breakdown.append((name, evaluated))

        # 按照优先级或逻辑顺序收集（使用翻译）
        if self.sect:
            label = t("Sect [{name}]", name=self.sect.name)
            _collect(label, source_obj=self.sect)
        else:
            # 散修应用默认道统效果
            from src.classes.core.orthodoxy import get_orthodoxy
            sanxiu_orthodoxy = get_orthodoxy("sanxiu")
            if sanxiu_orthodoxy:
                label = t("Orthodoxy [{name}]", name=t(sanxiu_orthodoxy.name))
                _collect(label, source_obj=sanxiu_orthodoxy)
            
        if self.technique:
            label = t("Technique [{name}]", name=self.technique.name)
            _collect(label, source_obj=self.technique)
            
        if self.root:
            _collect(t("Spirit Root"), source_obj=self.root)
            
        for p in self.personas:
            label = t("Trait [{name}]", name=p.name)
            _collect(label, source_obj=p)
            
        if self.weapon:
            label = t("Weapon [{name}]", name=self.weapon.name)
            _collect(label, source_obj=self.weapon)
            
        if self.auxiliary:
            label = t("Auxiliary [{name}]", name=self.auxiliary.name)
            _collect(label, source_obj=self.auxiliary)
            
        if self.spirit_animal:
            label = t("Spirit Animal [{name}]", name=self.spirit_animal.name)
            _collect(label, source_obj=self.spirit_animal)
            
        if self.world.current_phenomenon:
            _collect(t("Heaven and Earth Phenomenon"), source_obj=self.world.current_phenomenon)

        for consumed in self.elixirs:
            # 使用 get_active_effects 获取当前生效的效果
            active = consumed.get_active_effects(int(self.world.month_stamp))
            label = t("Elixir [{name}]", name=consumed.elixir.name)
            _collect(label, explicit_effects=active)

        # 处理临时效果（如闭关获得的短期加成）
        for temp_eff in self.get_active_temporary_effects():
            # 来源显示，支持翻译
            source_key = temp_eff.get("source", "Unknown")
            label = t(source_key)
            _collect(label, explicit_effects=temp_eff.get("effects", {}))

        return breakdown

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
