from __future__ import annotations

from dataclasses import dataclass
import random
from typing import TYPE_CHECKING, Any

from src.classes.effect import format_effects_to_text, load_effect_from_str
from src.i18n import t
from src.utils.df import game_configs, get_int, get_str

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


@dataclass(frozen=True)
class FormationTypeConfig:
    key: str
    name_id: str
    base_duration_months: int
    base_cost: int
    effects: dict[str, int | float]


DEFAULT_FORMATION_TYPES: dict[str, FormationTypeConfig] = {
    FORMATION_SPIRIT_GATHERING: FormationTypeConfig(
        key=FORMATION_SPIRIT_GATHERING,
        name_id="formation_spirit_gathering_name",
        base_duration_months=24,
        base_cost=120,
        effects={"extra_respire_exp_multiplier": 0.20},
    ),
    FORMATION_MOUNTAIN_GUARD: FormationTypeConfig(
        key=FORMATION_MOUNTAIN_GUARD,
        name_id="formation_mountain_guard_name",
        base_duration_months=24,
        base_cost=160,
        effects={"extra_battle_strength_points": 3},
    ),
    FORMATION_HEALING: FormationTypeConfig(
        key=FORMATION_HEALING,
        name_id="formation_healing_name",
        base_duration_months=18,
        base_cost=100,
        effects={"extra_hp_recovery_rate": 0.40},
    ),
    FORMATION_CLARITY: FormationTypeConfig(
        key=FORMATION_CLARITY,
        name_id="formation_clarity_name",
        base_duration_months=18,
        base_cost=140,
        effects={"extra_breakthrough_success_rate": 0.06, "extra_retreat_success_rate": 0.06},
    ),
    FORMATION_VEIN_SEEKING: FormationTypeConfig(
        key=FORMATION_VEIN_SEEKING,
        name_id="formation_vein_seeking_name",
        base_duration_months=18,
        base_cost=80,
        effects={"extra_mine_materials": 1},
    ),
    FORMATION_WOOD_GROWTH: FormationTypeConfig(
        key=FORMATION_WOOD_GROWTH,
        name_id="formation_wood_growth_name",
        base_duration_months=18,
        base_cost=80,
        effects={"extra_harvest_materials": 1},
    ),
    FORMATION_BEAST_DRIVING: FormationTypeConfig(
        key=FORMATION_BEAST_DRIVING,
        name_id="formation_beast_driving_name",
        base_duration_months=18,
        base_cost=80,
        effects={"extra_hunt_materials": 1},
    ),
}


def get_formation_types() -> dict[str, FormationTypeConfig]:
    rows = game_configs.get("formation", []) or []
    if not rows:
        return DEFAULT_FORMATION_TYPES

    configs: dict[str, FormationTypeConfig] = {}
    for row in rows:
        key = normalize_formation_type(get_str(row, "key"))
        if not key:
            continue
        default = DEFAULT_FORMATION_TYPES.get(key, FormationTypeConfig(key, key, 1, 1, {}))
        effects = load_effect_from_str(get_str(row, "effects"))
        if not isinstance(effects, dict):
            effects = {}
        configs[key] = FormationTypeConfig(
            key=key,
            name_id=get_str(row, "name_id") or default.name_id,
            base_duration_months=max(1, get_int(row, "base_duration_months", default.base_duration_months)),
            base_cost=max(1, get_int(row, "base_cost", default.base_cost)),
            effects={k: v for k, v in effects.items() if isinstance(v, (int, float))},
        )

    return configs or DEFAULT_FORMATION_TYPES


def normalize_formation_type(formation_type: str) -> str:
    return str(formation_type or "").strip().lower()


def is_valid_formation_type(formation_type: str) -> bool:
    return normalize_formation_type(formation_type) in get_formation_types()


def get_formation_type_name(formation_type: str) -> str:
    cfg = get_formation_types().get(normalize_formation_type(formation_type))
    return t(cfg.name_id) if cfg else str(formation_type)


def get_formation_disk_config(auxiliary: "Auxiliary | None") -> FormationDiskConfig | None:
    if auxiliary is None:
        return None
    effects = getattr(auxiliary, "effects", {}) or {}
    legal = effects.get("legal_actions", [])
    if SET_FORMATION_ACTION not in legal:
        return None
    try:
        item_id = int(getattr(auxiliary, "id", 0) or 0)
    except (TypeError, ValueError):
        item_id = 0
    return FormationDiskConfig(item_id=item_id)


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
    if key not in get_formation_types():
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
        for cfg in get_formation_types().values()
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
            option["duration"] = compute_formation_duration(avatar, cfg.key, randomize=False)
            option["effect_desc"] = format_effects_to_text(effects)
        options.append(option)
    return options


def compute_formation_cost(
    avatar: "Avatar",
    formation_type: str,
    region: "Region | None",
    disk_cfg: FormationDiskConfig | None = None,
) -> int:
    cfg = get_formation_types()[normalize_formation_type(formation_type)]
    disk = disk_cfg or get_formation_disk_config(getattr(avatar, "auxiliary", None))
    if disk is None:
        return 0
    cost = float(cfg.base_cost) * _region_cost_multiplier(region)
    reduction = float(getattr(avatar, "effects", {}).get(FORMATION_COST_REDUCTION, 0.0) or 0.0)
    reduction = max(0.0, min(0.8, reduction))
    return max(1, int(round(cost * (1.0 - reduction))))


def compute_formation_duration(
    avatar: "Avatar",
    formation_type: str,
    *,
    randomize: bool = True,
) -> int:
    cfg = get_formation_types()[normalize_formation_type(formation_type)]
    extra = int(getattr(avatar, "effects", {}).get(EXTRA_FORMATION_DURATION_MONTHS, 0) or 0)
    delta = random.randint(-3, 6) if randomize else 0
    return max(1, int(cfg.base_duration_months + extra + delta))


def build_formation_effects(
    avatar: "Avatar",
    formation_type: str,
    disk_cfg: FormationDiskConfig,
) -> dict[str, int | float]:
    cfg = get_formation_types()[normalize_formation_type(formation_type)]
    base_effects = cfg.effects
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
        "duration": compute_formation_duration(avatar, key),
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
