from __future__ import annotations

import json
from typing import Any, Callable, Optional


def load_effect_from_str(value: object) -> dict[str, Any]:
    """
    将 effects 字段解析为 dict（仅支持标准 JSON 字符串）。
    - value 为 None/空字符串/'nan' 时返回 {}
    - 解析失败或结果非 dict 返回 {}
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


def build_effects_map_from_df(
    df,
    key_column: str,
    parse_key: Callable[[str], Any],
    effects_column: str = "effects",
) -> dict[Any, dict[str, object]]:
    """
    将配表 DataFrame 构造成 {key -> effects} 的映射：
    - key_column：用于定位键（字符串），通过 parse_key 解析为目标键（如 Enum）
    - effects_column：字符串列，使用 load_effect_from_str 解析
    解析失败或空值的行将被忽略。
    """
    effects_map: dict[Any, dict[str, object]] = {}
    if df is None:
        return effects_map
    for _, row in df.iterrows():
        raw_key = str(row.get(key_column, "")).strip()
        if not raw_key or raw_key == "nan":
            continue
        try:
            key = parse_key(raw_key)
        except Exception:
            continue
        eff = load_effect_from_str(row.get(effects_column, ""))
        if eff:
            effects_map[key] = eff
    return effects_map
