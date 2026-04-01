import importlib
from pathlib import Path

import src.config.data_paths as data_paths
import src.utils.config as app_config


def test_data_paths_are_scoped_under_cws_data_dir(monkeypatch, tmp_path: Path):
    explicit_root = (tmp_path / "docker-runtime-data").resolve()
    monkeypatch.setenv("CWS_DATA_DIR", str(explicit_root))
    data_paths.reset_data_paths_cache()

    paths = data_paths.get_data_paths()

    assert paths.root == explicit_root
    assert paths.settings_file == explicit_root / "settings.json"
    assert paths.secrets_file == explicit_root / "secrets.json"
    assert paths.saves_dir == explicit_root / "saves"
    assert paths.logs_dir == explicit_root / "logs"
    assert paths.cache_dir == explicit_root / "cache"
    assert paths.incompatible_dir == explicit_root / "incompatible"

    assert paths.root.exists()
    assert paths.saves_dir.exists()
    assert paths.logs_dir.exists()
    assert paths.cache_dir.exists()
    assert paths.incompatible_dir.exists()


def test_config_paths_saves_is_injected_from_data_paths(monkeypatch, tmp_path: Path):
    explicit_root = (tmp_path / "docker-runtime-data").resolve()
    monkeypatch.setenv("CWS_DATA_DIR", str(explicit_root))
    data_paths.reset_data_paths_cache()

    reloaded_config = importlib.reload(app_config)
    resolved_paths = data_paths.get_data_paths()

    assert reloaded_config.CONFIG.paths.saves == resolved_paths.saves_dir
