import re
from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def parse_copy_sources(dockerfile: Path) -> list[str]:
    sources: list[str] = []
    for raw_line in dockerfile.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or not line.startswith("COPY "):
            continue

        parts = line.split()
        if len(parts) >= 3:
            sources.extend(parts[1:-1])
    return sources


def test_frontend_registry_import_targets_static_registry():
    project_root = get_project_root()
    registry_ts = project_root / "web" / "src" / "locales" / "registry.ts"
    content = registry_ts.read_text(encoding="utf-8")

    match = re.search(r"import\s+localeRegistryData\s+from\s+'([^']+)'", content)
    assert match, "Expected locale registry import in web/src/locales/registry.ts"

    imported_path = (registry_ts.parent / match.group(1)).resolve()
    expected_path = (project_root / "static" / "locales" / "registry.json").resolve()

    assert imported_path == expected_path
    assert imported_path.exists()


def test_frontend_dockerfile_copies_shared_locale_registry():
    dockerfile = get_project_root() / "deploy" / "Dockerfile.frontend"
    copy_sources = parse_copy_sources(dockerfile)

    assert "web/" in copy_sources
    assert "static/locales/registry.json" in copy_sources, (
        "Frontend Docker build must copy the shared locale registry because "
        "web/src/locales/registry.ts imports it from outside web/."
    )


def test_frontend_world_info_import_targets_static_game_config():
    project_root = get_project_root()
    world_info_ts = project_root / "web" / "src" / "utils" / "worldInfo.ts"
    content = world_info_ts.read_text(encoding="utf-8")

    match = re.search(r"import\s+worldInfoCsvText\s+from\s+'([^']+)'", content)
    assert match, "Expected world info csv import in web/src/utils/worldInfo.ts"

    imported_path = (world_info_ts.parent / match.group(1).replace("?raw", "")).resolve()
    expected_path = (project_root / "static" / "game_configs" / "world_info.csv").resolve()

    assert imported_path == expected_path
    assert imported_path.exists()


def test_frontend_dockerfile_copies_shared_world_info_csv():
    dockerfile = get_project_root() / "deploy" / "Dockerfile.frontend"
    copy_sources = parse_copy_sources(dockerfile)

    assert "static/game_configs/world_info.csv" in copy_sources, (
        "Frontend Docker build must copy the shared world info csv because "
        "web/src/utils/worldInfo.ts imports it from outside web/."
    )


def test_backend_dockerfile_does_not_copy_tools_directory():
    dockerfile = get_project_root() / "deploy" / "Dockerfile.backend"
    copy_sources = parse_copy_sources(dockerfile)

    assert "src/" in copy_sources
    assert "static/" in copy_sources
    assert "assets/" in copy_sources
    assert "tools/" not in copy_sources, (
        "Backend runtime should not depend on the tools directory after the "
        "locale registry migration to static/locales/registry.json."
    )
