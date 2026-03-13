from __future__ import annotations

from typing import Protocol, TypeVar

from .models import SingleChoiceDecision, SingleChoiceRequest

OutcomeT = TypeVar("OutcomeT")


class SingleChoiceScenario(Protocol[OutcomeT]):
    def build_request(self) -> SingleChoiceRequest:
        ...

    async def apply_decision(self, decision: SingleChoiceDecision) -> OutcomeT:
        ...
