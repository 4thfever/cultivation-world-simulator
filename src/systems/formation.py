from __future__ import annotations

from dataclasses import dataclass
import random
from typing import TYPE_CHECKING, Any

from src.classes.effect import format_effects_to_text
from src.i18n import t

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.core.world import World
    from src.classes.environment.region import Region
    from src.classes.items.auxiliary import Auxiliary


SET_FORMATION_ACTION = "SetFormation"

FORMATION_SPIRIT_GATHERING = "spirit_gathering"
FORMATION_MOUNTAIN_GUARD = "mountain_guard"
FORMATION_HEALING = "healing"
FORMATION_CLARITY = "clarity"
FORMATION_VEIN_SEEKING = "vein_seeking"
FORMATION_WOOD_GROWTH = "wood_growth"
FORMATION_BEAST_DRIVING = "beast_driving"

EXTRA_FORMATION_POWER = "extra_formation_power"
EXTRA_FORMATION_DURATION_MONTHS = "extra_formation_duration_months"
FORMATION_COST_REDUCTION = "formation_cost_reduction"


@dataclass(frozen=True)
class FormationDiskConfig:
    item_id: int
    rank: int
    base_duration_months: int
    base_cost: int


@dataclass(frozen=True)
class FormationTypeConfig:
    key: str
    name_id: str
    cost_multiplier: float
    effects_by_disk_rank: tuple[dict[str, int | float], ...]


FORMATION_DISK_CONFIGS: dict[int, FormationDiskConfig] = {
    2081: FormationDiskConfig(item_id=2081, rank=0, base_duration_months=18, base_cost=80),
    2082: FormationDiskConfig(item_id=2082, rank=1, base_duration_months=24, base_cost=200),
    2083: FormationDiskConfig(item_id=2083, rank=2, base_duration_months=30, base_cost=600),
    2084: FormationDiskConfig(item_id=2084, rank=3, base_duration_months=36, base_cost=1800),
}


FORMATION_TYPES: dict[str, FormationTypeConfig] = {
    FORMATION_SPIRIT_GATHERING: FormationTypeConfig(
        key=FORMATION_SPIRIT_GATHERING,
        name_id="formation_spirit_gathering_name",
        cost_multiplier=1.2,
        effects_by_disk_rank=(
            {"extra_respire_exp_multiplier": 0.10},
            {"extra_respire_exp_multiplier": 0.18},
            {"extra_respire_exp_multiplier": 0.28},
            {"extra_respire_exp_multiplier": 0.40},
        ),
    ),
    FORMATION_MOUNTAIN_GUARD: FormationTypeConfig(
        key=FORMATION_MOUNTAIN_GUARD,
        name_id="formation_mountain_guard_name",
        cost_multiplier=1.4,
        effects_by_disk_rank=(
            {"extra_battle_strength_points": 1},
            {"extra_battle_strength_points": 2},
            {"extra_battle_strength_points": 4},
            {"extra_battle_strength_points": 7},
        ),
    ),
    FORMATION_HEALING: FormationTypeConfig(
        key=FORMATION_HEALING,
        name_id="formation_healing_name",
        cost_multiplier=1.0,
        effects_by_disk_rank=(
            {"extra_hp_recovery_rate": 0.20},
            {"extra_hp_recovery_rate": 0.35},
            {"extra_hp_recovery_rate": 0.55},
            {"extra_hp_recovery_rate": 0.80},
        ),
    ),
    FORMATION_CLARITY: FormationTypeConfig(
        key=FORMATION_CLARITY,
        name_id="formation_clarity_name",
        cost_multiplier=1.3,
        effects_by_disk_rank=(
            {"extra_breakthrough_success_rate": 0.03, "extra_retreat_success_rate": 0.03},
            {"extra_breakthrough_success_rate": 0.05, "extra_retreat_success_rate": 0.05},
            {"extra_breakthrough_success_rate": 0.08, "extra_retreat_success_rate": 0.08},
            {"extra_breakthrough_success_rate": 0.12, "extra_retreat_success_rate": 0.12},
        ),
    ),
    FORMATION_VEIN_SEEKING: FormationTypeConfig(
        key=FORMATION_VEIN_SEEKING,
        name_id="formation_vein_seeking_name",
        cost_multiplier=0.8,
        effects_by_disk_rank=(
            {"extra_mine_materials": 1},
            {"extra_mine_materials": 1},
            {"extra_mine_materials": 2},
            {"extra_mine_materials": 3},
        ),
    ),
    FORMATION_WOOD_GROWTH: FormationTypeConfig(
        key=FORMATION_WOOD_GROWTH,
        name_id="formation_wood_growth_name",
        cost_multiplier=0.8,
        effects_by_disk_rank=(
            {"extra_harvest_materials": 1},
            {"extra_harvest_materials": 1},
            {"extra_harvest_materials": 2},
            {"extra_harvest_materials": 3},
        ),
    ),
    FORMATION_BEAST_DRIVING: FormationTypeConfig(
        key=FORMATION_BEAST_DRIVING,
        name_id="formation_beast_driving_name",
        cost_multiplier=0.8,
        effects_by_disk_rank=(
            {"extra_hunt_materials": 1},
            {"extra_hunt_materials": 1},
            {"extra_hunt_materials": 2},
            {"extra_hunt_materials": 3},
        ),
    ),
}


