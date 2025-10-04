from __future__ import annotations

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.battle import decide_battle


class Battle(InstantAction):
    COMMENT = "与目标进行对战，判定胜负"
    DOABLES_REQUIREMENTS = "任何时候都可以执行"
    PARAMS = {"avatar_name": "AvatarName"}

    def _get_target(self, avatar_name: str):
        for v in self.world.avatar_manager.avatars.values():
            if v.name == avatar_name:
                return v
        return None

    def _execute(self, avatar_name: str) -> None:
        target = self._get_target(avatar_name)
        if target is None:
            return
        winner, loser, damage = decide_battle(self.avatar, target)
        loser.hp.reduce(damage)
        self._last_result = (winner.name, loser.name)

    def can_start(self, avatar_name: str | None = None) -> bool:
        if avatar_name is None:
            return False
        return self._get_target(avatar_name) is not None

    def start(self, avatar_name: str) -> Event:
        target = self._get_target(avatar_name)
        target_name = target.name if target is not None else avatar_name
        return Event(self.world.month_stamp, f"{self.avatar.name} 对 {target_name} 发起战斗")

    # InstantAction 已实现 step 完成

    def finish(self, avatar_name: str) -> list[Event]:
        res = self._last_result
        if isinstance(res, tuple) and len(res) == 2:
            winner, loser = res
            return [Event(self.world.month_stamp, f"{winner} 战胜了 {loser}")]
        return []


