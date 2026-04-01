from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_multilingual_readmes_document_docker_persistence_contract():
    project_root = get_project_root()
    readme_paths = [
        project_root / "README.md",
        project_root / "docs" / "readme" / "EN_README.md",
        project_root / "docs" / "readme" / "ZH-TW_README.md",
        project_root / "docs" / "readme" / "VI-VN_README.md",
    ]

    for readme_path in readme_paths:
        content = readme_path.read_text(encoding="utf-8")
        assert "CWS_DATA_DIR=/data" in content, f"{readme_path} must mention CWS_DATA_DIR=/data"
        assert "./docker-data" in content, f"{readme_path} must mention ./docker-data mapping"
