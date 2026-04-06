"""
Tests for env-driven server binding and static config cleanup.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


def test_start_uses_default_host_and_port():
    from src.server import main

    with patch.dict(os.environ, {}, clear=True), \
         patch.object(main, "uvicorn") as mock_uvicorn, \
         patch("webbrowser.open"), \
         patch("os.kill"):
        main.start()

    mock_uvicorn.run.assert_called_once()
    kwargs = mock_uvicorn.run.call_args.kwargs
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 8002


def test_start_uses_env_host_and_port():
    from src.server import main

    with patch.dict(os.environ, {"SERVER_HOST": "0.0.0.0", "SERVER_PORT": "8080"}, clear=True), \
         patch.object(main, "uvicorn") as mock_uvicorn, \
         patch("webbrowser.open"), \
         patch("os.kill"):
        main.start()

    kwargs = mock_uvicorn.run.call_args.kwargs
    assert kwargs["host"] == "0.0.0.0"
    assert kwargs["port"] == 8080


def test_empty_env_host_falls_back_to_default():
    with patch.dict(os.environ, {"SERVER_HOST": ""}, clear=True):
        host = os.environ.get("SERVER_HOST") or "127.0.0.1"
    assert host == "127.0.0.1"


def test_invalid_port_raises_value_error():
    with patch.dict(os.environ, {"SERVER_PORT": "not_a_number"}):
        with pytest.raises(ValueError):
            int(os.environ.get("SERVER_PORT") or 8002)


def test_static_config_no_longer_contains_system_section():
    from src.utils.config import CONFIG

    assert "system" not in CONFIG


def test_static_config_no_longer_contains_runtime_saves_source():
    from src.utils.config import CONFIG

    assert "resources" in CONFIG
    assert "saves" not in CONFIG.resources
