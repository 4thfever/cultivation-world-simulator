from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

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
        rule_desc = str(getattr(sect, "rule_desc", "") or "入门后需守宗门戒律。")
        situation = (
            f"{sect.name} 向你发出招徕。\n"
            f"宗门简介：{sect.get_detailed_info()}\n"
            f"门规：{rule_desc}\n"
            f"若你答应加入，将成为该宗门弟子。"
        )
        options = [
            SingleChoiceOption(
                key="ACCEPT",
                title="接受招徕",
                description=f"加入{sect.name}，成为门下弟子。",
            ),
            SingleChoiceOption(
                key="REJECT",
                title="拒绝招徕",
                description="继续保持散修身份。",
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
            f"{avatar.name} 答应了 {sect.name} 的招徕。"
            if accepted
            else f"{avatar.name} 拒绝了 {sect.name} 的招徕。"
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
