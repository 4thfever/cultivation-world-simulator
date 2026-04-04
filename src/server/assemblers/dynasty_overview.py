from __future__ import annotations

from typing import Any, Dict
from src.classes.official_rank import DYNASTY_STYLE_MSGIDS, get_dynasty_preference_label
from src.i18n import t


def _localize_style_tag(raw: Any) -> str:
    text = str(raw or "").strip()
    if not text:
        return ""
    translated = t(DYNASTY_STYLE_MSGIDS.get(text, text))
    return translated if translated and translated != text else text


def build_dynasty_overview(world: Any) -> Dict[str, Any]:
    dynasty = getattr(world, "dynasty", None) if world is not None else None
    current_month = int(getattr(world, "month_stamp", 0) or 0) if world is not None else 0
    if dynasty is None:
        return {
            "name": "",
            "title": "",
            "royal_surname": "",
            "royal_house_name": "",
            "desc": "",
            "effect_desc": "",
            "style_tag": "",
            "official_preference_label": "",
            "is_low_magic": True,
            "current_emperor": None,
        }

    emperor = getattr(dynasty, "current_emperor", None)
    emperor_data = None
    if emperor is not None:
        emperor_data = {
            "name": str(getattr(emperor, "name", "") or ""),
            "surname": str(getattr(emperor, "surname", "") or ""),
            "given_name": str(getattr(emperor, "given_name", "") or ""),
            "age": int(emperor.get_age(current_month)),
            "max_age": int(getattr(emperor, "max_age", 80) or 80),
            "is_mortal": True,
        }

    return {
        "name": str(getattr(dynasty, "localized_name", "") or getattr(dynasty, "name", "") or ""),
        "title": str(getattr(dynasty, "title", "") or ""),
        "royal_surname": str(getattr(dynasty, "royal_surname", "") or ""),
        "royal_house_name": str(getattr(dynasty, "royal_house_name", "") or ""),
        "desc": str(getattr(dynasty, "localized_desc", "") or getattr(dynasty, "desc", "") or ""),
        "effect_desc": str(
            getattr(dynasty, "localized_effect_desc", "") or getattr(dynasty, "effect_desc", "") or ""
        ),
        "style_tag": _localize_style_tag(getattr(dynasty, "style_tag", "")),
        "official_preference_label": get_dynasty_preference_label(dynasty),
        "is_low_magic": bool(getattr(dynasty, "is_low_magic", True)),
        "current_emperor": emperor_data,
    }
