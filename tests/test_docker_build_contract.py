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
