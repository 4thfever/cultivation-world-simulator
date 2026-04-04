from __future__ import annotations

from src.classes.action import TimedAction
from src.classes.environment.region import CityRegion
from src.classes.event import Event
from src.classes.official_rank import (
    apply_official_reputation_delta,
    calculate_governance_reputation_gain,
    get_governance_salary,
    get_official_rank_name,
    resolve_rank_changes,
)
from src.classes.story_event_service import StoryEventKind, StoryEventService
from src.i18n import t


class Govern(TimedAction):
    ACTION_NAME_ID = "govern_action_name"
    DESC_ID = "govern_description"
    REQUIREMENTS_ID = "govern_requirements"

    EMOJI = "🏛"
    PARAMS = {}
    duration_months = 3

    def can_possibly_start(self) -> bool:
        return True

    def _execute(self) -> None:
        return

    def can_start(self) -> tuple[bool, str]:
        region = getattr(getattr(self.avatar, "tile", None), "region", None)
        if not isinstance(region, CityRegion):
            return False, t("Must be in a City to govern.")
        return True, ""

    def start(self) -> Event:
        region = self.avatar.tile.region
        return Event(
            self.world.month_stamp,
            t("{avatar} begins governing in {city}.", avatar=self.avatar.name, city=region.name),
            related_avatars=[self.avatar.id],
        )

    async def finish(self) -> list[Event]:
        events: list[Event] = []
        region = getattr(getattr(self.avatar, "tile", None), "region", None)
        city_name = region.name if isinstance(region, CityRegion) else t("Unknown")

        reputation_gain = calculate_governance_reputation_gain(self.avatar, getattr(self.world, "dynasty", None))
        salary = get_governance_salary(getattr(self.avatar, "official_rank", None))

        old_rank = str(getattr(self.avatar, "official_rank", "NONE") or "NONE")
        apply_official_reputation_delta(self.avatar, reputation_gain)
        self.avatar.magic_stone = self.avatar.magic_stone + salary
        self.avatar.last_governance_month = int(self.world.month_stamp)
        _resolved_old_rank, new_rank = resolve_rank_changes(self.avatar)

        events.append(
            Event(
                self.world.month_stamp,
                t(
                    "{avatar} governed effectively in {city}. Court reputation +{reputation}, salary +{salary} spirit stones.",
                    avatar=self.avatar.name,
                    city=city_name,
                    reputation=reputation_gain,
                    salary=salary,
                ),
                related_avatars=[self.avatar.id],
            )
        )

        if new_rank != old_rank:
            events.append(
                Event(
                    self.world.month_stamp,
                    t(
                        "{avatar} was promoted from {old_rank} to {new_rank} for distinguished governance.",
                        avatar=self.avatar.name,
                        old_rank=get_official_rank_name(old_rank),
                        new_rank=get_official_rank_name(new_rank),
                    ),
                    related_avatars=[self.avatar.id],
                    is_major=True,
                )
            )
            self.avatar.recalc_effects()

        story_event = await StoryEventService.maybe_create_story(
            kind=StoryEventKind.DAILY_SOCIAL,
            month_stamp=self.world.month_stamp,
            start_text=t("{avatar} was governing in {city}.", avatar=self.avatar.name, city=city_name),
            result_text=t(
                "{avatar} completed a round of governance, and new ripples spread through court and countryside.",
                avatar=self.avatar.name,
            ),
            actors=[self.avatar],
            related_avatar_ids=[self.avatar.id],
            prompt=t("Focus on governance affairs, malevolent incidents, local strongmen, and political rivals creating obstacles."),
        )
        if story_event is not None:
            events.append(story_event)

        return events
