from __future__ import annotations

from src.classes.death import handle_death
from src.classes.death_reason import DeathReason, DeathType
from src.classes.poi import GravePOI
from src.systems.time import Month, Year, create_month_stamp


def test_death_creates_grave_poi_with_equipment_snapshot(base_world, dummy_avatar, mock_item_data):
    dummy_avatar.weapon = mock_item_data["obj_weapon"]
    dummy_avatar.auxiliary = mock_item_data["obj_auxiliary"]
    dummy_avatar.technique = object()
    dummy_avatar.pos_x = 2
    dummy_avatar.pos_y = 3
    dummy_avatar.tile = base_world.map.get_tile(2, 3)
    base_world.avatar_manager.register_avatar(dummy_avatar)

    handle_death(base_world, dummy_avatar, DeathReason(DeathType.SERIOUS_INJURY))

    graves = base_world.poi_manager.get_all_active(int(base_world.month_stamp))
    assert len(graves) == 1
    grave = graves[0]
    assert isinstance(grave, GravePOI)
    assert grave.x == 2
    assert grave.y == 3
    assert grave.expires_month == int(base_world.month_stamp) + 50 * 12
    assert grave.weapon_payload == {
        "kind": "weapon",
        "item_id": mock_item_data["obj_weapon"].id,
        "name": mock_item_data["obj_weapon"].name,
        "realm": mock_item_data["obj_weapon"].realm.value,
        "special_data": {},
    }
    assert grave.auxiliary_payload["kind"] == "auxiliary"
    assert not hasattr(grave, "technique_payload")


def test_grave_poi_save_load_and_cleanup(base_world, dummy_avatar, mock_item_data):
    dummy_avatar.weapon = mock_item_data["obj_weapon"]
    base_world.avatar_manager.register_avatar(dummy_avatar)
    handle_death(base_world, dummy_avatar, "test death")
    grave = next(iter(base_world.poi_manager.pois.values()))
    grave.discover(dummy_avatar)

    saved = base_world.poi_manager.to_save_list()
    base_world.poi_manager.load_from_list(saved)
    loaded = next(iter(base_world.poi_manager.pois.values()))

    assert isinstance(loaded, GravePOI)
    assert loaded.id == grave.id
    assert loaded.weapon_payload["item_id"] == mock_item_data["obj_weapon"].id
    assert loaded.is_known_by(dummy_avatar)

    before_expiry = create_month_stamp(Year(50), Month.DECEMBER)
    assert base_world.poi_manager.cleanup_expired(int(before_expiry)) == 0
    assert loaded.id in base_world.poi_manager.pois

    at_expiry = create_month_stamp(Year(51), Month.JANUARY)
    assert base_world.poi_manager.cleanup_expired(int(at_expiry)) == 1
    assert loaded.id not in base_world.poi_manager.pois


def test_deceased_records_cleanup_uses_fifty_year_threshold(base_world, dummy_avatar):
    base_world.avatar_manager.register_avatar(dummy_avatar)
    handle_death(base_world, dummy_avatar, "test death")

    before_expiry = create_month_stamp(Year(50), Month.DECEMBER)
    assert base_world.deceased_manager.cleanup_expired_records(before_expiry, threshold_years=50) == 0
    assert base_world.deceased_manager.get_record(dummy_avatar.id) is not None

    at_expiry = create_month_stamp(Year(51), Month.JANUARY)
    assert base_world.deceased_manager.cleanup_expired_records(at_expiry, threshold_years=50) == 1
    assert base_world.deceased_manager.get_record(dummy_avatar.id) is None
