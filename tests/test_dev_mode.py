"""Tests for dev mode functionality in the server."""

import subprocess
from unittest.mock import patch, MagicMock
import pytest


class TestEnsureNpmDependencies:
    """Tests for ensure_npm_dependencies function."""

    def test_npm_install_success_unix(self):
        """Test npm install succeeds on Unix-like systems."""
        from src.server.main import ensure_npm_dependencies
        
        with patch("platform.system", return_value="Darwin"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = ensure_npm_dependencies("/fake/web/dir")
            
            assert result is True
            mock_run.assert_called_once_with(
                ["npm", "install"],
                cwd="/fake/web/dir",
                shell=False,
                check=True
            )

    def test_npm_install_success_windows(self):
        """Test npm install succeeds on Windows."""
        from src.server.main import ensure_npm_dependencies
        
        with patch("platform.system", return_value="Windows"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = ensure_npm_dependencies("/fake/web/dir")
            
            assert result is True
            mock_run.assert_called_once_with(
                "npm install",
                cwd="/fake/web/dir",
                shell=True,
                check=True
            )

    def test_npm_install_failure_returns_false(self):
        """Test npm install failure returns False but doesn't raise."""
        from src.server.main import ensure_npm_dependencies
        
        with patch("platform.system", return_value="Darwin"), \
             patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "npm install")
            
            result = ensure_npm_dependencies("/fake/web/dir")
            
            assert result is False

    def test_npm_install_linux(self):
        """Test npm install on Linux uses same path as macOS."""
        from src.server.main import ensure_npm_dependencies
        
        with patch("platform.system", return_value="Linux"), \
             patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            result = ensure_npm_dependencies("/fake/web/dir")
            
            assert result is True
            # Linux should use the same non-shell approach as macOS.
            mock_run.assert_called_once_with(
                ["npm", "install"],
                cwd="/fake/web/dir",
                shell=False,
                check=True
            )
