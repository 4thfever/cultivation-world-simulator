from __future__ import annotations

from typing import Any, Dict


def build_dynasty_overview(world: Any) -> Dict[str, Any]:
    dynasty = getattr(world, "dynasty", None)
    current_month = int(getattr(world, "month_stamp", 0))
    if dynasty is None:
        return {
            "name": "",
            "title": "",
            "royal_surname": "",
            "royal_house_name": "",
            "desc": "",
            "effect_desc": "",
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
        "name": str(getattr(dynasty, "name", "") or ""),
        "title": str(getattr(dynasty, "title", "") or ""),
        "royal_surname": str(getattr(dynasty, "royal_surname", "") or ""),
        "royal_house_name": str(getattr(dynasty, "royal_house_name", "") or ""),
        "desc": str(getattr(dynasty, "desc", "") or ""),
        "effect_desc": str(getattr(dynasty, "effect_desc", "") or ""),
        "is_low_magic": bool(getattr(dynasty, "is_low_magic", True)),
        "current_emperor": emperor_data,
    }