def normalize_formation_type(formation_type: str) -> str:
    return str(formation_type or "").strip().lower()


def is_valid_formation_type(formation_type: str) -> bool:
    return normalize_formation_type(formation_type) in FORMATION_TYPES


def get_formation_type_name(formation_type: str) -> str:
    cfg = FORMATION_TYPES.get(normalize_formation_type(formation_type))
    return t(cfg.name_id) if cfg else str(formation_type)


def get_formation_disk_config(auxiliary: "Auxiliary | None") -> FormationDiskConfig | None:
    if auxiliary is None:
        return None
    try:
        item_id = int(getattr(auxiliary, "id", 0) or 0)
    except (TypeError, ValueError):
        return None
    return FORMATION_DISK_CONFIGS.get(item_id)


def is_formation_disk(auxiliary: "Auxiliary | None") -> bool:
    return get_formation_disk_config(auxiliary) is not None


def has_formation_permission(avatar: "Avatar") -> bool:
    legal = getattr(avatar, "effects", {}).get("legal_actions", [])
    return SET_FORMATION_ACTION in legal


def ensure_region_formations(world: "World") -> dict[int, dict[str, Any]]:
    game_map = getattr(world, "map", None)
    if game_map is None:
        return {}
    formations = getattr(game_map, "region_formations", None)
    if formations is None:
        formations = {}
        setattr(game_map, "region_formations", formations)
    return formations


def cleanup_expired_region_formations(world: "World", current_month: int | None = None) -> None:
    formations = ensure_region_formations(world)
    month = int(current_month if current_month is not None else getattr(world, "month_stamp", 0))
    expired: list[int] = []
    for region_id, formation in formations.items():
        start = _int_or_default(formation.get("start_month"), month)
        duration = _int_or_default(formation.get("duration"), 0)
        if duration <= 0 or month >= start + duration:
            expired.append(region_id)
    for region_id in expired:
        formations.pop(region_id, None)


def get_active_region_formation(world: "World", region_id: int | str | None) -> dict[str, Any] | None:
    if region_id is None:
        return None
    cleanup_expired_region_formations(world)
    try:
        normalized_region_id = int(region_id)
    except (TypeError, ValueError):
        return None
    formation = ensure_region_formations(world).get(normalized_region_id)
    if not formation:
        return None
    return formation


def get_active_region_formation_effects(world: "World", region_id: int | str | None) -> dict[str, object]:
    formation = get_active_region_formation(world, region_id)
    if formation is None:
        return {}
    effects = formation.get("effects", {})
    return dict(effects) if isinstance(effects, dict) else {}


def get_current_region_formation_effects(avatar: "Avatar") -> dict[str, object]:
    region = getattr(getattr(avatar, "tile", None), "region", None)
    world = getattr(avatar, "world", None)
    if world is None or region is None:
        return {}
    return get_active_region_formation_effects(world, getattr(region, "id", None))


def get_region_formation_effect_value(avatar: "Avatar", effect_key: str, default: int | float = 0) -> int | float:
    effects = get_current_region_formation_effects(avatar)
    value = effects.get(effect_key, default)
    if isinstance(default, int) and not isinstance(default, bool):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def is_formation_allowed_in_region(formation_type: str, region: "Region | None") -> bool:
    if region is None:
        return False
    key = normalize_formation_type(formation_type)
    if key not in FORMATION_TYPES:
        return False

    from src.classes.environment.region import CityRegion, CultivateRegion, NormalRegion
    from src.classes.environment.sect_region import SectRegion

    if key in {FORMATION_SPIRIT_GATHERING, FORMATION_MOUNTAIN_GUARD, FORMATION_CLARITY}:
        return isinstance(region, (CultivateRegion, SectRegion))
    if key == FORMATION_HEALING:
        return isinstance(region, (CultivateRegion, SectRegion, CityRegion))
    if key == FORMATION_VEIN_SEEKING:
        return isinstance(region, NormalRegion) and bool(getattr(region, "lodes", []) or [])
    if key == FORMATION_WOOD_GROWTH:
        return isinstance(region, NormalRegion) and bool(getattr(region, "plants", []) or [])
    if key == FORMATION_BEAST_DRIVING:
        return isinstance(region, NormalRegion) and bool(getattr(region, "animals", []) or [])
    return False


def get_available_formation_types_for_region(region: "Region | None") -> list[FormationTypeConfig]:
    return [
        cfg
        for cfg in FORMATION_TYPES.values()
        if is_formation_allowed_in_region(cfg.key, region)
    ]


