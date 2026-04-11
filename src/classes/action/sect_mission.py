from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from src.classes.action import TimedAction
from src.classes.core.sect import Sect
from src.classes.death import handle_death
from src.classes.death_reason import DeathReason, DeathType
from src.classes.environment.sect_region import SectRegion
from src.classes.event import Event
from src.classes.story_event_service import StoryEventKind, StoryEventService
from src.i18n import t
from src.systems.cultivation import Realm
from src.utils.df import game_configs, get_float, get_int, get_list_str, get_str


REALM_SUFFIX_MAP: dict[Realm, str] = {
    Realm.Qi_Refinement: "qi",
    Realm.Foundation_Establishment: "foundation",
    Realm.Core_Formation: "core",
    Realm.Nascent_Soul: "nascent",
}


@dataclass(frozen=True)
class SectTaskDefinition:
    id: str
    title: str
    category: str
    issuer_type: str
    min_duration: int
    max_duration: int
    allowed_realms: tuple[Realm, ...]
    base_success: dict[Realm, float]
    reward_stone_per_month: dict[Realm, int]
    reward_contribution_per_month: dict[Realm, int]
    fail_damage_ratio: dict[Realm, float]
    weight: float


def _load_sect_task_definitions() -> list[SectTaskDefinition]:
    rows = game_configs.get("sect_task", [])
    definitions: list[SectTaskDefinition] = []
    for row in rows:
        task_id = get_str(row, "id")
        raw_title = get_str(row, "title")
        if not task_id or not raw_title:
            continue
        title = t(f"sect_task_title_{task_id}", default=raw_title)

        allowed_realms: list[Realm] = []
        for raw_realm in get_list_str(row, "allowed_realms"):
            try:
                allowed_realms.append(Realm.from_str(raw_realm))
            except Exception:
                continue
        if not allowed_realms:
            continue

        base_success: dict[Realm, float] = {}
        reward_stone_per_month: dict[Realm, int] = {}
        reward_contribution_per_month: dict[Realm, int] = {}
        fail_damage_ratio: dict[Realm, float] = {}
        for realm, suffix in REALM_SUFFIX_MAP.items():
            base_success[realm] = max(0.0, min(1.0, get_float(row, f"base_success_{suffix}", 0.0)))
            reward_stone_per_month[realm] = max(0, get_int(row, f"reward_stone_per_month_{suffix}", 0))
            reward_contribution_per_month[realm] = max(
                0,
                get_int(row, f"reward_contribution_per_month_{suffix}", 0),
            )
            fail_damage_ratio[realm] = max(0.0, get_float(row, f"fail_damage_ratio_{suffix}", 0.0))

        definitions.append(
            SectTaskDefinition(
                id=task_id,
                title=title,
                category=get_str(row, "category"),
                issuer_type=get_str(row, "issuer_type", "both") or "both",
                min_duration=max(1, get_int(row, "min_duration", 3)),
                max_duration=max(1, get_int(row, "max_duration", 9)),
                allowed_realms=tuple(allowed_realms),
                base_success=base_success,
                reward_stone_per_month=reward_stone_per_month,
                reward_contribution_per_month=reward_contribution_per_month,
                fail_damage_ratio=fail_damage_ratio,
                weight=max(0.01, get_float(row, "weight", 1.0)),
            )
        )
    return definitions


SECT_TASK_DEFINITIONS: list[SectTaskDefinition] = _load_sect_task_definitions()
SECT_TASKS_BY_ID: dict[str, SectTaskDefinition] = {task.id: task for task in SECT_TASK_DEFINITIONS}


