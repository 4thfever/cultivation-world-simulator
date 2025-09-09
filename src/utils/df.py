import pandas as pd 
from pathlib import Path

from src.utils.config import CONFIG


def load_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    row_types = {
        "id": int,
        "name": str,
        "description": str,
        "prompt": str,
    }
    for column, dtype in row_types.items():
        if column in df.columns:
            df[column] = df[column].astype(dtype)
    return df

def load_game_configs() -> dict[str, pd.DataFrame]:
    game_configs = {}
    for path in CONFIG.paths.game_configs.glob("*.csv"):
        df = load_csv(path)
        game_configs[path.stem] = df
    return game_configs

game_configs = load_game_configs()