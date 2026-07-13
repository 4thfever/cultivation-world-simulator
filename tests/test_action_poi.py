from __future__ import annotations

import pytest

from src.classes.action.dig_grave import DigGrave
from src.classes.action.move_to_poi import MoveToPOI
from src.classes.action.param_options import build_param_options
from src.classes.poi import GravePOI
from src.systems.cultivation import Realm
from src.systems.single_choice import ItemDisposition, ItemExchangeKind, ItemExchangeOutcome
from src.systems.single_choice.models import ChoiceSource, SingleChoiceDecision
from src.classes.items.weapon import weapons_by_id


def _make_grave(base_world, dummy_avatar, *, x=2, y=0, weapon=None) -> GravePOI:
    grave = GravePOI.from_avatar(dummy_avatar, int(base_world.month_stamp))
    grave.x = x
    grave.y = y
    grave.weapon_payload = {
        "kind": "weapon",
        "item_id": int(weapon.id),
        "name": weapon.name,
        "realm": weapon.realm.value,
        "special_data": {},
    } if weapon is not None else None
    grave.auxiliary_payload = None
    base_world.poi_manager.add(grave)
    grave.discover(dummy_avatar)
    return grave


def test_known_poi_param_options_are_executable(base_world, dummy_avatar, mock_item_data):
    dummy_avatar.world = base_world
    base_world.avatar_manager.register_avatar(dummy_avatar)
    grave = _make_grave(base_world, dummy_avatar, weapon=mock_item_data["obj_weapon"])

    options = build_param_options(MoveToPOI, dummy_avatar)["poi_id"]
    grave_options = build_param_options(DigGrave, dummy_avatar)["poi_id"]

    assert options[0]["value"] == grave.id
    assert grave_options[0]["value"] == grave.id
    can_move, reason = MoveToPOI(dummy_avatar, base_world).can_start(options[0]["value"])
    assert can_move is True, reason

    dummy_avatar.pos_x = grave.x
    dummy_avatar.pos_y = grave.y
    can_dig, reason = DigGrave(dummy_avatar, base_world).can_start(grave_options[0]["value"])
    assert can_dig is True, reason


def test_move_to_poi_moves_until_exact_point(base_world, dummy_avatar, mock_item_data):
    dummy_avatar.world = base_world
    dummy_avatar.pos_x = 0
    dummy_avatar.pos_y = 0
    dummy_avatar.tile = base_world.map.get_tile(0, 0)
    grave = _make_grave(base_world, dummy_avatar, x=3, y=0, weapon=mock_item_data["obj_weapon"])

    action = MoveToPOI(dummy_avatar, base_world)

    first = action.step(grave.id)
    assert first.status.value == "running"
    assert (dummy_avatar.pos_x, dummy_avatar.pos_y) != (grave.x, grave.y)

    second = action.step(grave.id)
    assert second.status.value == "completed"
    assert (dummy_avatar.pos_x, dummy_avatar.pos_y) == (3, 0)


@pytest.mark.asyncio
async def test_dig_grave_success_loots_item_and_removes_payload(monkeypatch, base_world, dummy_avatar, mock_item_data):
    weapon = weapons_by_id[1001]
    dummy_avatar.world = base_world
    dummy_avatar.weapon = None
    dummy_avatar.pos_x = 0
    dummy_avatar.pos_y = 0
    grave = _make_grave(base_world, dummy_avatar, x=0, y=0, weapon=weapon)

    monkeypatch.setattr("src.classes.action.dig_grave.random.random", lambda: 0.0)

    action = DigGrave(dummy_avatar, base_world)
    result = action.step(poi_id=grave.id)
    events = await action.finish(poi_id=grave.id)

    assert result.status.value == "completed"
    assert dummy_avatar.luck_base == pytest.approx(-0.2)
    assert dummy_avatar.weapon.id == weapon.id
    assert grave.weapon_payload is None
    assert grave.get_detail_payload(base_world)["grave_goods"]["weapon"] is None
    assert events and events[0].is_major is True


@pytest.mark.asyncio
async def test_dig_grave_does_not_mark_rejected_item_looted(monkeypatch, base_world, dummy_avatar, mock_item_data):
    weapon = weapons_by_id[1001]
    dummy_avatar.world = base_world
    dummy_avatar.weapon = mock_item_data["obj_weapon"]
    dummy_avatar.pos_x = 0
    dummy_avatar.pos_y = 0
    grave = _make_grave(base_world, dummy_avatar, x=0, y=0, weapon=weapon)

    monkeypatch.setattr("src.classes.action.dig_grave.random.random", lambda: 0.0)

    async def reject_exchange(request):
        return ItemExchangeOutcome(
            decision=SingleChoiceDecision(
                selected_key="REJECT",
                thinking="",
                source=ChoiceSource.FALLBACK,
                raw_response=None,
                used_fallback=True,
            ),
            result_text="rejected",
            kind=ItemExchangeKind.WEAPON,
            accepted=False,
            action=ItemDisposition.ABANDONED_NEW,
            current_item_before=dummy_avatar.weapon,
            current_item_after=dummy_avatar.weapon,
            sold_price=None,
            new_item=request.new_item,
        )

    monkeypatch.setattr("src.classes.action.dig_grave.resolve_item_exchange", reject_exchange)

    action = DigGrave(dummy_avatar, base_world)
    action.step(poi_id=grave.id)
    await action.finish(poi_id=grave.id)

    assert grave.weapon_payload is not None
