from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


class ChoiceSource(Enum):
    LLM = "llm"
    FALLBACK = "fallback"


class FallbackMode(Enum):
    FIRST_OPTION = "first_option"
    PREFERRED_KEY = "preferred_key"
    RAISE = "raise"


@dataclass(slots=True)
class FallbackPolicy:
    mode: FallbackMode
    preferred_key: str | None = None


@dataclass(slots=True)
class SingleChoiceOption:
    key: str
    title: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SingleChoiceRequest:
    task_name: str
    template_path: Path
    avatar: "Avatar"
    situation: str
    options: list[SingleChoiceOption]
    fallback_policy: FallbackPolicy
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SingleChoiceDecision:
    selected_key: str
    thinking: str
    source: ChoiceSource
    raw_response: str | dict[str, Any] | None
    used_fallback: bool
    fallback_reason: str | None = None


@dataclass(slots=True)
class SingleChoiceOutcome:
    decision: SingleChoiceDecision
    result_text: str
