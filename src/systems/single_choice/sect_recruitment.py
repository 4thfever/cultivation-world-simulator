from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.i18n import t
from src.utils.config import CONFIG

from .models import (
    ChoiceSource,
    FallbackMode,
    FallbackPolicy,
    SingleChoiceDecision,
    SingleChoiceOption,
    SingleChoiceOutcome,
    SingleChoiceRequest,
)
from .scenario import SingleChoiceScenario

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.core.sect import Sect


@dataclass(slots=True)
class SectRecruitmentRequest:
    sect: "Sect"
    avatar: "Avatar"
    cost: int
    fallback_policy: FallbackPolicy = field(
        default_factory=lambda: FallbackPolicy(FallbackMode.PREFERRED_KEY, preferred_key="REJECT")
    )


@dataclass(slots=True)
class SectRecruitmentOutcome(SingleChoiceOutcome):
    accepted: bool
    sect_id: int
    avatar_id: str


class SectRecruitmentScenario(SingleChoiceScenario[SectRecruitmentOutcome]):
    def __init__(self, request: SectRecruitmentRequest):
        self.request = request

    def build_request(self) -> SingleChoiceRequest:
        sect = self.request.sect
        avatar = self.request.avatar
        rule_desc = str(getattr(sect, "rule_desc", "") or t("New disciples must abide by the sect rules."))
        situation = (
            t("{sect_name} has extended a recruitment invitation to you.", sect_name=sect.name)
            + "\n"
            + t("Sect overview: {sect_info}", sect_info=sect.get_detailed_info())
            + "\n"
            + t("Sect rules: {rule_desc}", rule_desc=rule_desc)
            + "\n"
            + t("If you accept, you will become a disciple of this sect.")
        )
        options = [
            SingleChoiceOption(
                key="ACCEPT",
                title=t("Accept invitation"),
                description=t("Join {sect_name} and become one of its disciples.", sect_name=sect.name),
            ),
            SingleChoiceOption(
                key="REJECT",
                title=t("Decline invitation"),
                description=t("Remain an independent cultivator."),
            ),
        ]
        return SingleChoiceRequest(
            task_name="single_choice",
            template_path=CONFIG.paths.templates / "single_choice.txt",
            avatar=avatar,
            situation=situation,
            options=options,
            fallback_policy=self.request.fallback_policy,
            context={
                "sect_name": sect.name,
                "sect_rule_desc": rule_desc,
            },
        )

    async def apply_decision(self, decision: SingleChoiceDecision) -> SectRecruitmentOutcome:
        accepted = decision.selected_key == "ACCEPT"
        sect = self.request.sect
        avatar = self.request.avatar
        result_text = (
            t("{avatar_name} accepted {sect_name}'s invitation.", avatar_name=avatar.name, sect_name=sect.name)
            if accepted
            else t("{avatar_name} declined {sect_name}'s invitation.", avatar_name=avatar.name, sect_name=sect.name)
        )
        return SectRecruitmentOutcome(
            decision=decision,
            result_text=result_text,
            accepted=accepted,
            sect_id=int(getattr(sect, "id", 0)),
            avatar_id=str(getattr(avatar, "id", "")),
        )


async def resolve_sect_recruitment(request: SectRecruitmentRequest) -> SectRecruitmentOutcome:
    from .engine import resolve_single_choice

    scenario = SectRecruitmentScenario(request)
    return await resolve_single_choice(scenario)
