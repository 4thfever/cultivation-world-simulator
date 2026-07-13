from __future__ import annotations

from src.classes.action import DefineAction, ActualActionMixin, Move
from src.classes.action.move_helper import clamp_manhattan_with_diagonal_priority
from src.classes.action.param_options import ParamOptionSource
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.event import Event
from src.i18n import t


class MoveToPOI(DefineAction, ActualActionMixin):
    ACTION_NAME_ID = "move_to_poi_action_name"
    DESC_ID = "move_to_poi_description"
    REQUIREMENTS_ID = "move_to_poi_requirements"

    EMOJI = "🏃"
    PARAMS = {"poi_id": "poi_id"}
    PARAM_OPTION_SOURCES = {"poi_id": ParamOptionSource.KNOWN_POI_ID}

    def _get_poi(self, poi_id: str):
        return getattr(self.world, "poi_manager", None).get(str(poi_id)) if getattr(self.world, "poi_manager", None) else None

    def _execute(self, poi_id: str) -> None:
        poi = self._get_poi(poi_id)
        if poi is None:
            return
        cur_loc = (self.avatar.pos_x, self.avatar.pos_y)
        raw_dx = int(poi.x) - cur_loc[0]
        raw_dy = int(poi.y) - cur_loc[1]
        step = getattr(self.avatar, "move_step_length", 1)
        dx, dy = clamp_manhattan_with_diagonal_priority(raw_dx, raw_dy, step)
        Move(self.avatar, self.world).execute(dx, dy)

    def can_start(self, poi_id: str) -> tuple[bool, str]:
        poi = self._get_poi(poi_id)
        if poi is None:
            return False, t("Cannot resolve point of interest: {poi}", poi=poi_id)
        if poi.is_expired(int(self.world.month_stamp)):
            return False, t("Point of interest has expired")
        if not poi.is_known_by(self.avatar):
            return False, t("Point of interest is unknown")
        if not self.world.map.is_in_bounds(int(poi.x), int(poi.y)):
            return False, t("Point of interest is out of bounds")
        return True, ""

    def start(self, poi_id: str) -> Event:
        poi = self._get_poi(poi_id)
        poi_name = poi.name if poi is not None else str(poi_id)
        return Event(
            self.world.month_stamp,
            t("{avatar} begins moving toward {poi}", avatar=self.avatar.name, poi=poi_name),
            related_avatars=[self.avatar.id],
        )

    def step(self, poi_id: str) -> ActionResult:
        self.execute(poi_id=poi_id)
        poi = self._get_poi(poi_id)
        if poi is None:
            return ActionResult(status=ActionStatus.FAILED, events=[])
        done = self.avatar.pos_x == int(poi.x) and self.avatar.pos_y == int(poi.y)
        return ActionResult(status=(ActionStatus.COMPLETED if done else ActionStatus.RUNNING), events=[])

    async def finish(self, poi_id: str) -> list[Event]:
        return []

    def can_possibly_start(self) -> bool:
        manager = getattr(self.world, "poi_manager", None)
        if not manager:
            return False
        current_month = int(getattr(self.world, "month_stamp", 0))
        return any(not poi.is_expired(current_month) for poi in manager.get_known_by(self.avatar))
