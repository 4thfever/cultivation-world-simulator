from __future__ import annotations

import random
from src.i18n import t
from src.classes.action import TimedAction
from src.classes.action.cooldown import cooldown_action
from src.classes.death import handle_death
from src.classes.death_reason import DeathReason, DeathType
from src.classes.event import Event
from src.classes.story_event_service import StoryEventKind, StoryEventService
from src.systems.cultivation import REALM_RANK
from src.classes.action_runtime import ActionResult, ActionStatus

@cooldown_action
class Retreat(TimedAction):
    """
    闭关：赌博性质的行为。
    随机持续 1-5 年。
    成功：获得持续10年的突破概率加成。
    失败：减少寿元。
    """
    
    ACTION_NAME_ID = "retreat_action_name"
    DESC_ID = "retreat_desc"
    REQUIREMENTS_ID = "retreat_requirements"
    
    EMOJI = "🛖"
    PARAMS = {}
    
    # 闭关结束后1年内不能再次闭关
    ACTION_CD_MONTHS = 12
    IS_MAJOR = True
    
    # 闭关期间，不问世事，不染因果
    ALLOW_GATHERING = False
    ALLOW_WORLD_EVENTS = False

    def __init__(self, avatar, world):
        super().__init__(avatar, world)
        # 随机持续时间：12 - 60 个月 (1-5年)
        self.duration_months = random.randint(12, 60)
    
    def get_save_data(self) -> dict:
        data = super().get_save_data()
        data['duration_months'] = self.duration_months
        return data

    def load_save_data(self, data: dict) -> None:
        super().load_save_data(data)
        if 'duration_months' in data:
            self.duration_months = data['duration_months']

    def calc_success_rate(self) -> float:
        """
        计算闭关成功率
        练气(0): 50%, 筑基(1): 40%, 金丹(2): 30%, 元婴(3): 20%
        """
        realm_idx = REALM_RANK.get(self.avatar.cultivation_progress.realm, 0)
        base = 0.5 - (realm_idx * 0.1)
        base = max(0.1, base)
        
        # 应用effect加成
        extra_rate = self.avatar.effects.get("extra_retreat_success_rate", 0.0)
        return min(1.0, base + float(extra_rate))

    def _execute(self) -> None:
        # TimedAction 的 _execute 每月调用，这里主要做结束时的结算
        # 但 TimedAction.step 会在时间到时将状态设为 COMPLETED
        # 我们需要在 finish 中处理结算逻辑，或者在最后一次 step 中处理
        # 按照 TimedAction 的设计，_execute 是过程逻辑。
        # 我们可以留空 _execute，或者在这里加一些描述性事件（可选）
        pass

    async def finish(self) -> list[Event]:
        # 1. 判定结果
        success_rate = self.calc_success_rate()
        is_success = random.random() < success_rate
        
        events = []
        current_month = int(self.world.month_stamp)
        
        if is_success:
            # 成功：增加临时效果（10年 = 120个月）
            buff_duration = 120
            # 增加 20% 突破成功率
            bonus = {
                "extra_breakthrough_success_rate": 0.3
            }
            
            self.avatar.temporary_effects.append({
                "source": "Retreat Bonus",
                "effects": bonus,
                "start_month": current_month,
                "duration": buff_duration
            })
            self.avatar.recalc_effects()
            
            result_text = t("retreat_success", duration=self.duration_months)
            core_text = t("{avatar} finished retreat successfully.", avatar=self.avatar.name)
            
            prompt = t("retreat_story_prompt_success")
            events.append(Event(self.world.month_stamp, core_text, related_avatars=[self.avatar.id], is_major=True))
            story_event = await StoryEventService.maybe_create_story(
                kind=StoryEventKind.CULTIVATION_MAJOR,
                month_stamp=self.world.month_stamp,
                start_text=core_text,
                result_text=result_text,
                actors=[self.avatar],
                related_avatar_ids=[self.avatar.id],
                prompt=prompt,
                allow_relation_changes=False,
            )
            if story_event is not None:
                events.append(story_event)
            
        else:
            # 失败：扣除寿元
            # 随机扣除 5-20 年
            reduce_years = random.randint(5, 20)
            self.avatar.add_persistent_effect(
                "effect_source_retreat_failure",
                {"extra_max_lifespan": -int(reduce_years)},
            )
            is_dead = self.avatar.age.age >= self.avatar.age.max_lifespan
            if is_dead and not self.avatar.is_dead:
                handle_death(
                    self.world,
                    self.avatar,
                    DeathReason(DeathType.OLD_AGE),
                )
            
            result_text = t("retreat_fail", reduce_years=reduce_years)
            if is_dead:
                result_text += t("retreat_death_append")
                
            core_text = t("{avatar} failed retreat and lost {years} years of lifespan.", avatar=self.avatar.name, years=reduce_years)
            
            prompt = t("retreat_story_prompt_fail")
            events.append(Event(self.world.month_stamp, core_text, related_avatars=[self.avatar.id], is_major=True))
            story_event = await StoryEventService.maybe_create_story(
                kind=StoryEventKind.CULTIVATION_MAJOR,
                month_stamp=self.world.month_stamp,
                start_text=core_text,
                result_text=result_text,
                actors=[self.avatar],
                related_avatar_ids=[self.avatar.id],
                prompt=prompt,
                allow_relation_changes=False,
            )
            if story_event is not None:
                events.append(story_event)

        return events

    def can_start(self) -> tuple[bool, str]:
        # 任何时候都可以闭关，只要没死
        # 可以加个限制：寿元太少时不建议闭关？不，那是用户自己的选择（或者 AI 的愚蠢选择）
        return True, ""

    def start(self) -> Event:
        # 记录开始
        content = t("retreat_start", avatar=self.avatar.name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id], is_major=False)
