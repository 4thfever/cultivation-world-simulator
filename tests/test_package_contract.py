from __future__ import annotations

from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_package_scripts_assert_no_sensitive_configs():
    package_dir = get_project_root() / "tools" / "package"
    scripts = [
        package_dir / "pack_github.ps1",
        package_dir / "pack_steam.ps1",
        package_dir / "compress.ps1",
    ]

    for script in scripts:
        content = script.read_text(encoding="utf-8")
        assert "Assert-NoSensitiveConfigs" in content
        assert "local_config.yml" in content
        assert "settings.json" in content
        assert "secrets.json" in content
