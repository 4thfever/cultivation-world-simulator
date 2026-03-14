from __future__ import annotations

import json
from typing import Any

from .models import FallbackMode, FallbackPolicy


def extract_choice_payload(response: dict[str, Any] | str) -> tuple[str, str]:
    if isinstance(response, dict):
        return str(response.get("choice", "")).strip(), str(response.get("thinking", "")).strip()

    clean_response = response.strip()
    if "{" in clean_response and "}" in clean_response:
        try:
            start = clean_response.find("{")
            end = clean_response.rfind("}") + 1
            payload = json.loads(clean_response[start:end])
            if isinstance(payload, dict):
                return (
                    str(payload.get("choice", "")).strip(),
                    str(payload.get("thinking", "")).strip(),
                )
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    return clean_response, ""


def normalize_choice_key(choice: str, valid_keys: list[str]) -> str | None:
    normalized = choice.strip()
    if not normalized:
        return None

    valid_key_set = set(valid_keys)
    if normalized in valid_key_set:
        return normalized

    normalized_upper = normalized.upper()
    for key in valid_keys:
        if normalized_upper == key.upper():
            return key

    if len(normalized_upper) == 1 and normalized_upper.isalpha():
        index = ord(normalized_upper) - ord("A")
        if 0 <= index < len(valid_keys):
            return valid_keys[index]

    compact = normalized_upper.replace(" ", "").replace("-", "_")
    for key in valid_keys:
        key_upper = key.upper()
        if compact == key_upper:
            return key
        if key_upper in compact:
            return key

    return None


def choose_fallback_key(valid_keys: list[str], policy: FallbackPolicy) -> str:
    if not valid_keys:
        raise ValueError("valid_keys cannot be empty")

    if policy.mode == FallbackMode.FIRST_OPTION:
        return valid_keys[0]

    if policy.mode == FallbackMode.PREFERRED_KEY:
        if policy.preferred_key in valid_keys:
            return str(policy.preferred_key)
        raise ValueError(f"Preferred fallback key is invalid: {policy.preferred_key}")

    raise ValueError("No valid fallback could be chosen")
