"""
Avatar 效果计算 Mixin

负责角色效果的计算和应用。
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.classes.avatar.core import Avatar

from .process import _merge_effects, _evaluate_conditional_effect
from src.classes.hp import HP_MAX_BY_REALM


class EffectsMixin:
    """效果计算相关方法"""
    
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
        """
        merged: dict[str, object] = {}
        
        def _process_source(source_obj):
            if source_obj is None:
                return
            # 1. 评估条件 (when)
            evaluated = _evaluate_conditional_effect(source_obj.effects, self)
            # 2. 评估动态值 (expressions)
            evaluated = self._evaluate_values(evaluated)
            # 3. 合并到总效果
            nonlocal merged
            merged = _merge_effects(merged, evaluated)

        # 来自宗门
        if self.sect is not None:
            _process_source(self.sect)
            
        # 来自功法
        if self.technique is not None:
            _process_source(self.technique)
            
        # 来自灵根
        if self.root is not None:
            _process_source(self.root)
            
        # 来自特质（persona）
        for persona in self.personas:
            _process_source(persona)
            
        # 来自兵器
        if self.weapon is not None:
            _process_source(self.weapon)
            
        # 来自辅助装备
        if self.auxiliary is not None:
            _process_source(self.auxiliary)
            
        # 来自灵兽
        if self.spirit_animal is not None:
            _process_source(self.spirit_animal)
            
        # 来自天地灵机（世界级buff/debuff）
        if self.world.current_phenomenon is not None:
            _process_source(self.world.current_phenomenon)

        # 来自已服用的丹药
        # 简化逻辑：直接 merge 所有丹药的效果
        for consumed in self.elixirs:
            _process_source(consumed.elixir)

        return merged

    def get_effect_breakdown(self: "Avatar") -> list[tuple[str, dict[str, Any]]]:
        """
        获取效果明细，返回 [(来源名称, 生效的效果字典), ...]
        用于 get_desc 展示。
        """
        breakdown = []
        
        def _collect(name: str, source_obj):
            if source_obj is None:
                return
            # 1. 评估条件 (when)
            evaluated = _evaluate_conditional_effect(source_obj.effects, self)
            # 2. 评估动态值 (expressions)
            evaluated = self._evaluate_values(evaluated)
            
            if evaluated:
                breakdown.append((name, evaluated))

        # 按照优先级或逻辑顺序收集
        if self.sect:
            _collect(f"宗门【{self.sect.name}】", self.sect)
            
        if self.technique:
            _collect(f"功法【{self.technique.name}】", self.technique)
            
        if self.root:
            _collect("灵根", self.root)
            
        for p in self.personas:
            _collect(f"特质【{p.name}】", p)
            
        if self.weapon:
            _collect(f"兵器【{self.weapon.name}】", self.weapon)
            
        if self.auxiliary:
            _collect(f"辅助【{self.auxiliary.name}】", self.auxiliary)
            
        if self.spirit_animal:
            _collect(f"灵兽【{self.spirit_animal.name}】", self.spirit_animal)
            
        if self.world.current_phenomenon:
            _collect("天地灵机", self.world.current_phenomenon)

        for consumed in self.elixirs:
            _collect(f"丹药【{consumed.elixir.name}】", consumed.elixir)

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

