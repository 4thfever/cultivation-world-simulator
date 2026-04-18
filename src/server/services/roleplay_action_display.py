from __future__ import annotations

from typing import Any

from src.classes.action.registry import ActionRegistry
import src.classes.action  # noqa: F401
import src.classes.mutual_action  # noqa: F401


def _stringify_simple_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "是" if value else "否"
    return str(value)


def _format_direction(value: Any) -> str:
    mapping = {
        "north": "北",
        "south": "南",
        "east": "东",
        "west": "西",
    }
    return mapping.get(str(value).lower(), _stringify_simple_value(value))


def _format_param_value(param_name: str, value: Any) -> str:
    if param_name == "direction":
        return _format_direction(value)
    return _stringify_simple_value(value)


def _format_move_delta(action_params: dict[str, Any]) -> str:
    dx = action_params.get("delta_x")
    dy = action_params.get("delta_y")
    parts: list[str] = []

    try:
        dx_num = int(dx)
    except (TypeError, ValueError):
        dx_num = 0
    try:
        dy_num = int(dy)
    except (TypeError, ValueError):
        dy_num = 0

    if dx_num > 0:
        parts.append(f"东{dx_num}")
    elif dx_num < 0:
        parts.append(f"西{abs(dx_num)}")

    if dy_num > 0:
        parts.append(f"南{dy_num}")
    elif dy_num < 0:
        parts.append(f"北{abs(dy_num)}")

    return " ".join(parts)


def _build_action_tokens(action_name: str, action_params: dict[str, Any]) -> list[dict[str, str]]:
    try:
        action_cls = ActionRegistry.get(action_name)
        verb = str(action_cls.get_action_name())
    except Exception:
        verb = str(action_name)

    tokens: list[dict[str, str]] = [{"kind": "verb", "text": verb}]
    ordered_values: list[str] = []

    if isinstance(action_params, dict):
        if {"delta_x", "delta_y"}.issubset(action_params.keys()):
            move_delta = _format_move_delta(action_params)
            if move_delta:
                ordered_values.append(move_delta)
        for param_name, value in action_params.items():
            if param_name in {"delta_x", "delta_y"}:
                continue
            display_value = _format_param_value(str(param_name), value)
            if display_value:
                ordered_values.append(display_value)

    for value_text in ordered_values:
        tokens.append({"kind": "arg", "text": value_text})

    return tokens


def build_roleplay_action_chain_display(action_name_params_pairs: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    display_items: list[dict[str, Any]] = []
    for action_name, action_params in action_name_params_pairs:
        display_items.append(
            {
                "action_name": str(action_name),
                "tokens": _build_action_tokens(str(action_name), dict(action_params or {})),
            }
        )
    return display_items
