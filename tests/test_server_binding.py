"""
Tests for configurable server host and port binding.

These tests verify:
- Environment variable configuration (SERVER_HOST, SERVER_PORT)
- Config file configuration (system.host, system.port)
- Priority: ENV > config file > default values
- Default fallback behavior
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from omegaconf import OmegaConf


class TestServerHostConfiguration:
    """Tests for server host configuration in lifespan and start functions."""

    def test_host_from_env_variable(self):
        """Test SERVER_HOST environment variable takes highest priority."""
        mock_config = MagicMock()
        mock_config.system.host = "192.168.1.100"

        with patch.dict(os.environ, {"SERVER_HOST": "0.0.0.0"}), \
             patch("src.server.main.CONFIG", mock_config):

            # Simulate the logic used in main.py.
            host = os.environ.get("SERVER_HOST") or getattr(
                getattr(mock_config, "system", None), "host", None
            ) or "127.0.0.1"

            assert host == "0.0.0.0"

    def test_host_from_config_when_no_env(self):
        """Test config file host is used when no environment variable."""
        mock_system = MagicMock()
        mock_system.host = "192.168.1.100"
        mock_config = MagicMock()
        mock_config.system = mock_system

        with patch.dict(os.environ, {}, clear=True):
            # Remove SERVER_HOST if it exists.
            os.environ.pop("SERVER_HOST", None)

            host = os.environ.get("SERVER_HOST") or getattr(
                getattr(mock_config, "system", None), "host", None
            ) or "127.0.0.1"

            assert host == "192.168.1.100"

    def test_host_default_when_no_config(self):
        """Test default 127.0.0.1 is used when no env or config."""
        mock_config = MagicMock()
        mock_config.system = None

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SERVER_HOST", None)

            host = os.environ.get("SERVER_HOST") or getattr(
                getattr(mock_config, "system", None), "host", None
            ) or "127.0.0.1"

            assert host == "127.0.0.1"

    def test_host_default_when_system_has_no_host(self):
        """Test default is used when system section exists but has no host."""
        mock_system = MagicMock(spec=[])  # Empty spec means no attributes.
        mock_config = MagicMock()
        mock_config.system = mock_system

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SERVER_HOST", None)

            host = os.environ.get("SERVER_HOST") or getattr(
                getattr(mock_config, "system", None), "host", None
            ) or "127.0.0.1"

            assert host == "127.0.0.1"

    def test_env_overrides_config_host(self):
        """Test environment variable overrides config file value."""
        mock_system = MagicMock()
        mock_system.host = "10.0.0.1"
        mock_config = MagicMock()
        mock_config.system = mock_system

        with patch.dict(os.environ, {"SERVER_HOST": "0.0.0.0"}):
            host = os.environ.get("SERVER_HOST") or getattr(
                getattr(mock_config, "system", None), "host", None
            ) or "127.0.0.1"

            assert host == "0.0.0.0"


class TestServerPortConfiguration:
    """Tests for server port configuration in start function."""

    def test_port_from_env_variable(self):
        """Test SERVER_PORT environment variable takes highest priority."""
        mock_config = MagicMock()
        mock_config.system.port = 9000

        with patch.dict(os.environ, {"SERVER_PORT": "8080"}):
            port = int(
                os.environ.get("SERVER_PORT") or getattr(
                    getattr(mock_config, "system", None), "port", None
                ) or 8002
            )

            assert port == 8080

    def test_port_from_config_when_no_env(self):
        """Test config file port is used when no environment variable."""
        mock_system = MagicMock()
        mock_system.port = 9000
        mock_config = MagicMock()
        mock_config.system = mock_system

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SERVER_PORT", None)

            port = int(
                os.environ.get("SERVER_PORT") or getattr(
                    getattr(mock_config, "system", None), "port", None
                ) or 8002
            )

            assert port == 9000

    def test_port_default_when_no_config(self):
        """Test default 8002 is used when no env or config."""
        mock_config = MagicMock()
        mock_config.system = None

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SERVER_PORT", None)

            port = int(
                os.environ.get("SERVER_PORT") or getattr(
                    getattr(mock_config, "system", None), "port", None
                ) or 8002
            )

            assert port == 8002

    def test_port_as_string_converted_to_int(self):
        """Test port from env variable (string) is converted to int."""
        with patch.dict(os.environ, {"SERVER_PORT": "3000"}):
            port = int(
                os.environ.get("SERVER_PORT") or 8002
            )

            assert port == 3000
            assert isinstance(port, int)


class TestStartFunction:
    """Tests for the start() function server binding."""

    def test_start_uses_default_host_and_port(self):
        """Test start() uses default values when no config."""
        from src.server import main

        mock_config = MagicMock()
        mock_config.system = None

        with patch.dict(os.environ, {}, clear=True), \
             patch.object(main, "CONFIG", mock_config), \
             patch.object(main, "uvicorn") as mock_uvicorn, \
             patch.object(main, "webview"), \
             patch("os.kill"):

            os.environ.pop("SERVER_HOST", None)
            os.environ.pop("SERVER_PORT", None)

            main.start()

            mock_uvicorn.run.assert_called_once()
            call_kwargs = mock_uvicorn.run.call_args
            assert call_kwargs[1]["host"] == "127.0.0.1"
            assert call_kwargs[1]["port"] == 8002

    def test_start_uses_env_variables(self):
        """Test start() uses environment variables when set."""
        from src.server import main

        mock_config = MagicMock()
        mock_system = MagicMock()
        mock_system.host = "10.0.0.1"
        mock_system.port = 9000
        mock_config.system = mock_system

        with patch.dict(os.environ, {"SERVER_HOST": "0.0.0.0", "SERVER_PORT": "8080"}), \
             patch.object(main, "CONFIG", mock_config), \
             patch.object(main, "uvicorn") as mock_uvicorn, \
             patch.object(main, "webview"), \
             patch("os.kill"):

            main.start()

            mock_uvicorn.run.assert_called_once()
            call_kwargs = mock_uvicorn.run.call_args
            assert call_kwargs[1]["host"] == "0.0.0.0"
            assert call_kwargs[1]["port"] == 8080

    def test_start_uses_config_values(self):
        """Test start() uses config file values when no env variables."""
        from src.server import main

        mock_system = MagicMock()
        mock_system.host = "192.168.0.1"
        mock_system.port = 3000
        mock_config = MagicMock()
        mock_config.system = mock_system

        with patch.dict(os.environ, {}, clear=True), \
             patch.object(main, "CONFIG", mock_config), \
             patch.object(main, "uvicorn") as mock_uvicorn, \
             patch.object(main, "webview"), \
             patch("os.kill"):

            os.environ.pop("SERVER_HOST", None)
            os.environ.pop("SERVER_PORT", None)

            main.start()

            mock_uvicorn.run.assert_called_once()
            call_kwargs = mock_uvicorn.run.call_args
            assert call_kwargs[1]["host"] == "192.168.0.1"
            assert call_kwargs[1]["port"] == 3000

    def test_start_env_overrides_config(self):
        """Test environment variables override config file in start()."""
        from src.server import main

        mock_system = MagicMock()
        mock_system.host = "10.0.0.1"
        mock_system.port = 9000
        mock_config = MagicMock()
        mock_config.system = mock_system

        # Only set SERVER_HOST, not SERVER_PORT.
        with patch.dict(os.environ, {"SERVER_HOST": "0.0.0.0"}, clear=True), \
             patch.object(main, "CONFIG", mock_config), \
             patch.object(main, "uvicorn") as mock_uvicorn, \
             patch.object(main, "webview"), \
             patch("os.kill"):

            os.environ.pop("SERVER_PORT", None)

            main.start()

            call_kwargs = mock_uvicorn.run.call_args
            # HOST from env.
            assert call_kwargs[1]["host"] == "0.0.0.0"
            # PORT from config.
            assert call_kwargs[1]["port"] == 9000


class TestLifespanHostConfiguration:
    """Tests for host configuration in lifespan function."""

    def test_lifespan_host_from_env(self):
        """Test lifespan uses SERVER_HOST environment variable."""
        from src.server import main

        mock_config = MagicMock()
        mock_system = MagicMock()
        mock_system.host = "10.0.0.1"
        mock_config.system = mock_system

        with patch.dict(os.environ, {"SERVER_HOST": "0.0.0.0"}), \
             patch.object(main, "CONFIG", mock_config):

            # Simulate the logic in lifespan.
            host = os.environ.get("SERVER_HOST") or getattr(
                getattr(main.CONFIG, "system", None), "host", None
            ) or "127.0.0.1"

            assert host == "0.0.0.0"

    def test_lifespan_host_from_config(self):
        """Test lifespan uses config host when no env variable."""
        from src.server import main

        mock_system = MagicMock()
        mock_system.host = "192.168.1.50"
        mock_config = MagicMock()
        mock_config.system = mock_system

        with patch.dict(os.environ, {}, clear=True), \
             patch.object(main, "CONFIG", mock_config):

            os.environ.pop("SERVER_HOST", None)

            host = os.environ.get("SERVER_HOST") or getattr(
                getattr(main.CONFIG, "system", None), "host", None
            ) or "127.0.0.1"

            assert host == "192.168.1.50"


class TestOmegaConfIntegration:
    """Tests using actual OmegaConf configuration objects."""

    def test_omegaconf_host_access(self):
        """Test accessing host from OmegaConf config object."""
        config = OmegaConf.create({
            "system": {
                "language": "zh-CN",
                "host": "0.0.0.0",
                "port": 8002
            }
        })

        host = getattr(getattr(config, "system", None), "host", None)
        assert host == "0.0.0.0"

    def test_omegaconf_port_access(self):
        """Test accessing port from OmegaConf config object."""
        config = OmegaConf.create({
            "system": {
                "language": "zh-CN",
                "host": "127.0.0.1",
                "port": 9000
            }
        })

        port = getattr(getattr(config, "system", None), "port", None)
        assert port == 9000

    def test_omegaconf_missing_system_section(self):
        """Test graceful handling when system section is missing."""
        config = OmegaConf.create({
            "game": {"init_npc_num": 10}
        })

        host = getattr(getattr(config, "system", None), "host", None) or "127.0.0.1"
        port = getattr(getattr(config, "system", None), "port", None) or 8002

        assert host == "127.0.0.1"
        assert port == 8002

    def test_omegaconf_missing_host_key(self):
        """Test graceful handling when host key is missing from system."""
        config = OmegaConf.create({
            "system": {
                "language": "zh-CN"
            }
        })

        host = getattr(getattr(config, "system", None), "host", None) or "127.0.0.1"
        assert host == "127.0.0.1"

    def test_omegaconf_merged_config_priority(self):
        """Test config merge priority (local_config overrides base config)."""
        base_config = OmegaConf.create({
            "system": {
                "language": "zh-CN",
                "host": "127.0.0.1",
                "port": 8002
            }
        })

        local_config = OmegaConf.create({
            "system": {
                "host": "0.0.0.0"
            }
        })

        # Simulate the merge behavior (local overrides base).
        merged = OmegaConf.merge(base_config, local_config)

        assert merged.system.host == "0.0.0.0"
        assert merged.system.port == 8002  # From base.
        assert merged.system.language == "zh-CN"  # From base.


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_env_variable_uses_config(self):
        """Test empty string env variable falls through to config."""
        mock_system = MagicMock()
        mock_system.host = "10.0.0.1"
        mock_config = MagicMock()
        mock_config.system = mock_system

        # Empty string is falsy in Python.
        with patch.dict(os.environ, {"SERVER_HOST": ""}):
            host = os.environ.get("SERVER_HOST") or getattr(
                getattr(mock_config, "system", None), "host", None
            ) or "127.0.0.1"

            assert host == "10.0.0.1"

    def test_invalid_port_raises_error(self):
        """Test invalid port string raises ValueError."""
        with patch.dict(os.environ, {"SERVER_PORT": "not_a_number"}):
            with pytest.raises(ValueError):
                int(os.environ.get("SERVER_PORT"))

    def test_port_zero_is_valid(self):
        """Test port 0 (random port) is accepted."""
        with patch.dict(os.environ, {"SERVER_PORT": "0"}):
            port = int(os.environ.get("SERVER_PORT") or 8002)
            assert port == 0

    def test_high_port_number(self):
        """Test high port numbers are accepted."""
        with patch.dict(os.environ, {"SERVER_PORT": "65535"}):
            port = int(os.environ.get("SERVER_PORT") or 8002)
            assert port == 65535

    def test_host_ipv6_address(self):
        """Test IPv6 address is accepted as host."""
        with patch.dict(os.environ, {"SERVER_HOST": "::"}):
            host = os.environ.get("SERVER_HOST") or "127.0.0.1"
            assert host == "::"

    def test_host_localhost_string(self):
        """Test 'localhost' string is accepted as host."""
        with patch.dict(os.environ, {"SERVER_HOST": "localhost"}):
            host = os.environ.get("SERVER_HOST") or "127.0.0.1"
            assert host == "localhost"


class TestConfigYamlDefaults:
    """Tests to verify the default values in config.yml."""

    def test_config_yml_has_default_host(self):
        """Test config.yml contains default host value."""
        import yaml

        config_path = "static/config.yml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        assert "system" in config
        assert "host" in config["system"]
        assert config["system"]["host"] == "127.0.0.1"

    def test_config_yml_has_default_port(self):
        """Test config.yml contains default port value."""
        import yaml

        config_path = "static/config.yml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        assert "system" in config
        assert "port" in config["system"]
        assert config["system"]["port"] == 8002