def get_available_formation_type_options(avatar: "Avatar") -> list[dict[str, Any]]:
    region = getattr(getattr(avatar, "tile", None), "region", None)
    disk_cfg = get_formation_disk_config(getattr(avatar, "auxiliary", None))
    options: list[dict[str, Any]] = []
    for cfg in get_available_formation_types_for_region(region):
        option: dict[str, Any] = {
            "value": cfg.key,
            "id": cfg.key,
            "name": get_formation_type_name(cfg.key),
        }
        if disk_cfg is not None:
            effects = build_formation_effects(avatar, cfg.key, disk_cfg)
            option["cost"] = compute_formation_cost(avatar, cfg.key, region, disk_cfg)
            option["duration"] = compute_formation_duration(avatar, disk_cfg, randomize=False)
            option["effect_desc"] = format_effects_to_text(effects)
        options.append(option)
    return options


def compute_formation_cost(
    avatar: "Avatar",
    formation_type: str,
    region: "Region | None",
    disk_cfg: FormationDiskConfig | None = None,
) -> int:
    cfg = FORMATION_TYPES[normalize_formation_type(formation_type)]
    disk = disk_cfg or get_formation_disk_config(getattr(avatar, "auxiliary", None))
    if disk is None:
        return 0
    cost = float(disk.base_cost) * cfg.cost_multiplier * _region_cost_multiplier(region)
    reduction = float(getattr(avatar, "effects", {}).get(FORMATION_COST_REDUCTION, 0.0) or 0.0)
    reduction = max(0.0, min(0.8, reduction))
    return max(1, int(round(cost * (1.0 - reduction))))


def compute_formation_duration(
    avatar: "Avatar",
    disk_cfg: FormationDiskConfig,
    *,
    randomize: bool = True,
) -> int:
    extra = int(getattr(avatar, "effects", {}).get(EXTRA_FORMATION_DURATION_MONTHS, 0) or 0)
    delta = random.randint(-3, 6) if randomize else 0
    return max(1, int(disk_cfg.base_duration_months + extra + delta))


def build_formation_effects(
    avatar: "Avatar",
    formation_type: str,
    disk_cfg: FormationDiskConfig,
) -> dict[str, int | float]:
    cfg = FORMATION_TYPES[normalize_formation_type(formation_type)]
    base_effects = cfg.effects_by_disk_rank[disk_cfg.rank]
    power_bonus = float(getattr(avatar, "effects", {}).get(EXTRA_FORMATION_POWER, 0.0) or 0.0)
    multiplier = 1.0 + max(0.0, power_bonus)
    effects: dict[str, int | float] = {}
    for key, value in base_effects.items():
        if isinstance(value, int):
            effects[key] = max(1, int(round(value * multiplier)))
        else:
            effects[key] = round(float(value) * multiplier, 4)
    return effects


def build_formation_record(
    avatar: "Avatar",
    formation_type: str,
    region: "Region",
    disk_cfg: FormationDiskConfig,
) -> dict[str, Any]:
    key = normalize_formation_type(formation_type)
    cost = compute_formation_cost(avatar, key, region, disk_cfg)
    return {
        "formation_type": key,
        "caster_id": str(getattr(avatar, "id", "")),
        "disk_item_id": int(disk_cfg.item_id),
        "start_month": int(getattr(getattr(avatar, "world", None), "month_stamp", 0)),
        "duration": compute_formation_duration(avatar, disk_cfg),
        "effects": build_formation_effects(avatar, key, disk_cfg),
        "cost": cost,
    }


def place_region_formation(world: "World", region_id: int, formation: dict[str, Any]) -> dict[str, Any] | None:
    formations = ensure_region_formations(world)
    old = formations.get(int(region_id))
    formations[int(region_id)] = formation
    return old


def get_formation_display_info(world: "World", region_id: int | str | None) -> dict[str, Any] | None:
    formation = get_active_region_formation(world, region_id)
    if formation is None:
        return None
    key = normalize_formation_type(str(formation.get("formation_type", "")))
    start = _int_or_default(formation.get("start_month"), int(getattr(world, "month_stamp", 0)))
    duration = _int_or_default(formation.get("duration"), 0)
    current = int(getattr(world, "month_stamp", 0))
    remaining = max(0, start + duration - current)
    effects = dict(formation.get("effects", {}) or {})
    return {
        "formation_type": key,
        "name": get_formation_type_name(key),
        "remaining_months": remaining,
        "effect_desc": format_effects_to_text(effects),
        "caster_id": str(formation.get("caster_id", "") or ""),
        "disk_item_id": int(formation.get("disk_item_id", 0) or 0),
        "cost": int(formation.get("cost", 0) or 0),
        "effects": effects,
    }


def _region_cost_multiplier(region: "Region | None") -> float:
    if region is None:
        return 1.0
    from src.classes.environment.region import CityRegion, CultivateRegion, NormalRegion
    from src.classes.environment.sect_region import SectRegion

    if isinstance(region, SectRegion):
        return 1.5
    if isinstance(region, CultivateRegion):
        return 1.3
    if isinstance(region, CityRegion):
        return 1.1
    if isinstance(region, NormalRegion):
        return 1.0
    return 1.0


def _int_or_default(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
