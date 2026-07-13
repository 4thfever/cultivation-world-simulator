from __future__ import annotations

import random

from src.classes.action import InstantAction
from src.classes.action.param_options import ParamOptionSource
from src.classes.action_runtime import ActionResult, ActionStatus
from src.classes.event import Event
from src.classes.poi import GravePOI, restore_grave_item
from src.i18n import t
from src.systems.cultivation import Realm
from src.systems.single_choice import (
    ItemDisposition,
    ItemExchangeKind,
    ItemExchangeRequest,
    RejectMode,
    resolve_item_exchange,
)

_REALM_RANK = {
    Realm.Qi_Refinement.value: 1,
    Realm.Foundation_Establishment.value: 2,
    Realm.Core_Formation.value: 3,
    Realm.Nascent_Soul.value: 4,
}


class DigGrave(InstantAction):
    ACTION_NAME_ID = "dig_grave_action_name"
    DESC_ID = "dig_grave_description"
    REQUIREMENTS_ID = "dig_grave_requirements"

    EMOJI = "⛏"
    PARAMS = {"poi_id": "poi_id"}
    PARAM_OPTION_SOURCES = {"poi_id": ParamOptionSource.KNOWN_GRAVE_POI_ID}
    IS_MAJOR = True

    LUCK_DELTA = -0.2

    def __init__(self, avatar, world):
        super().__init__(avatar, world)
        self._last_event: Event | None = None
        self._pending_payload: dict | None = None
        self._pending_item = None

    def _get_grave(self, poi_id: str) -> GravePOI | None:
        manager = getattr(self.world, "poi_manager", None)
        poi = manager.get(str(poi_id)) if manager is not None else None
        return poi if isinstance(poi, GravePOI) else None

    def _realm_delta(self, grave: GravePOI) -> int:
        digger_realm = getattr(getattr(self.avatar, "cultivation_progress", None), "realm", None)
        digger_rank = _REALM_RANK.get(getattr(digger_realm, "value", ""), 1)
        deceased_rank = _REALM_RANK.get(grave.realm_at_death, 1)
        return digger_rank - deceased_rank

    def _success_rate(self, grave: GravePOI) -> float:
        return max(0.05, min(0.85, 0.45 + self._realm_delta(grave) * 0.15))

    def _injury_rate(self, grave: GravePOI) -> float:
        return max(0.02, min(0.50, 0.10 - self._realm_delta(grave) * 0.05))

    def _pick_payload(self, grave: GravePOI) -> dict | None:
        payloads = grave.get_available_item_payloads()
        if not payloads:
            return None
        payloads.sort(key=lambda payload: _REALM_RANK.get(str(payload.get("realm", "")), 1), reverse=True)
        best_rank = _REALM_RANK.get(str(payloads[0].get("realm", "")), 1)
        best = [payload for payload in payloads if _REALM_RANK.get(str(payload.get("realm", "")), 1) == best_rank]
        return random.choice(best)

    def can_start(self, poi_id: str) -> tuple[bool, str]:
        grave = self._get_grave(poi_id)
        if grave is None:
            return False, t("Cannot resolve grave: {poi}", poi=poi_id)
        if grave.is_expired(int(self.world.month_stamp)):
            return False, t("Grave has expired")
        if not grave.is_known_by(self.avatar):
            return False, t("Grave is unknown")
        if self.avatar.pos_x != grave.x or self.avatar.pos_y != grave.y:
            return False, t("Must be at the grave to dig")
        return True, ""

    def _execute(self, poi_id: str) -> None:
        self._last_event = None
        self._pending_payload = None
        self._pending_item = None

        grave = self._get_grave(poi_id)
        if grave is None:
            return

        grave.dig_attempt_count += 1
        self.avatar.luck_base = float(getattr(self.avatar, "luck_base", 0.0) or 0.0) + self.LUCK_DELTA
        self.avatar.recalc_effects()

        payload = self._pick_payload(grave)
        if payload is None:
            self._last_event = Event(
                self.world.month_stamp,
                t("{avatar} dug at {grave}, but found no usable relics.", avatar=self.avatar.name, grave=grave.name),
                related_avatars=[self.avatar.id],
                is_major=False,
            )
            return

        if random.random() <= self._success_rate(grave):
            item = restore_grave_item(payload)
            if item is None:
                self._last_event = Event(
                    self.world.month_stamp,
                    t("{avatar} disturbed {grave}, but the relic inside had already decayed.", avatar=self.avatar.name, grave=grave.name),
                    related_avatars=[self.avatar.id],
                )
                return
            self._pending_payload = payload
            self._pending_item = item
            return

        content = t("{avatar} failed to dig up useful relics from {grave}.", avatar=self.avatar.name, grave=grave.name)
        if random.random() <= self._injury_rate(grave):
            damage = max(1, int(getattr(self.avatar.hp, "max", 100) * 0.12))
            self.avatar.hp.reduce(damage)
            content = t(
                "{avatar} triggered lingering grave restrictions at {grave} and was injured for {damage} HP.",
                avatar=self.avatar.name,
                grave=grave.name,
                damage=damage,
            )
        self._last_event = Event(self.world.month_stamp, content, related_avatars=[self.avatar.id], is_major=True)

    def step(self, **params) -> ActionResult:
        self._execute(**params)
        return ActionResult(status=ActionStatus.COMPLETED, events=[])

    async def finish(self, poi_id: str) -> list[Event]:
        if self._last_event is not None:
            return [self._last_event]
        if self._pending_payload is None or self._pending_item is None:
            return []

        grave = self._get_grave(poi_id)
        if grave is None:
            return []
        kind = ItemExchangeKind(self._pending_payload["kind"])
        item = self._pending_item
        outcome = await resolve_item_exchange(
            ItemExchangeRequest(
                avatar=self.avatar,
                new_item=item,
                kind=kind,
                scene_intro=t(
                    "{avatar} dug up {item} from {grave}.",
                    avatar=self.avatar.name,
                    item=item.name,
                    grave=grave.name,
                ),
                reject_mode=RejectMode.ABANDON_NEW,
                auto_accept_when_empty=True,
            )
        )
        accepted_actions = {ItemDisposition.AUTO_ACCEPTED, ItemDisposition.REPLACED_OLD}
        if outcome.accepted and outcome.action in accepted_actions:
            grave.mark_item_looted(self._pending_payload)
        return [
            Event(
                self.world.month_stamp,
                t("{avatar} dug up {item} from {grave}. {result}", avatar=self.avatar.name, item=item.name, grave=grave.name, result=outcome.result_text),
                related_avatars=[self.avatar.id],
                is_major=True,
            )
        ]

    def can_possibly_start(self) -> bool:
        manager = getattr(self.world, "poi_manager", None)
        if manager is None:
            return False
        current_month = int(getattr(self.world, "month_stamp", 0))
        for poi in manager.get_known_by(self.avatar, kind="grave"):
            if poi.is_expired(current_month):
                continue
            if poi.x == self.avatar.pos_x and poi.y == self.avatar.pos_y:
                return True
        return False
