from __future__ import annotations

from src.run.static_data_registry import build_static_game_data_registry
from src.server.assemblers.avatar_detail import build_avatar_detail
from src.server.assemblers.avatar_list import build_avatar_list_payload
from src.server.services.roleplay_state import RoleplayStatus, create_roleplay_session_dict
from src.sim.save.sections.registry import SAVE_SECTIONS
from src.sim.simulator_engine.phase_registry import get_simulation_phases


def test_save_sections_define_stable_top_level_payload_order():
    assert [section.key for section in SAVE_SECTIONS] == [
        "meta",
        "run_config",
        "custom_content",
        "world",
        "avatars",
        "events",
        "simulator",
    ]


def test_roleplay_session_model_exports_runtime_dict_shape():
    session = create_roleplay_session_dict()

    assert session["status"] == RoleplayStatus.INACTIVE.value
    assert session["controlled_avatar_id"] is None
    assert session["pending_request"] is None
    assert session["conversation_session"] is None
    assert session["interaction_history"] == []


def test_static_game_data_registry_covers_public_api_sources():
    registry = build_static_game_data_registry()

    assert isinstance(registry.sects_by_id, dict)
    assert isinstance(registry.races_by_id, dict)
    assert isinstance(registry.personas_by_id, dict)
    assert isinstance(registry.techniques_by_id, dict)
    assert isinstance(registry.weapons_by_id, dict)
    assert isinstance(registry.auxiliaries_by_id, dict)
    assert isinstance(registry.goldfingers_by_id, dict)
    assert isinstance(registry.celestial_phenomena_by_id, dict)


def test_simulation_phase_registry_has_stable_order_and_finalize_tail():
    phases = get_simulation_phases()

    assert [phase.index for phase in phases] == list(range(1, len(phases) + 1))
    assert phases[0].name == "update_perception_and_knowledge"
    assert phases[-1].name == "finalize_step"
    assert phases[-1].reset_check_after is False


def test_avatar_api_assemblers_are_dedicated_entrypoints():
    assert callable(build_avatar_detail)
    assert callable(build_avatar_list_payload)
