import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.config import CONFIG


def load_csv(path: Path) -> List[Dict[str, Any]]:
    data = []
    if not path.exists():
        return data

    with open(path, "r", encoding="utf-8") as f:
        lines = list(csv.reader(f))
    
    if len(lines) < 1:
        return data

    headers = [h.strip() for h in lines[0]]
    # 去除BOM
    if headers and headers[0].startswith('\ufeff'):
        headers[0] = headers[0][1:]

    # 如果有第二行（说明行），则从第三行开始读取数据
    start_index = 2 if len(lines) > 1 else 1
    
    # 预定义的类型转换规则 (部分核心字段)
    type_converters = {
        "id": int,
        "weight": float,
        "sect_id": int,
        "stage_id": int,
        "root_density": int,
        "duration_years": int,
    }

    for i in range(start_index, len(lines)):
        row_values = lines[i]
        if not row_values:
            continue
            
        row_dict = {}
        for h_idx, header in enumerate(headers):
            if h_idx < len(row_values):
                val = row_values[h_idx].strip()
                
                # 统一处理空值
                if not val or val.lower() == 'nan':
                    val = None
                
                # 类型转换
                elif header in type_converters:
                    try:
                        val = type_converters[header](val)
                    except (ValueError, TypeError):
                        pass # 转换失败保留原字符串
                
                row_dict[header] = val
            else:
                row_dict[header] = None
        
        data.append(row_dict)

    return data

def load_game_configs() -> dict[str, List[Dict[str, Any]]]:
    game_configs = {}
    for path in CONFIG.paths.game_configs.glob("*.csv"):
        data = load_csv(path)
        game_configs[path.stem] = data
    return game_configs

game_configs = load_game_configs()

# =============================================================================
# 辅助函数：让业务层代码更简洁
# =============================================================================

def get_str(row: Dict[str, Any], key: str, default: str = "") -> str:
    val = row.get(key)
    if val is None:
        return default
    return str(val).strip()

def get_int(row: Dict[str, Any], key: str, default: int = 0) -> int:
    val = row.get(key)
    if val is None:
        return default
    try:
        return int(float(val)) # 处理可能存在的浮点数字符串 "1.0"
    except (ValueError, TypeError):
        return default

def get_float(row: Dict[str, Any], key: str, default: float = 0.0) -> float:
    val = row.get(key)
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default
        
def get_bool(row: Dict[str, Any], key: str, default: bool = False) -> bool:
    val = row.get(key)
    if val is None:
        return default
    s = str(val).lower()
    return s in ('true', '1', 'yes', 'y')

def get_list_int(row: Dict[str, Any], key: str, separator: str = None) -> List[int]:
    """解析整数列表，如 "1|2|3" """
    if separator is None:
        separator = CONFIG.df.ids_separator
    val = row.get(key)
    if not val:
        return []
    res = []
    for x in str(val).split(separator):
        x = x.strip()
        if x:
            try:
                res.append(int(float(x)))
            except ValueError:
                pass
    return res

def get_list_str(row: Dict[str, Any], key: str, separator: str = None) -> List[str]:
    """解析字符串列表"""
    if separator is None:
        separator = CONFIG.df.ids_separator
    val = row.get(key)
    if not val:
        return []
    return [x.strip() for x in str(val).split(separator) if x.strip()]
