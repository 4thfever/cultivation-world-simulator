from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TOOL_ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT_DIR = TOOL_ROOT / "dist"
ASSETS_ROOT = PROJECT_ROOT / "assets"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif")


def _ensure_project_importable() -> None:
    import sys

    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def _json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, set):
        return sorted(str(item) for item in value)
    if hasattr(value, "value"):
        return value.value
    return str(value)


def _as_plain_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return json.loads(json.dumps(value, ensure_ascii=False, default=_json_default))


def _structured_items(values: Iterable[Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in values:
        if hasattr(item, "get_structured_info"):
            data = item.get_structured_info()
        elif hasattr(item, "get_info"):
            data = item.get_info(detailed=True)
        else:
            data = getattr(item, "__dict__", {})
        items.append(_as_plain_dict(data))
    return sorted(items, key=lambda row: str(row.get("id", row.get("name", ""))))


def _get_rarity_info(item: Any) -> dict[str, Any] | None:
    rarity = getattr(item, "rarity", None)
    if rarity is None:
        return None
    level = getattr(rarity, "level", None)
    return {
        "level": getattr(level, "value", str(level)) if level is not None else "",
        "name": str(rarity),
        "weight": float(getattr(rarity, "weight", 0.0) or 0.0),
        "color": list(getattr(rarity, "color_rgb", (255, 255, 255))),
        "color_hex": getattr(rarity, "color_hex", "#ffffff"),
    }


def _build_completeness(required_fields: dict[str, Any], optional_fields: dict[str, Any] | None = None) -> dict[str, Any]:
    missing = [key for key, value in required_fields.items() if value in (None, "", [], {}, ())]
    optional_missing = [key for key, value in (optional_fields or {}).items() if value in (None, "", [], {}, ())]
    return {
        "missing": missing,
        "optional_missing": optional_missing,
        "complete": not missing,
    }


def _category_meta(category: str, *, source: str, tone: str = "") -> dict[str, Any]:
    return {"category": category, "source": source, "tone": tone}


def _drop_relations(item: dict[str, Any]) -> dict[str, list[str]]:
    drops = item.get("drops")
    if not isinstance(drops, list):
        return {}
    materials = [str(drop.get("name")) for drop in drops if isinstance(drop, dict) and drop.get("name")]
    return {"materials": materials} if materials else {}


def _asset_path(relative_path: str | Path) -> Path:
    return ASSETS_ROOT / Path(relative_path)


def _asset_src(relative_path: str | Path) -> str:
    return f"./assets/{Path(relative_path).as_posix()}"


def _image(relative_path: str | Path, alt: str, kind: str = "illustration") -> dict[str, str] | None:
    path = _asset_path(relative_path)
    if not path.exists() or not path.is_file():
        return None
    return {
        "src": _asset_src(relative_path),
        "alt": str(alt),
        "kind": kind,
    }


def _images(candidates: Iterable[tuple[str | Path, str, str]]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for relative_path, alt, kind in candidates:
        image = _image(relative_path, alt, kind)
        if image and image["src"] not in seen:
            result.append(image)
            seen.add(image["src"])
    return result


def _attach_images(item: dict[str, Any], images: Iterable[dict[str, str] | None]) -> None:
    valid_images = [image for image in images if image]
    if not valid_images:
        return
    item["cover_image"] = valid_images[0]
    item["images"] = valid_images


def _numbered_asset_gallery(directory: str, stem: str, *, alt: str, kind: str, count: int = 4) -> list[dict[str, str]]:
    candidates: list[tuple[str, str, str]] = []
    for index in range(count):
        for extension in IMAGE_EXTENSIONS:
            candidates.append((f"{directory}/{stem}_{index}{extension}", f"{alt} {index + 1}", kind))
    return _images(candidates)


def _normal_region_images(region_id: Any, name: str) -> list[dict[str, str]]:
    tile_by_id = {
        "101": "plain",
        "102": "desert",
        "103": "rainforest",
        "104": "glacier",
        "105": "sea",
        "106": "water",
        "107": "mountain",
        "108": "snow_mountain",
        "109": "grassland",
        "110": "forest",
        "111": "volcano",
        "112": "farm",
        "113": "swamp",
        "114": "mountain",
        "115": "bamboo",
        "116": "tundra",
        "117": "gobi",
        "118": "island",
    }
    tile = tile_by_id.get(str(region_id))
    if not tile:
        return []
    return _images([(f"tiles/{tile}.png", name, "tile"), (f"tiles/{tile}_0.png", f"{name} tile sample", "tile")])


def _cultivate_region_images(sub_type: Any, name: str) -> list[dict[str, str]]:
    stem = "ruin" if str(sub_type or "").lower() == "ruin" else "cave"
    gallery = _numbered_asset_gallery("tiles", stem, alt=name, kind="tile")
    return _images([(f"tiles/{stem}.png", name, "tile")]) + gallery


def _city_region_images(region_id: Any, name: str) -> list[dict[str, str]]:
    gallery = _numbered_asset_gallery("cities", f"city_{region_id}", alt=name, kind="region")
    named = _images([(f"cities/{name}.jpg", name, "region"), (f"cities/{name}.png", name, "region")])
    return gallery + named


def _sect_images(sect_id: Any, name: str) -> list[dict[str, str]]:
    return _images([(f"sects/sect_{sect_id}.png", name, "sect")]) + _numbered_asset_gallery(
        "sects", f"sect_{sect_id}", alt=name, kind="sect"
    )


def _theme_for_rarity(level: str | None) -> str:
    return {
        "N": "rarity-n",
        "R": "rarity-r",
        "SR": "rarity-sr",
        "SSR": "rarity-ssr",
    }.get(str(level or "").upper(), "")


def _theme_for_grade(grade: Any) -> str:
    grade_text = str(grade or "").upper()
    if "UPPER" in grade_text or "上品" in grade_text or "THƯỢNG" in grade_text:
        return "grade-upper"
    if "MIDDLE" in grade_text or "中品" in grade_text or "TRUNG" in grade_text:
        return "grade-middle"
    if "LOWER" in grade_text or "下品" in grade_text or "HẠ" in grade_text:
        return "grade-lower"
    if "NASCENT" in grade_text:
        return "grade-nascent"
    if "CORE" in grade_text:
        return "grade-core"
    if "FOUNDATION" in grade_text:
        return "grade-foundation"
    if "QI" in grade_text:
        return "grade-qi"
    return ""


def _serialize_world_info() -> list[dict[str, Any]]:
    from src.utils.df import game_configs, get_str

    rows = []
    for row in game_configs.get("world_info", []):
        item = {
            "id": get_str(row, "name_id") or get_str(row, "title_id") or get_str(row, "title"),
            "title": get_str(row, "title"),
            "name": get_str(row, "name"),
            "desc": get_str(row, "desc"),
            "title_id": get_str(row, "title_id"),
            "name_id": get_str(row, "name_id"),
            "desc_id": get_str(row, "desc_id"),
            "meta": _category_meta("world", source="csv"),
            "completeness": _build_completeness(
                {
                    "title": get_str(row, "title"),
                    "name_id": get_str(row, "name_id"),
                    "desc_id": get_str(row, "desc_id"),
                }
            ),
        }
        rows.append(item)
    return rows


def _param_sources_to_dict(action_cls: type) -> dict[str, str]:
    sources: dict[str, Any] = {}
    for cls in reversed(action_cls.__mro__):
        sources.update(getattr(cls, "PARAM_OPTION_SOURCES", {}) or {})
    return {str(key): str(getattr(value, "value", value)) for key, value in sources.items()}


def _serialize_actions() -> list[dict[str, Any]]:
    import src.classes.action  # noqa: F401
    import src.classes.mutual_action  # noqa: F401
    from src.classes.action.registry import ActionRegistry

    actions = []
    for action_cls in ActionRegistry.all_actual():
        params = getattr(action_cls, "PARAMS", {}) or {}
        actions.append(
            {
                "id": action_cls.__name__,
                "name": action_cls.get_action_name(),
                "desc": action_cls.get_desc(),
                "requirements": action_cls.get_requirements(),
                "params": _as_plain_dict(params),
                "param_sources": _param_sources_to_dict(action_cls),
                "cooldown_months": int(getattr(action_cls, "ACTION_CD_MONTHS", 0) or 0),
                "duration_months": int(getattr(action_cls, "duration_months", 0) or 0),
                "is_major": bool(getattr(action_cls, "IS_MAJOR", False)),
                "allow_gathering": bool(action_cls.can_gather()),
                "allow_world_events": bool(action_cls.can_trigger_events()),
                "module": action_cls.__module__,
                "meta": _category_meta("action", source="registry", tone="system"),
                "completeness": _build_completeness(
                    {
                        "name": action_cls.get_action_name(),
                        "desc": action_cls.get_desc(),
                        "requirements": action_cls.get_requirements(),
                    },
                    {
                        "params": params,
                    },
                ),
            }
        )
    return sorted(actions, key=lambda row: row["id"])


def _serialize_personas() -> list[dict[str, Any]]:
    from src.classes.persona import personas_by_id

    items = _structured_items(personas_by_id.values())
    for item in items:
        source = next((persona for persona in personas_by_id.values() if str(persona.id) == str(item.get("id"))), None)
        if source is None:
            continue
        item["rarity"] = _get_rarity_info(source)
        item["meta"] = _category_meta("persona", source="csv", tone="character")
        item["completeness"] = _build_completeness(
            {
                "name": item.get("name"),
                "desc": item.get("desc"),
                "rarity": item.get("rarity"),
            },
            {
                "condition": item.get("condition"),
            },
        )
        item["theme"] = _theme_for_rarity(item["rarity"]["level"] if item["rarity"] else None)
    return items


def _serialize_races() -> list[dict[str, Any]]:
    from src.classes.race import races_by_id

    items = sorted(
        [_as_plain_dict(race.get_info(detailed=True)) | {"weight": race.weight, "is_yao": race.is_yao} for race in races_by_id.values()],
        key=lambda row: str(row["id"]),
    )
    for item in items:
        item["meta"] = _category_meta("race", source="csv", tone="species")
        item["completeness"] = _build_completeness(
            {"id": item.get("id"), "name": item.get("name"), "desc": item.get("desc")},
            {"effect_desc": item.get("effect_desc")},
        )
        item["theme"] = "race-yao" if item.get("is_yao") else "race-human"
    return items


def _serialize_orthodoxies() -> list[dict[str, Any]]:
    from src.classes.core.orthodoxy import orthodoxy_by_id

    items = sorted(
        [_as_plain_dict(orthodoxy.get_info(detailed=True)) for orthodoxy in orthodoxy_by_id.values()],
        key=lambda row: str(row["id"]),
    )
    for item in items:
        item["meta"] = _category_meta("orthodoxy", source="csv", tone="system")
        item["completeness"] = _build_completeness(
            {"id": item.get("id"), "name": item.get("name"), "desc": item.get("desc")},
            {"effect_desc": item.get("effect_desc")},
        )
        item["theme"] = f"orthodoxy-{item.get('id')}"
    return items


def _serialize_techniques() -> list[dict[str, Any]]:
    from src.classes.technique import techniques_by_id

    items = _structured_items(techniques_by_id.values())
    for item in items:
        source = next((tech for tech in techniques_by_id.values() if str(tech.id) == str(item.get("id"))), None)
        if source is None:
            continue
        item["meta"] = _category_meta("technique", source="csv", tone="skill")
        item["rarity"] = _get_rarity_info(getattr(source, "grade", None))
        item["completeness"] = _build_completeness(
            {
                "name": item.get("name"),
                "desc": item.get("desc"),
                "attribute": item.get("attribute"),
                "grade": item.get("grade"),
            },
            {
                "realm": item.get("realm"),
                "effect_desc": item.get("effect_desc"),
            },
        )
        item["theme"] = _theme_for_grade(item.get("grade"))
    return items


def _serialize_sects() -> list[dict[str, Any]]:
    from src.classes.core.orthodoxy import get_orthodoxy
    from src.classes.core.sect import sects_by_id
    from src.classes.technique import techniques_by_name

    items: list[dict[str, Any]] = []
    for sect in sects_by_id.values():
        orthodoxy = get_orthodoxy(sect.orthodoxy_id)
        techniques = []
        for name in sect.technique_names:
            technique = techniques_by_name.get(name)
            techniques.append(technique.get_structured_info() if technique else {"name": name})
        item = {
                "id": sect.id,
                "name": sect.name,
                "name_id": sect.name_id,
                "desc": sect.desc,
                "alignment": str(sect.alignment),
                "orthodoxy_id": sect.orthodoxy_id,
                "orthodoxy_name": orthodoxy.get_info().get("name") if orthodoxy else sect.orthodoxy_id,
                "style": sect.get_identity_summary().get("style", ""),
                "headquarter": {
                    "name": sect.headquarter.name,
                    "desc": sect.headquarter.desc,
                },
                "preferred_weapon": str(sect.preferred_weapon) if sect.preferred_weapon else "",
                "effect_desc": sect.effect_desc,
                "rule_id": sect.rule_id,
                "rule_desc": sect.rule_desc,
                "accept_yao": sect.accept_yao,
                "color": sect.color,
                "techniques": _as_plain_dict({"items": techniques})["items"],
                "relations": {
                    "orthodoxy": orthodoxy.get_info().get("name") if orthodoxy else sect.orthodoxy_id,
                    "techniques": [tech.get("name") for tech in techniques if tech.get("name")],
                },
                "meta": _category_meta("sect", source="csv", tone="faction"),
                "completeness": _build_completeness(
                    {
                        "name": sect.name,
                        "desc": sect.desc,
                        "orthodoxy_id": sect.orthodoxy_id,
                        "member_act_style": sect.member_act_style,
                    },
                    {
                        "rule_desc": sect.rule_desc,
                        "preferred_weapon": sect.preferred_weapon,
                        "effect_desc": sect.effect_desc,
                    },
                ),
            }
        _attach_images(item, _sect_images(sect.id, sect.name))
        items.append(item)
    return sorted(items, key=lambda row: int(row["id"]))


def _serialize_items() -> dict[str, list[dict[str, Any]]]:
    from src.classes.items.auxiliary import auxiliaries_by_id
    from src.classes.items.elixir import elixirs_by_id
    from src.classes.items.weapon import weapons_by_id
    from src.classes.material import materials_by_id

    weapons = _structured_items(weapons_by_id.values())
    for item in weapons:
        item["meta"] = _category_meta("weapon", source="csv", tone="equipment")
        item["rarity"] = _get_rarity_info(next((w for w in weapons_by_id.values() if str(w.id) == str(item.get("id"))), None))
        item["completeness"] = _build_completeness({"name": item.get("name"), "desc": item.get("desc"), "realm": item.get("realm")})
        item["theme"] = _theme_for_grade(item.get("realm"))

    auxiliaries = _structured_items(auxiliaries_by_id.values())
    for item in auxiliaries:
        item["meta"] = _category_meta("auxiliary", source="csv", tone="equipment")
        item["rarity"] = _get_rarity_info(next((a for a in auxiliaries_by_id.values() if str(a.id) == str(item.get("id"))), None))
        item["completeness"] = _build_completeness({"name": item.get("name"), "desc": item.get("desc"), "realm": item.get("realm")})
        item["theme"] = _theme_for_grade(item.get("realm"))

    elixirs = _structured_items(elixirs_by_id.values())
    for item in elixirs:
        item["meta"] = _category_meta("elixir", source="csv", tone="consumable")
        item["rarity"] = _get_rarity_info(next((e for e in elixirs_by_id.values() if str(e.id) == str(item.get("id"))), None))
        item["completeness"] = _build_completeness({"name": item.get("name"), "desc": item.get("desc"), "realm": item.get("realm")})
        item["theme"] = _theme_for_grade(item.get("grade") or item.get("realm"))

    materials = _structured_items(materials_by_id.values())
    for item in materials:
        item["meta"] = _category_meta("material", source="csv", tone="resource")
        item["completeness"] = _build_completeness({"name": item.get("name"), "desc": item.get("desc"), "grade": item.get("grade")})
        item["theme"] = _theme_for_grade(item.get("grade"))

    return {
        "weapons": weapons,
        "auxiliaries": auxiliaries,
        "elixirs": elixirs,
        "materials": materials,
    }


def _serialize_resources() -> dict[str, list[dict[str, Any]]]:
    from src.classes.animal import animals_by_id
    from src.classes.environment.lode import lodes_by_id
    from src.classes.environment.plant import plants_by_id

    animals = _structured_items(animals_by_id.values())
    for item in animals:
        item["meta"] = _category_meta("animal", source="csv", tone="resource")
        item["completeness"] = _build_completeness({"name": item.get("name"), "desc": item.get("desc"), "grade": item.get("grade")})
        item["theme"] = _theme_for_grade(item.get("grade"))
        item["relations"] = _drop_relations(item)

    plants = _structured_items(plants_by_id.values())
    for item in plants:
        item["meta"] = _category_meta("plant", source="csv", tone="resource")
        item["completeness"] = _build_completeness({"name": item.get("name"), "desc": item.get("desc"), "grade": item.get("grade")})
        item["theme"] = _theme_for_grade(item.get("grade"))
        item["relations"] = _drop_relations(item)

    lodes = _structured_items(lodes_by_id.values())
    for item in lodes:
        item["meta"] = _category_meta("lode", source="csv", tone="resource")
        item["completeness"] = _build_completeness({"name": item.get("name"), "desc": item.get("desc"), "grade": item.get("grade")})
        item["theme"] = _theme_for_grade(item.get("grade"))
        item["relations"] = _drop_relations(item)

    return {
        "animals": animals,
        "plants": plants,
        "lodes": lodes,
    }


def _serialize_hidden_domains() -> list[dict[str, Any]]:
    from src.systems.cultivation import Realm
    from src.utils.df import get_float, get_int, get_str

    items: list[dict[str, Any]] = []
    for row in _csv_rows("hidden_domain"):
        required_realm = get_str(row, "required_realm")
        try:
            realm_display = str(Realm.from_str(required_realm))
        except Exception:
            realm_display = required_realm
        item = {
            **row,
            "name": get_str(row, "name"),
            "desc": get_str(row, "desc"),
            "required_realm": realm_display,
            "danger_prob": get_float(row, "danger_prob"),
            "hp_loss_percent": get_float(row, "hp_loss_percent"),
            "drop_prob": get_float(row, "drop_prob"),
            "cd_years": get_int(row, "cd_years"),
            "open_prob": get_float(row, "open_prob"),
            "meta": _category_meta("hidden_domain", source="csv", tone="domain"),
            "completeness": _build_completeness(
                {
                    "id": get_str(row, "id"),
                    "name": get_str(row, "name"),
                    "desc": get_str(row, "desc"),
                    "required_realm": required_realm,
                }
            ),
            "theme": _theme_for_grade(required_realm) or "domain",
        }
        items.append(item)
    return sorted(items, key=lambda row: str(row.get("id", "")))


def _serialize_sect_tasks() -> list[dict[str, Any]]:
    from src.i18n import t
    from src.systems.cultivation import Realm
    from src.utils.df import get_float, get_int, get_list_str, get_str

    realm_suffixes = {
        "qi": Realm.Qi_Refinement,
        "foundation": Realm.Foundation_Establishment,
        "core": Realm.Core_Formation,
        "nascent": Realm.Nascent_Soul,
    }
    items: list[dict[str, Any]] = []
    for row in _csv_rows("sect_task"):
        task_id = get_str(row, "id")
        raw_allowed_realms = get_list_str(row, "allowed_realms")
        allowed_realms: list[str] = []
        for raw_realm in raw_allowed_realms:
            try:
                allowed_realms.append(str(Realm.from_str(raw_realm)))
            except Exception:
                allowed_realms.append(raw_realm)

        success_by_realm: dict[str, float] = {}
        stone_reward_by_realm: dict[str, int] = {}
        contribution_reward_by_realm: dict[str, int] = {}
        fail_damage_by_realm: dict[str, float] = {}
        for suffix, realm in realm_suffixes.items():
            realm_name = str(realm)
            success_by_realm[realm_name] = get_float(row, f"base_success_{suffix}", 0.0)
            stone_reward_by_realm[realm_name] = get_int(row, f"reward_stone_per_month_{suffix}", 0)
            contribution_reward_by_realm[realm_name] = get_int(row, f"reward_contribution_per_month_{suffix}", 0)
            fail_damage_by_realm[realm_name] = get_float(row, f"fail_damage_ratio_{suffix}", 0.0)

        title = t(f"sect_task_title_{task_id}", default=get_str(row, "title"))
        item = {
            "id": task_id,
            "name": title,
            "title": title,
            "category": get_str(row, "category"),
            "issuer_type": get_str(row, "issuer_type", "both") or "both",
            "min_duration": get_int(row, "min_duration"),
            "max_duration": get_int(row, "max_duration"),
            "allowed_realms": allowed_realms,
            "base_success": success_by_realm,
            "reward_stone_per_month": stone_reward_by_realm,
            "reward_contribution_per_month": contribution_reward_by_realm,
            "fail_damage_ratio": fail_damage_by_realm,
            "weight": get_float(row, "weight", 1.0),
            "meta": _category_meta("sect_task", source="csv", tone="faction"),
            "completeness": _build_completeness(
                {
                    "id": task_id,
                    "title": title,
                    "category": get_str(row, "category"),
                    "allowed_realms": allowed_realms,
                }
            ),
            "theme": "sect-task",
        }
        items.append(item)
    return sorted(items, key=lambda row: str(row.get("id", "")))


def _csv_rows(config_name: str) -> list[dict[str, Any]]:
    from src.utils.df import game_configs

    return [_as_plain_dict(row) for row in game_configs.get(config_name, [])]


def _serialize_regions() -> dict[str, list[dict[str, Any]]]:
    from src.i18n import t

    regions = {
        "normal": {
            "title": t("Normal Region (can hunt, gather, mine)"),
            "items": _csv_rows("normal_region"),
        },
        "cultivate": {
            "title": t("Cultivate Region (can respire to increase cultivation)"),
            "items": _csv_rows("cultivate_region"),
        },
        "city": {
            "title": t("City Region"),
            "items": _csv_rows("city_region"),
        },
        "sect": {
            "title": t("Sect Headquarters (sect disciples heal faster here)"),
            "items": _csv_rows("sect_region"),
        },
    }
    for group_name, group in regions.items():
        for row in group["items"]:
            row["meta"] = _category_meta(f"{group_name}_region", source="csv", tone="map")
            row["completeness"] = _build_completeness({"name": row.get("name"), "desc": row.get("desc")})
            row["theme"] = f"region-{group_name}"
            if group_name == "normal":
                _attach_images(row, _normal_region_images(row.get("id"), str(row.get("name") or "")))
            elif group_name == "cultivate":
                _attach_images(row, _cultivate_region_images(row.get("sub_type"), str(row.get("name") or "")))
            elif group_name == "city":
                _attach_images(row, _city_region_images(row.get("id"), str(row.get("name") or "")))
            elif group_name == "sect":
                _attach_images(row, _sect_images(row.get("sect_id"), str(row.get("name") or "")))
    return regions


def _tab(title: str, kind: str, items: Any) -> dict[str, Any]:
    return {"title": title, "kind": kind, "items": items}


def build_wiki_payload(locale: str) -> dict[str, Any]:
    from src.classes.language import language_manager

    previous_locale = str(language_manager)
    language_manager.set_language(locale)
    try:
        item_tabs = _serialize_items()
        resource_tabs = _serialize_resources()
        return {
            "locale": locale,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tabs": {
                "world": _tab("World Info", "list", _serialize_world_info()),
                "actions": _tab("Actions", "list", _serialize_actions()),
                "personas": _tab("Persona", "list", _serialize_personas()),
                "sects": _tab("Sects", "list", _serialize_sects()),
                "sect_tasks": _tab("Sect Tasks", "list", _serialize_sect_tasks()),
                "orthodoxies": _tab("Orthodoxies", "list", _serialize_orthodoxies()),
                "races": _tab("Races", "list", _serialize_races()),
                "techniques": _tab("Techniques", "list", _serialize_techniques()),
                "weapons": _tab("Weapons", "list", item_tabs["weapons"]),
                "auxiliaries": _tab("Auxiliaries", "list", item_tabs["auxiliaries"]),
                "elixirs": _tab("Elixirs", "list", item_tabs["elixirs"]),
                "materials": _tab("Materials", "list", item_tabs["materials"]),
                "animals": _tab("Animals", "list", resource_tabs["animals"]),
                "plants": _tab("Plants", "list", resource_tabs["plants"]),
                "lodes": _tab("Lodes", "list", resource_tabs["lodes"]),
                "hidden_domains": _tab("Hidden Domains", "list", _serialize_hidden_domains()),
                "regions": _tab("Regions", "groups", _serialize_regions()),
            },
        }
    finally:
        if previous_locale != locale:
            language_manager.set_language(previous_locale)


def _copy_static_assets(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(TOOL_ROOT / "index.html", output_dir / "index.html")
    src_dir = output_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("app.js", "styles.css"):
        shutil.copy2(TOOL_ROOT / "src" / filename, src_dir / filename)


def _iter_payload_asset_sources(value: Any) -> Iterable[Path]:
    if isinstance(value, dict):
        src = value.get("src")
        if isinstance(src, str) and src.startswith("./assets/"):
            yield ASSETS_ROOT / src.removeprefix("./assets/")
        for child in value.values():
            yield from _iter_payload_asset_sources(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_payload_asset_sources(child)


def _copy_payload_assets(output_dir: Path, payloads: Iterable[dict[str, Any]]) -> None:
    assets_dir = output_dir / "assets"
    if assets_dir.exists():
        shutil.rmtree(assets_dir)

    copied: set[Path] = set()
    for payload in payloads:
        for source in _iter_payload_asset_sources(payload):
            if not source.exists() or source in copied:
                continue
            try:
                relative = source.relative_to(ASSETS_ROOT)
            except ValueError:
                continue
            target = assets_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.add(source)


def generate(output_dir: Path = DEFAULT_OUTPUT_DIR) -> list[str]:
    _ensure_project_importable()

    from src.i18n.locale_registry import get_locale_entries

    output_dir = output_dir.resolve()
    data_dir = output_dir / "data"
    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    _copy_static_assets(output_dir)

    locale_entries = get_locale_entries(enabled_only=True)
    registry = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "default_locale": next((entry["code"] for entry in locale_entries if entry.get("source_of_truth")), locale_entries[0]["code"]),
        "locales": locale_entries,
    }
    (data_dir / "registry.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")

    generated: list[str] = []
    payloads: list[dict[str, Any]] = []
    for entry in locale_entries:
        locale = str(entry["code"])
        payload = build_wiki_payload(locale)
        payloads.append(payload)
        (data_dir / f"{locale}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")
        generated.append(locale)
    _copy_payload_assets(output_dir, payloads)
    return generated


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the local cultivation-world wiki.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output directory. Defaults to tools/wiki/dist.")
    args = parser.parse_args()

    generated = generate(args.out)
    print(f"Generated wiki for {len(generated)} locale(s): {', '.join(generated)}")
    print(f"Output: {args.out.resolve()}")


if __name__ == "__main__":
    main()
