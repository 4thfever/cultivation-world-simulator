from __future__ import annotations

from typing import TYPE_CHECKING

from src.classes.action import InstantAction
from src.classes.action.param_options import ParamOptionSource
from src.classes.action.targeting_mixin import TargetingMixin
from src.classes.event import Event
from src.i18n import t
from src.systems.gu import (
    INFLICT_GU_ACTION,
    apply_gu_effect,
    build_gu_effect,
    compute_gu_success_rate,
    get_gu_type_name,
    has_gu_permission,
    is_gu_tool,
    is_valid_gu_type,
    normalize_gu_type,
    roll_gu_failure_detected,
)

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


class InflictGu(InstantAction, TargetingMixin):
    """下蛊：持有蛊具时，对目标施加一种按月结算的蛊。"""

    ACTION_NAME_ID = "inflict_gu_action_name"
    DESC_ID = "inflict_gu_description"
    REQUIREMENTS_ID = "inflict_gu_requirements"

    EMOJI = "🪲"
    PARAMS = {
        "avatar_name": "AvatarName",
        "gu_type": "GuType",
    }
    PARAM_OPTION_SOURCES = {
        "avatar_name": ParamOptionSource.OBSERVABLE_AVATAR_NAME,
        "gu_type": ParamOptionSource.AVAILABLE_GU_TYPE,
    }

    def __init__(self, avatar: "Avatar", world):
        super().__init__(avatar, world)
        self._last_target: "Avatar | None" = None
        self._last_gu_type = ""
        self._last_success = False
        self._last_detected = False
        self._last_rate = 0.0

    def can_possibly_start(self) -> bool:
        return has_gu_permission(self.avatar)

    def can_start(self, avatar_name: str, gu_type: str) -> tuple[bool, str]:
        if not has_gu_permission(self.avatar):
            return False, t("Missing Gu tool")
        if not is_gu_tool(getattr(self.avatar, "auxiliary", None)):
            return False, t("Missing Gu tool")
        if not is_valid_gu_type(gu_type):
            return False, t("Invalid Gu type")

        target, ok, reason = self.validate_target_avatar(avatar_name)
        if not ok or target is None:
            return False, reason
        if target is self.avatar:
            return False, t("Cannot inflict Gu on self")
        return True, ""

    def start(self, avatar_name: str, gu_type: str) -> Event:
        target = self.find_avatar_by_name(avatar_name)
        target_name = target.name if target is not None else str(avatar_name)
        normalized = normalize_gu_type(gu_type)
        content = t(
            "{caster} attempts to inflict {gu_name} on {target}.",
            caster=self.avatar.name,
            gu_name=get_gu_type_name(normalized),
            target=target_name,
        )
        related = [self.avatar.id]
        if target is not None:
            related.append(target.id)
        self._start_event_content = content
        return Event(self.world.month_stamp, content, related_avatars=related)

    def _execute(self, avatar_name: str, gu_type: str) -> None:
        target = self.find_avatar_by_name(avatar_name)
        self._last_target = target
        self._last_gu_type = normalize_gu_type(gu_type)
        self._last_success = False
        self._last_detected = False
        self._last_rate = 0.0

        if target is None or target is self.avatar or target.is_dead:
            return
        if not is_valid_gu_type(self._last_gu_type):
            return

        self._last_rate = compute_gu_success_rate(self.avatar, target)
        import random

        self._last_success = random.random() < self._last_rate
        if self._last_success:
            apply_gu_effect(target, build_gu_effect(self.avatar, self._last_gu_type))
            return

        self._last_detected = roll_gu_failure_detected()
        if self._last_detected:
            from src.classes.relation.relations import add_friendliness

            current_month = int(self.world.month_stamp)
            add_friendliness(target, self.avatar, -25, current_month=current_month)

    async def finish(self, avatar_name: str, gu_type: str) -> list[Event]:
        target = self._last_target or self.find_avatar_by_name(avatar_name)
        if target is None:
            return []

        gu_name = get_gu_type_name(self._last_gu_type or gu_type)
        if self._last_success:
            content = t(
                "{caster} successfully inflicted {gu_name} on {target}.",
                caster=self.avatar.name,
                gu_name=gu_name,
                target=target.name,
            )
        elif self._last_detected:
            content = t(
                "{caster} failed to inflict {gu_name} on {target}; the attempt was detected.",
                caster=self.avatar.name,
                gu_name=gu_name,
                target=target.name,
            )
        else:
            content = t(
                "{caster} failed to inflict {gu_name} on {target}.",
                caster=self.avatar.name,
                gu_name=gu_name,
                target=target.name,
            )

        return [
            Event(
                self.world.month_stamp,
                content,
                related_avatars=[self.avatar.id, target.id],
            )
        ]
