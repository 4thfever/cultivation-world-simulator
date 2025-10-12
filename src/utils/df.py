import pandas as pd 
from pathlib import Path

from src.utils.config import CONFIG


def load_csv(path: Path) -> pd.DataFrame:
    # 跳过第二行说明行，只读取标题行和实际数据行
    df = pd.read_csv(path, skiprows=[1])
    row_types = {
        "id": int,
        "name": str,
        "description": str,
        "desc": str,
        "weight": float,
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