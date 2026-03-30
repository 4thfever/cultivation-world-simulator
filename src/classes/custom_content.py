from __future__ import annotations

from typing import Any

from src.classes.effect import format_effects_to_text
from src.classes.items.auxiliary import Auxiliary, auxiliaries_by_id, auxiliaries_by_name
from src.classes.items.registry import ItemRegistry
from src.classes.items.weapon import Weapon, weapons_by_id, weapons_by_name
from src.classes.technique import (
    Technique,
    TechniqueAttribute,
    TechniqueGrade,
    techniques_by_id,
    techniques_by_name,
)
from src.classes.weapon_type import WeaponType
from src.systems.cultivation import Realm


CUSTOM_ID_START = {
    "technique": 900001,
    "weapon": 910001,
    "auxiliary": 920001,
}


def is_custom_content_id(item_id: int | str | None) -> bool:
    try:
        value = int(item_id)
    except (TypeError, ValueError):
        return False
    return value >= min(CUSTOM_ID_START.values())


class CustomContentRegistry:
    custom_techniques_by_id: dict[int, Technique] = {}
    custom_weapons_by_id: dict[int, Weapon] = {}
    custom_auxiliaries_by_id: dict[int, Auxiliary] = {}
    next_ids: dict[str, int] = dict(CUSTOM_ID_START)

    @classmethod
    def reset(cls) -> None:
        for item_id, technique in list(cls.custom_techniques_by_id.items()):
            techniques_by_id.pop(item_id, None)
            techniques_by_name.pop(technique.name, None)
        cls.custom_techniques_by_id.clear()

        for item_id, weapon in list(cls.custom_weapons_by_id.items()):
            weapons_by_id.pop(item_id, None)
            weapons_by_name.pop(weapon.name, None)
            ItemRegistry.unregister(item_id)
        cls.custom_weapons_by_id.clear()

        for item_id, auxiliary in list(cls.custom_auxiliaries_by_id.items()):
            auxiliaries_by_id.pop(item_id, None)
            auxiliaries_by_name.pop(auxiliary.name, None)
            ItemRegistry.unregister(item_id)
        cls.custom_auxiliaries_by_id.clear()

        cls.next_ids = dict(CUSTOM_ID_START)

    @classmethod
    def allocate_id(cls, category: str) -> int:
        next_id = int(cls.next_ids.get(category, CUSTOM_ID_START[category]))
        cls.next_ids[category] = next_id + 1
        return next_id

    @classmethod
    def register_technique(cls, technique: Technique) -> Technique:
        cls.custom_techniques_by_id[technique.id] = technique
        techniques_by_id[technique.id] = technique
        techniques_by_name[technique.name] = technique
        return technique

    @classmethod
    def register_weapon(cls, weapon: Weapon) -> Weapon:
        cls.custom_weapons_by_id[weapon.id] = weapon
        weapons_by_id[weapon.id] = weapon
        weapons_by_name[weapon.name] = weapon
        ItemRegistry.register(weapon.id, weapon)
        return weapon

    @classmethod
    def register_auxiliary(cls, auxiliary: Auxiliary) -> Auxiliary:
        cls.custom_auxiliaries_by_id[auxiliary.id] = auxiliary
        auxiliaries_by_id[auxiliary.id] = auxiliary
        auxiliaries_by_name[auxiliary.name] = auxiliary
        ItemRegistry.register(auxiliary.id, auxiliary)
        return auxiliary

    @classmethod
    def to_save_dict(cls) -> dict[str, Any]:
        return {
            "techniques": [cls._serialize_technique(item) for item in cls.custom_techniques_by_id.values()],
            "weapons": [cls._serialize_weapon(item) for item in cls.custom_weapons_by_id.values()],
            "auxiliaries": [cls._serialize_auxiliary(item) for item in cls.custom_auxiliaries_by_id.values()],
            "next_ids": dict(cls.next_ids),
        }

    @classmethod
    def load_from_dict(cls, data: dict[str, Any] | None) -> None:
        cls.reset()
        payload = data if isinstance(data, dict) else {}
        raw_next_ids = dict(payload.get("next_ids", {}) or {})
        for category, start_value in CUSTOM_ID_START.items():
            raw_value = raw_next_ids.get(category, start_value)
            try:
                cls.next_ids[category] = max(int(raw_value), start_value)
            except (TypeError, ValueError):
                cls.next_ids[category] = start_value

        for item_data in list(payload.get("techniques", []) or []):
            technique = cls._deserialize_technique(item_data)
            if technique is not None:
                cls.register_technique(technique)

        for item_data in list(payload.get("weapons", []) or []):
            weapon = cls._deserialize_weapon(item_data)
            if weapon is not None:
                cls.register_weapon(weapon)

        for item_data in list(payload.get("auxiliaries", []) or []):
            auxiliary = cls._deserialize_auxiliary(item_data)
            if auxiliary is not None:
                cls.register_auxiliary(auxiliary)

        if cls.custom_techniques_by_id:
            cls.next_ids["technique"] = max(cls.next_ids["technique"], max(cls.custom_techniques_by_id) + 1)
        if cls.custom_weapons_by_id:
            cls.next_ids["weapon"] = max(cls.next_ids["weapon"], max(cls.custom_weapons_by_id) + 1)
        if cls.custom_auxiliaries_by_id:
            cls.next_ids["auxiliary"] = max(cls.next_ids["auxiliary"], max(cls.custom_auxiliaries_by_id) + 1)

    @staticmethod
    def _serialize_technique(item: Technique) -> dict[str, Any]:
        return {
            "id": int(item.id),
            "name": str(item.name),
            "attribute": item.attribute.value,
            "grade": item.grade.value,
            "realm": item.realm.value if item.realm is not None else None,
            "desc": str(item.desc),
            "weight": float(item.weight),
            "condition": str(item.condition or ""),
            "sect_id": item.sect_id,
            "effects": dict(item.effects or {}),
        }

    @staticmethod
    def _serialize_weapon(item: Weapon) -> dict[str, Any]:
        return {
            "id": int(item.id),
            "name": str(item.name),
            "weapon_type": item.weapon_type.value,
            "realm": item.realm.value,
            "desc": str(item.desc),
            "effects": dict(item.effects or {}),
        }

    @staticmethod
    def _serialize_auxiliary(item: Auxiliary) -> dict[str, Any]:
        return {
            "id": int(item.id),
            "name": str(item.name),
            "realm": item.realm.value,
            "desc": str(item.desc),
            "effects": dict(item.effects or {}),
        }

    @staticmethod
    def _deserialize_technique(data: dict[str, Any]) -> Technique | None:
        try:
            effects = dict(data.get("effects", {}) or {})
            return Technique(
                id=int(data["id"]),
                name=str(data["name"]),
                attribute=TechniqueAttribute(str(data["attribute"])),
                grade=TechniqueGrade.from_str(str(data["grade"])),
                realm=Realm.from_str(str(data["realm"])) if data.get("realm") else None,
                desc=str(data.get("desc", "") or ""),
                weight=float(data.get("weight", 0.0) or 0.0),
                condition=str(data.get("condition", "") or ""),
                sect_id=data.get("sect_id"),
                effects=effects,
                effect_desc=format_effects_to_text(effects),
            )
        except Exception:
            return None

    @staticmethod
    def _deserialize_weapon(data: dict[str, Any]) -> Weapon | None:
        try:
            effects = dict(data.get("effects", {}) or {})
            return Weapon(
                id=int(data["id"]),
                name=str(data["name"]),
                weapon_type=WeaponType.from_str(str(data["weapon_type"])),
                realm=Realm.from_str(str(data["realm"])),
                desc=str(data.get("desc", "") or ""),
                effects=effects,
                effect_desc=format_effects_to_text(effects),
            )
        except Exception:
            return None

    @staticmethod
    def _deserialize_auxiliary(data: dict[str, Any]) -> Auxiliary | None:
        try:
            effects = dict(data.get("effects", {}) or {})
            return Auxiliary(
                id=int(data["id"]),
                name=str(data["name"]),
                realm=Realm.from_str(str(data["realm"])),
                desc=str(data.get("desc", "") or ""),
                effects=effects,
                effect_desc=format_effects_to_text(effects),
            )
        except Exception:
            return None
