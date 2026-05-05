from __future__ import annotations

from src.i18n import t
from src.classes.action import TimedAction
from src.classes.event import Event


class Rest(TimedAction):
    ACTION_NAME_ID = "rest_action_name"
    DESC_ID = "rest_description"
    REQUIREMENTS_ID = "rest_requirements"

    EMOJI = "💤"
    PARAMS = {}

    duration_months = 1
    BASE_HP_RECOVERY_RATIO = 0.2

    def _execute(self) -> None:
        return

    def can_start(self) -> tuple[bool, str]:
        if getattr(self.avatar, "is_dead", False):
            return False, t("Dead avatars cannot rest.")
        return True, ""

    def start(self) -> Event:
        if getattr(getattr(self.avatar, "race", None), "id", "human") == "turtle":
            content = t("{avatar} withdraws into quiet turtle-breathing rest.", avatar=self.avatar.name)
        else:
            content = t("{avatar} begins resting.", avatar=self.avatar.name)
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    async def finish(self) -> list[Event]:
        hp_max = int(getattr(getattr(self.avatar, "hp", None), "max", 0) or 0)
        extra_recovery = float(self.avatar.effects.get("extra_rest_hp_recovery_rate", 0.0) or 0.0)
        recovery = max(1, int(hp_max * (self.BASE_HP_RECOVERY_RATIO + extra_recovery))) if hp_max > 0 else 0
        if recovery > 0 and hasattr(self.avatar.hp, "recover"):
            self.avatar.hp.recover(recovery)

        exp = int(self.avatar.effects.get("extra_rest_exp", 0) or 0)
        if exp > 0 and self.avatar.cultivation_progress.can_cultivate():
            self.avatar.cultivation_progress.add_exp(exp)

        if exp > 0:
            content = t("{avatar} finished resting, recovered {hp} HP and gained {exp} cultivation experience.", avatar=self.avatar.name, hp=recovery, exp=exp)
        else:
            content = t("{avatar} finished resting and recovered {hp} HP.", avatar=self.avatar.name, hp=recovery)
        return [Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])]
