from __future__ import annotations

import json
import ast
from typing import Any


def load_effect_from_str(value: object) -> dict[str, Any]:
    """
    解析 effects 字符串为 dict：
    - 支持 JSON 格式（双引号）
    - 支持 Python 字面量（单引号，如 {'k': ['v']})
    - value 为 None/空字符串/'nan' 时返回 {}
    - 解析非 dict 则返回 {}
    """
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    s = str(value).strip()
    if not s or s == "nan":
        return {}
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        try:
            obj = ast.literal_eval(s)
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}


def _merge_effects(base: dict[str, object], addition: dict[str, object]) -> dict[str, object]:
    """
    合并两个 effects 字典：
    - list 型（如 legal_actions）：做去重并集
    - 数值型：相加
    - 其他：后者覆盖前者
    返回新字典，不修改原对象。
    """
    if not base and not addition:
        return {}
    merged: dict[str, object] = dict(base) if base else {}
    for key, val in (addition or {}).items():
        if key in merged:
            old = merged[key]
            if isinstance(old, list) and isinstance(val, list):
                # 去重并集，保持相对顺序
                seen: set[object] = set()
                result: list[object] = []
                for x in old + val:
                    if x in seen:
                        continue
                    seen.add(x)
                    result.append(x)
                merged[key] = result
            elif isinstance(old, (int, float)) and isinstance(val, (int, float)):
                merged[key] = old + val
            else:
                merged[key] = val
        else:
            merged[key] = val
    return merged
