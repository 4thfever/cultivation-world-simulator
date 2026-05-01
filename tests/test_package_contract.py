from __future__ import annotations

from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_package_scripts_assert_no_sensitive_configs():
    package_dir = get_project_root() / "tools" / "package"
    scripts = [
        package_dir / "pack_github.ps1",
        package_dir / "pack_steam_electron.ps1",
        package_dir / "compress.ps1",
    ]

    for script in scripts:
        content = script.read_text(encoding="utf-8")
        assert "Assert-NoSensitiveConfigs" in content
        assert "local_config.yml" in content
        assert "settings.json" in content
        assert "secrets.json" in content


def test_steam_electron_packaging_contract():
    project_root = get_project_root()
    script = project_root / "tools" / "package" / "pack_steam_electron.ps1"
    content = script.read_text(encoding="utf-8")

    assert "CWS_STEAM_BACKEND_DIR" in content
    assert "CWS_STEAM_SEED_FILE" in content
    assert "steam_electron_content_root.txt" in content
    assert "npm run dist:steam" in content
    assert "Assert-NoSensitiveConfigs" in content
    assert "CWS_DEFAULT_LLM_API_KEY" in content
    assert 'Remove-Item -Path $DestWeb -Recurse -Force' in content


def test_steam_frontend_build_avoids_fragile_vendor_chunks():
    project_root = get_project_root()
    config = project_root / "web" / "vite.config.ts"
    content = config.read_text(encoding="utf-8")

    assert "return 'game-panels'" in content
    assert "vendor-vue" not in content
    assert "vendor-ui" not in content


def test_pack_upload_steam_wraps_full_pipeline():
    project_root = get_project_root()
    script = project_root / "tools" / "package" / "pack_upload_steam.ps1"
    content = script.read_text(encoding="utf-8")

    assert "pack_steam_electron.ps1" in content
    assert "steam_electron_content_root.txt" in content
    assert "upload_steam.ps1" in content
    assert "-ContentRoot" in content
    assert "-BuildDesc" in content
    assert "[switch]$PreviewUpload" in content
    assert not (project_root / "tools" / "package" / "pack_upload_steam.cmd").exists()
    assert not (project_root / "tools" / "package" / "pack_upload_steam.sh").exists()


def test_steam_upload_script_supports_electron_parameters():
    project_root = get_project_root()
    script = project_root / "tools" / "package" / "upload_steam.ps1"
    content = script.read_text(encoding="utf-8")

    assert "[Parameter(Mandatory = $true)][string]$ContentRoot" in content
    assert "[string]$BuildDesc" in content
    assert "[string]$Branch" in content
    assert "[switch]$Preview" in content
    assert "SET_LIVE_BRANCH" in content
    assert "tmp\\${tag}_steam" not in content


def test_steam_electron_cursor_command_exists():
    project_root = get_project_root()
    command = project_root / ".cursor" / "commands" / "pack_to_steam.md"
    content = command.read_text(encoding="utf-8")

    assert "pack_upload_steam.ps1" in content
    assert "pack_upload_steam.cmd" not in content


def test_default_steam_cursor_command_does_not_use_legacy_pack_script():
    project_root = get_project_root()
    command = project_root / ".cursor" / "commands" / "pack_to_steam.md"
    content = command.read_text(encoding="utf-8")

    assert "powershell ./tools/package/pack_steam.ps1" not in content


def test_legacy_steam_pack_script_removed():
    project_root = get_project_root()
    assert not (project_root / "tools" / "package" / "pack_steam.ps1").exists()
    assert not (project_root / ".cursor" / "commands" / "pack_to_steam_electron.md").exists()
