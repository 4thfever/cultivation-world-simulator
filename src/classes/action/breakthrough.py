from __future__ import annotations

import random
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.hp_and_mp import HP_MAX_BY_REALM, MP_MAX_BY_REALM
from src.classes.root import extra_breakthrough_success_rate


class Breakthrough(TimedAction):
    """
    突破境界。
    成功率由 `CultivationProgress.get_breakthrough_success_rate()` 决定；
    失败时按 `CultivationProgress.get_breakthrough_fail_reduce_lifespan()` 减少寿元（年）。
    """

    COMMENT = "尝试突破境界（成功增加寿元上限，失败折损寿元上限；境界越高，成功率越低。）"
    DOABLES_REQUIREMENTS = "角色处于瓶颈时"
    PARAMS = {}

    def calc_success_rate(self) -> float:
        """
        计算突破境界的成功率（由修为进度给出）
        """
        base = self.avatar.cultivation_progress.get_breakthrough_success_rate()
        bonus = extra_breakthrough_success_rate[self.avatar.root]
        # 夹紧到 [0, 1]
        return max(0.0, min(1.0, base + bonus))

    duration_months = 1

    def _execute(self) -> None:
        """
        突破境界
        """
        assert self.avatar.cultivation_progress.can_break_through()
        success_rate = self.calc_success_rate()
        # 记录本次尝试的基础信息
        self._success_rate_cached = success_rate
        if random.random() < success_rate:
            old_realm = self.avatar.cultivation_progress.realm
            self.avatar.cultivation_progress.break_through()
            new_realm = self.avatar.cultivation_progress.realm

            # 突破成功时更新HP和MP的最大值
            if new_realm != old_realm:
                self._update_hp_mp_on_breakthrough(new_realm)
                # 成功：确保最大寿元至少达到新境界的基线
                self.avatar.age.ensure_max_lifespan_at_least_realm_base(new_realm)
            # 记录结果用于 finish 事件
            self._last_result = (
                "success",
                getattr(old_realm, "value", str(old_realm)),
                getattr(new_realm, "value", str(new_realm)),
            )
        else:
            # 突破失败：减少最大寿元上限
            reduce_years = self.avatar.cultivation_progress.get_breakthrough_fail_reduce_lifespan()
            self.avatar.age.decrease_max_lifespan(reduce_years)
            # 记录结果用于 finish 事件
            self._last_result = ("fail", int(reduce_years))

    def _update_hp_mp_on_breakthrough(self, new_realm):
        """
        突破境界时更新HP和MP的最大值并完全恢复

        Args:
            new_realm: 新的境界
        """
        new_max_hp = HP_MAX_BY_REALM.get(new_realm, 100)
        new_max_mp = MP_MAX_BY_REALM.get(new_realm, 100)

        # 计算增加的最大值
        hp_increase = new_max_hp - self.avatar.hp.max
        mp_increase = new_max_mp - self.avatar.mp.max

        # 更新最大值并恢复相应的当前值
        self.avatar.hp.add_max(hp_increase)
        self.avatar.hp.recover(hp_increase)  # 突破时完全恢复HP
        self.avatar.mp.add_max(mp_increase)
        self.avatar.mp.recover(mp_increase)  # 突破时完全恢复MP

    def can_start(self) -> bool:
        return self.avatar.cultivation_progress.can_break_through()

    def start(self) -> Event:
        # 清理上次残留的结果状态（防御性）
        self._last_result = None
        self._success_rate_cached = None
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始尝试突破境界")

    # TimedAction 已统一 step 逻辑

    def finish(self) -> list[Event]:
        # 根据执行阶段记录的 _last_result 生成简洁完成事件
        res = getattr(self, "_last_result", None)
        if isinstance(res, tuple) and res:
            if res[0] == "success":
                return [Event(self.world.month_stamp, f"{self.avatar.name} 突破成功")]
            elif res[0] == "fail":
                return [Event(self.world.month_stamp, f"{self.avatar.name} 突破失败")]
            else:
                raise ValueError(f"Unknown result: {res}")


