from __future__ import annotations

import random
from src.classes.action import TimedAction
from src.classes.action.cooldown import cooldown_action
from src.classes.event import Event
from src.classes.cultivation import Realm
from src.classes.story_teller import StoryTeller
from src.classes.tribulation import TribulationSelector
from src.classes.hp_and_mp import HP_MAX_BY_REALM
from src.classes.effect import _merge_effects

# —— 配置：哪些"出发境界"会生成突破小故事（global var）——
ALLOW_STORY_FROM_REALMS: list[Realm] = [
    Realm.Foundation_Establishment,  # 筑基
    Realm.Core_Formation,            # 金丹
]


@cooldown_action
class Breakthrough(TimedAction):
    """
    突破境界。
    成功率由 `CultivationProgress.get_breakthrough_success_rate()` 决定；
    失败时按 `CultivationProgress.get_breakthrough_fail_reduce_lifespan()` 减少寿元（年）。
    """

    ACTION_NAME = "突破"
    DESC = "尝试突破境界（成功增加寿元上限，失败折损寿元上限；境界越高，成功率越低。）"
    DOABLES_REQUIREMENTS = "角色处于瓶颈时；不能连续执行"
    PARAMS = {}
    # 冷却：突破应当有CD，避免连刷
    ACTION_CD_MONTHS: int = 3
    # 突破是大事（长期记忆）
    IS_MAJOR: bool = True
    # 保留类级常量声明，实际读取模块级配置

    def calc_success_rate(self) -> float:
        """
        计算突破境界的成功率（由修为进度给出）
        """
        base = self.avatar.cultivation_progress.get_breakthrough_success_rate()
        # 统一从 avatar.effects 读取额外加成（root/technique/sect 等已合并）
        bonus = float(self.avatar.effects.get("extra_breakthrough_success_rate", 0.0))
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

            # 突破成功时更新HP的最大值
            if new_realm != old_realm:
                self._update_hp_on_breakthrough(new_realm)
                # 成功：确保最大寿元至少达到新境界的基线
                self.avatar.age.ensure_max_lifespan_at_least_realm_base(new_realm)
            # 记录结果用于 finish 事件
            self._last_result = (
                "success",
                old_realm.value,
                new_realm.value,
            )
        else:
            # 突破失败：减少最大寿元上限
            reduce_years = self.avatar.cultivation_progress.get_breakthrough_fail_reduce_lifespan()
            self.avatar.age.decrease_max_lifespan(reduce_years)
            # 记录结果用于 finish 事件
            self._last_result = ("fail", int(reduce_years))

    def _update_hp_on_breakthrough(self, new_realm):
        """
        突破境界时更新HP的最大值并完全恢复

        Args:
            new_realm: 新的境界
        """
        new_max_hp = HP_MAX_BY_REALM.get(new_realm, 100)

        # 计算增加的最大值
        hp_increase = new_max_hp - self.avatar.hp.max

        # 更新最大值并恢复相应的当前值
        self.avatar.hp.add_max(hp_increase)
        self.avatar.hp.recover(hp_increase)  # 突破时完全恢复HP

    def can_start(self) -> tuple[bool, str]:
        ok = self.avatar.cultivation_progress.can_break_through()
        return (ok, "" if ok else "当前不处于瓶颈，无法突破")

    def start(self) -> Event:
        # 初始化状态
        self._last_result = None
        self._success_rate_cached = None
        # 预判是否生成故事与选择劫难
        old_realm = self.avatar.cultivation_progress.realm
        self._gen_story = old_realm in ALLOW_STORY_FROM_REALMS
        if self._gen_story:
            self._calamity = TribulationSelector.choose_tribulation(self.avatar)
            self._calamity_other = TribulationSelector.choose_related_avatar(self.avatar, self._calamity)
        else:
            self._calamity = None
            self._calamity_other = None
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始尝试突破境界", related_avatars=[self.avatar.id], is_major=True)

    # TimedAction 已统一 step 逻辑

    async def finish(self) -> list[Event]:
        if not self._last_result:
            return []
        result_ok = self._last_result[0] == "success"
        if not self._gen_story:
            # 不生成故事：不出现劫难，仅简单结果
            core_text = f"{self.avatar.name} 突破{'成功' if result_ok else '失败'}"
            return [Event(self.world.month_stamp, core_text, related_avatars=[self.avatar.id], is_major=True)]

        calamity = self._calamity
        core_text = f"{self.avatar.name} 遭遇了{calamity}劫难，突破{'成功' if result_ok else '失败'}"
        rel_ids = [self.avatar.id]
        if self._calamity_other is not None:
            try:
                rel_ids.append(self._calamity_other.id)
            except Exception:
                pass
        events: list[Event] = [Event(self.world.month_stamp, core_text, related_avatars=rel_ids, is_major=True)]

        # 故事参与者：本体 +（可选）相关角色
        prompt = TribulationSelector.get_story_prompt(str(calamity))
        # 突破强制单人模式，不改变关系（因为没有双修/战斗那样的互动）
        story = await StoryTeller.tell_story(core_text, ("突破成功" if result_ok else "突破失败"), self.avatar, self._calamity_other, prompt=prompt, allow_relation_changes=False)
        events.append(Event(self.world.month_stamp, story, related_avatars=rel_ids, is_story=True))
        return events
