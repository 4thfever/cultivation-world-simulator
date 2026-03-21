from __future__ import annotations

from typing import Any, Dict, List

from src.classes.environment.region import CityRegion
from src.classes.mortal import Mortal


def _iter_city_regions(world: Any) -> List[CityRegion]:
    regions = getattr(getattr(world, "map", None), "regions", {}) or {}
    return [region for region in regions.values() if isinstance(region, CityRegion)]


def _get_region_name_by_id(world: Any, region_id: int) -> str:
    if region_id < 0:
        return ""
    regions = getattr(getattr(world, "map", None), "regions", {}) or {}
    region = regions.get(region_id)
    if region is None:
        return ""
    return str(getattr(region, "name", "") or "")


def _get_mortal_age_years(world: Any, mortal: Mortal) -> int:
    current_month = int(getattr(world, "month_stamp", 0))
    return max(0, (current_month - int(mortal.birth_month_stamp)) // 12)


def _build_city_item(city: CityRegion) -> Dict[str, Any]:
    return {
        "id": int(city.id),
        "name": str(city.name),
        "population": float(city.population),
        "population_capacity": float(city.population_capacity),
        "natural_growth": float(city.get_monthly_natural_growth()),
    }


def _build_tracked_mortal_item(world: Any, mortal: Mortal) -> Dict[str, Any]:
    age = _get_mortal_age_years(world, mortal)
    return {
        "id": str(mortal.id),
        "name": str(mortal.name),
        "gender": str(getattr(mortal.gender, "value", mortal.gender)),
        "age": age,
        "born_region_id": int(getattr(mortal, "born_region_id", -1)),
        "born_region_name": _get_region_name_by_id(world, int(getattr(mortal, "born_region_id", -1))),
        "parents": [str(parent_id) for parent_id in list(getattr(mortal, "parents", []) or [])],
        "is_awakening_candidate": age >= 16,
    }


def build_mortal_overview(world: Any) -> Dict[str, Any]:
    city_items = sorted(
        (_build_city_item(city) for city in _iter_city_regions(world)),
        key=lambda item: (-item["population"], item["name"]),
    )

    mortal_manager = getattr(world, "mortal_manager", None)
    tracked_mortals_raw = list(getattr(mortal_manager, "mortals", {}).values()) if mortal_manager else []
    tracked_mortals = sorted(
        (_build_tracked_mortal_item(world, mortal) for mortal in tracked_mortals_raw),
        key=lambda item: (-item["age"], item["name"], item["id"]),
    )

    awakening_candidate_count = sum(1 for item in tracked_mortals if item["is_awakening_candidate"])

    return {
        "summary": {
            "total_population": float(sum(item["population"] for item in city_items)),
            "total_population_capacity": float(sum(item["population_capacity"] for item in city_items)),
            "total_natural_growth": float(sum(item["natural_growth"] for item in city_items)),
            "tracked_mortal_count": len(tracked_mortals),
            "awakening_candidate_count": awakening_candidate_count,
        },
        "cities": city_items,
        "tracked_mortals": tracked_mortals,
    }
