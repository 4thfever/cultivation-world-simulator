from types import SimpleNamespace

from src.server.loop_runtime import (
    build_auto_save_toast,
    build_avatar_updates,
    build_tick_state,
    should_trigger_auto_save,
)


def test_build_avatar_updates_includes_birth_death_and_position_deltas():
    born_avatar = SimpleNamespace(
        id="born-1",
        name="Newborn",
        pos_x=3,
        pos_y=4,
        gender=SimpleNamespace(value="male"),
        cultivation_progress=SimpleNamespace(realm=SimpleNamespace(value="QI_REFINEMENT")),
        current_action_name="行走",
    )
    dead_avatar = SimpleNamespace(id="dead-1", name="Ancestor")
    living_avatar = SimpleNamespace(
        id="live-1",
        pos_x=7,
        pos_y=8,
        gender=SimpleNamespace(value="female"),
        cultivation_progress=SimpleNamespace(realm=SimpleNamespace(value="FOUNDATION_ESTABLISHMENT")),
    )

    avatar_manager = SimpleNamespace(
        avatars={"born-1": born_avatar},
        pop_newly_born=lambda: ["born-1"],
        pop_newly_dead=lambda: ["dead-1"],
        get_avatar=lambda avatar_id: dead_avatar if avatar_id == "dead-1" else None,
        get_living_avatars=lambda: [born_avatar, living_avatar],
    )
    world = SimpleNamespace(avatar_manager=avatar_manager)

    updates = build_avatar_updates(
        world=world,
        resolve_avatar_pic_id=lambda avatar: 99 if avatar.id == "born-1" else 1,
        resolve_avatar_action_emoji=lambda avatar: "🚶" if avatar.id == "born-1" else "✨",
    )

    assert updates[0]["id"] == "born-1"
    assert updates[0]["pic_id"] == 99
    assert updates[0]["realm"] == "QI_REFINEMENT"
    assert updates[0]["action_emoji"] == "🚶"
    assert updates[1] == {
        "id": "dead-1",
        "name": "Ancestor",
        "is_dead": True,
        "action": "已故",
    }
    assert updates[2] == {
        "id": "live-1",
        "x": 7,
        "y": 8,
        "gender": "female",
        "pic_id": 1,
        "realm": "FOUNDATION_ESTABLISHMENT",
        "action_emoji": "✨",
    }


def test_build_tick_state_uses_serializer_hooks():
    world = SimpleNamespace(
        month_stamp=SimpleNamespace(
            get_year=lambda: 120,
            get_month=lambda: SimpleNamespace(value=6),
        ),
        current_phenomenon=SimpleNamespace(id=1),
    )

    state = build_tick_state(
        world=world,
        events=["evt"],
        avatar_updates=[{"id": "a"}],
        serialize_events_for_client=lambda events: [{"count": len(events)}],
        serialize_phenomenon=lambda phenomenon: {"id": phenomenon.id},
        serialize_active_domains=lambda _world: [{"id": "domain"}],
    )

    assert state == {
        "type": "tick",
        "year": 120,
        "month": 6,
        "events": [{"count": 1}],
        "avatars": [{"id": "a"}],
        "phenomenon": {"id": 1},
        "active_domains": [{"id": "domain"}],
    }


def test_should_trigger_auto_save_respects_decade_boundary(monkeypatch):
    class DummySettingsService:
        def get_settings(self):
            return SimpleNamespace(simulation=SimpleNamespace(auto_save_enabled=True))

    monkeypatch.setattr("src.server.loop_runtime.get_settings_service", lambda: DummySettingsService())

    world = SimpleNamespace(
        start_year=100,
        month_stamp=SimpleNamespace(
            get_year=lambda: 110,
            get_month=lambda: SimpleNamespace(value=1),
        ),
    )

    assert should_trigger_auto_save(world=world) == (True, 110, 1)


def test_build_auto_save_toast_has_stable_contract():
    toast = build_auto_save_toast()

    assert toast["type"] == "toast"
    assert toast["level"] == "info"
    assert isinstance(toast["message"], str)
