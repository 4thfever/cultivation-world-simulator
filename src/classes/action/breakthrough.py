from __future__ import annotations

import random
from src.classes.action import TimedAction
from src.classes.event import Event
from src.classes.cultivation import Realm
from src.classes.story_teller import StoryTeller
from src.classes.relation import Relation

# —— 配置：哪些“出发境界”会生成突破小故事（global var）——
ALLOW_STORY_FROM_REALMS: list[Realm] = [
    Realm.Foundation_Establishment,  # 筑基
    Realm.Core_Formation,            # 金丹
]

# 故事提示词（global var）
STORY_PROMPT_BASE = "以古风、凝练、不炫技的笔触，描绘修士历经{calamity}劫时的心境与取舍，篇幅60~120字。"

# 劫难说明（global var）
CALAMITY_DESCRIPTIONS: dict[str, str] = {
    "心魔": "心念起伏，自我否定与执念缠斗，外寂而内喧。",
    "雷劫": "天威如潮，电光凝成纹理，压迫骨血与神识。",
    "肉身": "筋骨皮膜重塑，真气磨砺经脉，疼痛与新生并至。",
    "寻仇": "仇人旧怨不散，刀光在心底回响，一念之差改写因果。",
    "情劫": "柔情即刃，难舍难分，念头被拉回人间烟火。",
}
from src.classes.hp_and_mp import HP_MAX_BY_REALM, MP_MAX_BY_REALM
from src.classes.effect import _merge_effects


class Breakthrough(TimedAction):
    """
    突破境界。
    成功率由 `CultivationProgress.get_breakthrough_success_rate()` 决定；
    失败时按 `CultivationProgress.get_breakthrough_fail_reduce_lifespan()` 减少寿元（年）。
    """

    COMMENT = "尝试突破境界（成功增加寿元上限，失败折损寿元上限；境界越高，成功率越低。）"
    DOABLES_REQUIREMENTS = "角色处于瓶颈时"
    PARAMS = {}
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
        # 清理状态
        self._last_result = None
        self._success_rate_cached = None
        # 预判是否生成故事与选择劫难
        old_realm = self.avatar.cultivation_progress.realm
        # 仅基于出发境界判断是否生成故事
        self._gen_story = old_realm in ALLOW_STORY_FROM_REALMS
        if self._gen_story:
            self._calamity = self._choose_calamity()
            self._calamity_other = self._choose_related_avatar(self._calamity)
        else:
            self._calamity = None
            self._calamity_other = None
        return Event(self.world.month_stamp, f"{self.avatar.name} 开始尝试突破境界")

    # TimedAction 已统一 step 逻辑

    def finish(self) -> list[Event]:
        res = getattr(self, "_last_result", None)
        if not (isinstance(res, tuple) and res):
            return []
        result_ok = res[0] == "success"
        if not getattr(self, "_gen_story", False):
            # 不生成故事：不出现劫难，仅简单结果
            core_text = f"{self.avatar.name} 突破{'成功' if result_ok else '失败'}"
            return [Event(self.world.month_stamp, core_text)]

        calamity = getattr(self, "_calamity", "劫难")
        core_text = f"{self.avatar.name} 遭遇了{calamity}劫难，突破{'成功' if result_ok else '失败'}"
        events: list[Event] = [Event(self.world.month_stamp, core_text)]

        if True:
            # 故事参与者：本体 +（可选）相关角色
            desc = CALAMITY_DESCRIPTIONS.get(str(calamity), "")
            prompt = (STORY_PROMPT_BASE.format(calamity=str(calamity)) + (" " + desc if desc else "")).strip()
            story = StoryTeller.tell_from_actors(core_text, ("突破成功" if result_ok else "突破失败"), self.avatar, getattr(self, "_calamity_other", None), prompt=prompt)
            events.append(Event(self.world.month_stamp, story))
        return events

    # ——— 内部：劫难选择与关联角色 ———
    def _choose_calamity(self) -> str:
        base = ["心魔", "雷劫", "肉身"]
        rels = getattr(self.avatar, "relations", {})
        has_enemy = any(rel is Relation.ENEMY for rel in rels.values())
        has_lover = any(rel is Relation.LOVERS for rel in rels.values())
        if has_enemy:
            base.append("寻仇")
        if has_lover:
            base.append("情劫")
        return random.choice(base)

    def _choose_related_avatar(self, calamity: str):
        if calamity not in ("寻仇", "情劫"):
            return None
        target_rel = Relation.ENEMY if calamity == "寻仇" else Relation.LOVERS
        candidates = [other for other, rel in self.avatar.relations.items() if rel is target_rel]
        if not candidates:
            return None
        return random.choice(candidates)