class SectMission(TimedAction):
    ACTION_NAME_ID = "sect_mission_action_name"
    DESC_ID = "sect_mission_description"
    REQUIREMENTS_ID = "sect_mission_requirements"

    EMOJI = "📜"
    PARAMS = {}
    duration_months = 3

    def __init__(self, avatar, world):
        super().__init__(avatar, world)
        self.task_id: Optional[str] = None
        self.task_title: str = ""
        self.task_category: str = ""
        self.issuer_type: str = "headquarter"
        self.issuer_avatar_id: Optional[str] = None
        self.issuer_name: str = ""
        self.base_success_rate: float = 0.0
        self.reward_magic_stones: int = 0
        self.reward_contribution: int = 0
        self.fail_damage_ratio: float = 0.0
        self.fail_damage: int = 0
        self.was_successful: Optional[bool] = None
        self._start_event_content: str = ""

    def get_save_data(self) -> dict:
        data = super().get_save_data()
        data.update(
            {
                "task_id": self.task_id,
                "task_title": self.task_title,
                "task_category": self.task_category,
                "issuer_type": self.issuer_type,
                "issuer_avatar_id": self.issuer_avatar_id,
                "issuer_name": self.issuer_name,
                "base_success_rate": self.base_success_rate,
                "reward_magic_stones": self.reward_magic_stones,
                "reward_contribution": self.reward_contribution,
                "fail_damage_ratio": self.fail_damage_ratio,
                "fail_damage": self.fail_damage,
                "was_successful": self.was_successful,
                "start_event_content": self._start_event_content,
                "duration_months": self.duration_months,
            }
        )
        return data

    def load_save_data(self, data: dict) -> None:
        super().load_save_data(data)
        self.task_id = data.get("task_id")
        self.task_title = str(data.get("task_title", "") or "")
        self.task_category = str(data.get("task_category", "") or "")
        self.issuer_type = str(data.get("issuer_type", "headquarter") or "headquarter")
        self.issuer_avatar_id = data.get("issuer_avatar_id")
        self.issuer_name = str(data.get("issuer_name", "") or "")
        self.base_success_rate = float(data.get("base_success_rate", 0.0) or 0.0)
        self.reward_magic_stones = int(data.get("reward_magic_stones", 0) or 0)
        self.reward_contribution = int(data.get("reward_contribution", 0) or 0)
        self.fail_damage_ratio = float(data.get("fail_damage_ratio", 0.0) or 0.0)
        self.fail_damage = int(data.get("fail_damage", 0) or 0)
        self.was_successful = data.get("was_successful")
        self._start_event_content = str(data.get("start_event_content", "") or "")
        self.duration_months = int(data.get("duration_months", self.duration_months) or self.duration_months)

    def can_possibly_start(self) -> bool:
        return getattr(self.avatar, "sect", None) is not None and bool(self._get_candidate_tasks())

    def can_start(self) -> tuple[bool, str]:
        sect = getattr(self.avatar, "sect", None)
        if sect is None:
            return False, t("sect_mission_members_only")

        region = getattr(getattr(self.avatar, "tile", None), "region", None)
        if not isinstance(region, SectRegion) or int(getattr(region, "sect_id", -1)) != int(sect.id):
            return False, t("sect_mission_hq_only")

        if not self._get_candidate_tasks():
            return False, t("sect_mission_no_task_available")

        return True, ""

    def start(self) -> Event:
        task = self._choose_task_definition()
        if task is None:
            raise ValueError("No sect mission task available for current realm")

        self._apply_task_definition(task)
        event_content = self._build_start_event_content()
        self._start_event_content = event_content

        related_avatar_ids = [self.avatar.id]
        if self.issuer_avatar_id:
            related_avatar_ids.append(self.issuer_avatar_id)

        return Event(
            month_stamp=self.world.month_stamp,
            content=event_content,
            related_avatars=related_avatar_ids,
            related_sects=[int(self.avatar.sect.id)],
            is_major=False,
        )

    def _execute(self) -> None:
        return

    async def finish(self) -> list[Event]:
        if not self.task_title or self.avatar.sect is None:
            return []

        events: list[Event] = []
        related_sect_ids = [int(self.avatar.sect.id)]
        related_avatar_ids = [self.avatar.id]
        if self.issuer_avatar_id:
            related_avatar_ids.append(self.issuer_avatar_id)

        success_rate = self.calc_success_rate()
        self.was_successful = random.random() < success_rate

        if self.was_successful:
            self.avatar.magic_stone += self.reward_magic_stones
            actual_contribution = self.avatar.add_sect_contribution(self.reward_contribution)
            result_text = t(
                "sect_mission_result_success",
                avatar=self.avatar.name,
                title=self.task_title,
                stones=self.reward_magic_stones,
                contribution=actual_contribution,
            )
            events.append(
                Event(
                    month_stamp=self.world.month_stamp,
                    content=result_text,
                    related_avatars=related_avatar_ids,
                    related_sects=related_sect_ids,
                    is_major=False,
                )
            )
            story_prompt = t("sect_mission_story_prompt_success")
        else:
            self.fail_damage = self._roll_fail_damage()
            self.avatar.hp.reduce(self.fail_damage)
            is_dead = self.avatar.hp.cur <= 0 and not self.avatar.is_dead
            result_text = t(
                "sect_mission_result_fail",
                avatar=self.avatar.name,
                title=self.task_title,
                damage=self.fail_damage,
                current=max(0, self.avatar.hp.cur),
                max=self.avatar.hp.max,
            )
            if is_dead:
                handle_death(self.world, self.avatar, DeathReason(DeathType.SERIOUS_INJURY))
                result_text += t("sect_mission_result_fail_death_append")
            events.append(
                Event(
                    month_stamp=self.world.month_stamp,
                    content=result_text,
                    related_avatars=related_avatar_ids,
                    related_sects=related_sect_ids,
                    is_major=False,
                )
            )
            story_prompt = t("sect_mission_story_prompt_fail")

        story_event = await StoryEventService.maybe_create_story(
            kind=StoryEventKind.SECT_MISSION,
            month_stamp=self.world.month_stamp,
            start_text=self._start_event_content,
            result_text=result_text,
            actors=[self.avatar, self._resolve_issuer_avatar()],
            related_avatar_ids=related_avatar_ids,
            prompt=story_prompt,
            allow_relation_changes=False,
        )
        if story_event is not None:
            story_event.related_sects = related_sect_ids
            events.append(story_event)

        return events

    def _get_candidate_tasks(self) -> list[SectTaskDefinition]:
        realm = getattr(getattr(self.avatar, "cultivation_progress", None), "realm", Realm.Qi_Refinement)
        return [task for task in SECT_TASK_DEFINITIONS if realm in task.allowed_realms]

    def _choose_task_definition(self) -> Optional[SectTaskDefinition]:
        candidates = self._get_candidate_tasks()
        if not candidates:
            return None
        weights = [task.weight for task in candidates]
        return random.choices(candidates, weights=weights, k=1)[0]

    def _apply_task_definition(self, task: SectTaskDefinition) -> None:
        realm = self.avatar.cultivation_progress.realm
        self.task_id = task.id
        self.task_title = task.title
        self.task_category = task.category
        self.duration_months = self._choose_duration(task.min_duration, task.max_duration)
        self.base_success_rate = float(task.base_success.get(realm, 0.0) or 0.0)
        self.reward_magic_stones = int(task.reward_stone_per_month.get(realm, 0) or 0) * self.duration_months
        self.reward_contribution = int(task.reward_contribution_per_month.get(realm, 0) or 0) * self.duration_months
        self.fail_damage_ratio = float(task.fail_damage_ratio.get(realm, 0.0) or 0.0)
        self.issuer_type, self.issuer_avatar_id, self.issuer_name = self._resolve_issuer(task)

    def _choose_duration(self, min_duration: int, max_duration: int) -> int:
        start = max(3, min_duration)
        end = max(start, min(9, max_duration))
        return random.choice(list(range(start, end + 1)))

    def _resolve_issuer(self, task: SectTaskDefinition) -> tuple[str, Optional[str], str]:
        sect = self.avatar.sect
        if sect is None:
            return "headquarter", None, ""

        issuer_type = task.issuer_type
        if issuer_type == "both":
            issuer_type = random.choice(["headquarter", "member_request"])

        if issuer_type == "member_request":
            candidate_members = [
                member
                for member in sect.members.values()
                if not getattr(member, "is_dead", False) and str(getattr(member, "id", "")) != str(self.avatar.id)
            ]
            if candidate_members:
                issuer = random.choice(candidate_members)
                return "member_request", str(issuer.id), str(issuer.name)

        return "headquarter", None, ""

    def _resolve_issuer_avatar(self):
        if not self.issuer_avatar_id:
            return None
        try:
            return self.world.avatar_manager.get_avatar(self.issuer_avatar_id)
        except Exception:
            return None

    def calc_success_rate(self) -> float:
        extra_rate = float(self.avatar.effects.get("extra_sect_mission_success_rate", 0.0) or 0.0)
        luck_bonus = max(-0.03, min(0.08, float(getattr(self.avatar, "luck", 0.0) or 0.0) * 0.002))
        return max(0.05, min(0.98, self.base_success_rate + extra_rate + luck_bonus))

    def _roll_fail_damage(self) -> int:
        low = max(0.9, 1.0 - 0.1)
        high = 1.0 + 0.1
        raw_damage = self.avatar.hp.max * self.fail_damage_ratio * random.uniform(low, high)
        return max(1, int(round(raw_damage)))

    def _build_start_event_content(self) -> str:
        if self.issuer_type == "member_request" and self.issuer_name:
            return t(
                "sect_mission_start_member_request",
                avatar=self.avatar.name,
                issuer=self.issuer_name,
                title=self.task_title,
                duration=self.duration_months,
            )
        return t(
            "sect_mission_start_headquarter",
            avatar=self.avatar.name,
            sect_name=self.avatar.sect.name if self.avatar.sect else "",
            title=self.task_title,
            duration=self.duration_months,
        )


__all__ = [
    "SectMission",
    "SectTaskDefinition",
    "SECT_TASK_DEFINITIONS",
    "SECT_TASKS_BY_ID",
]
