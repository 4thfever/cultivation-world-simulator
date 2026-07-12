from __future__ import annotations

import inspect

from src.run.static_data_registry import build_static_game_data_registry
from src.server.app_context import ServerAppContext
from src.server.app_factory import create_configured_app
from src.server.llm_runtime_handlers import create_llm_runtime_handlers
from src.server.runtime_hooks import create_runtime_hooks
from src.server.services.game_command_service import GameCommandService
from src.server.services.game_query_service import GameQueryService
from src.server.settings_handlers import SettingsServiceProxy, create_settings_handlers
from src.sim.save.sections import registry
from src.sim.save.sections.load_restore import restore_loaded_game


def test_phase3_server_composition_entrypoints_exist():
    assert callable(create_configured_app)
    assert callable(create_runtime_hooks)
    assert callable(create_settings_handlers)
    assert callable(create_llm_runtime_handlers)
    assert callable(GameQueryService.from_dependencies)
    assert callable(GameCommandService.from_dependencies)


def test_server_context_carries_static_data_and_services():
    annotations = ServerAppContext.__annotations__

    assert "static_data" in annotations
    assert "query_service" in annotations
    assert "command_service" in annotations


def test_save_registry_is_only_section_order_and_dispatch():
    source = inspect.getsource(registry)

    assert "SAVE_SECTIONS" in source
    assert "def dump_save_data" in source
    assert "class WorldSection" not in source
    assert "def restore_loaded_game" not in source
    assert registry.restore_loaded_game is restore_loaded_game


def test_settings_service_proxy_reads_current_service_each_call():
    calls = []

    class Service:
        def __init__(self, token):
            self.token = token

        def get_settings_view(self):
            return self.token

    def get_service():
        token = object()
        calls.append(token)
        return Service(token)

    proxy = SettingsServiceProxy(get_service)

    first = proxy.get_settings_view()
    second = proxy.get_settings_view()

    assert first is calls[0]
    assert second is calls[1]
    assert first is not second


def test_static_data_registry_is_shared_phase3_dependency_source():
    static_data = build_static_game_data_registry()

    assert static_data.sects_by_id
    assert static_data.celestial_phenomena_by_id
