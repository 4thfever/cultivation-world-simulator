from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from fastapi import HTTPException

from src.classes.custom_content import CustomContentRegistry, is_custom_content_id
from src.classes.language import language_manager
from src.classes.effect import (
    ALL_EFFECTS,
    LEGAL_ACTIONS,
    format_effects_to_text,
)
from src.classes.effect.desc import get_effect_desc
from src.classes.effect import consts as effect_consts
from src.classes.items.auxiliary import Auxiliary, auxiliaries_by_id
from src.classes.items.weapon import Weapon, weapons_by_id
from src.classes.technique import (
    Technique,
    TechniqueAttribute,
    TechniqueGrade,
    techniques_by_id,
)
from src.classes.weapon_type import WeaponType
from src.systems.cultivation import Realm
from src.utils.config import CONFIG
from src.utils.llm.client import call_llm_with_task_name


CustomCategory = Literal["technique", "weapon", "auxiliary"]
FORBIDDEN_EFFECT_KEYS = {
    LEGAL_ACTIONS,
}

_EXAMPLE_VALUES = {
    "extra_battle_strength_points": 3,
    "extra_max_hp": 30,
    "extra_observation_radius": 1,
    "extra_appearance": 1,
    "extra_respire_exp": 20,
    "extra_respire_exp_multiplier": 0.2,
    "respire_duration_reduction": 0.1,
    "temper_duration_reduction": 0.1,
    "extra_breakthrough_success_rate": 0.1,
    "extra_retreat_success_rate": 0.1,
    "extra_dual_cultivation_exp": 50,
    "extra_harvest_materials": 1,
    "extra_hunt_materials": 1,
    "extra_mine_materials": 1,
    "extra_plant_income": 20,
    "extra_move_step": 1,
    "extra_catch_success_rate": 0.1,
    "extra_escape_success_rate": 0.1,
    "extra_assassinate_success_rate": 0.1,
    "extra_luck": 2,
    "extra_fortune_probability": 0.1,
    "extra_misfortune_probability": -0.1,
    "extra_cast_success_rate": 0.1,
    "extra_refine_success_rate": 0.1,
    "extra_sect_mission_success_rate": 0.1,
    "extra_weapon_proficiency_gain": 0.2,
    "extra_weapon_upgrade_chance": 0.1,
    "extra_max_lifespan": 10,
    "extra_hp_recovery_rate": 0.2,
    "damage_reduction": 0.1,
    "realm_suppression_bonus": 0.05,
    "extra_item_sell_price_multiplier": 0.2,
    "shop_buy_price_reduction": 0.1,
    "extra_plunder_multiplier": 0.5,
    "extra_hidden_domain_drop_prob": 0.1,
    "extra_hidden_domain_danger_prob": -0.1,
    "extra_epiphany_probability": 0.05,
}

_REFERENCE_LABEL_MAP = {
    "微量": "small",
    "中量": "medium",
    "大量": "large",
    "极限": "cap",
    "极高": "very high",
    "基础概率": "base chance",
    "基础值": "base value",
    "普通人": "ordinary",
    "有福缘": "fortunate",
    "主角模板": "protagonist-tier",
    "倒霉体质": "unlucky",
    "坦克": "tanky",
    "奸商": "profit-focused",
    "降低危险": "safer",
    "增加危险": "riskier",
    "天才": "talent-tier",
}


_PROMPT_I18N = {
    "zh-CN": {
        "categories": {
            "technique": "功法",
            "weapon": "兵器",
            "auxiliary": "辅助装备",
        },
        "labels": {
            "name": "名称",
            "desc": "描述",
            "attribute": "属性",
            "grade": "品阶",
            "weapon_type": "兵器类型",
            "realm": "境界",
            "effect_desc": "效果说明",
            "effects": "effects",
            "value_type": "值类型",
            "example": "示例",
            "magnitude_guidance": "量级参考",
            "same_type_reference": "同类型参考资料：",
            "same_type_same_realm_reference": "同类型、同境界参考资料：",
            "scope_without_realm": "这是一个新的{category_label}，不需要额外指定境界。",
            "scope_with_realm": "这是一个“{realm}”层级的{category_label}。",
        },
    },
    "en-US": {
        "categories": {
            "technique": "technique",
            "weapon": "weapon",
            "auxiliary": "auxiliary equipment",
        },
        "labels": {
            "name": "Name",
            "desc": "Description",
            "attribute": "Attribute",
            "grade": "Grade",
            "weapon_type": "Weapon Type",
            "realm": "Realm",
            "effect_desc": "Effect Summary",
            "effects": "effects",
            "value_type": "value type",
            "example": "example",
            "magnitude_guidance": "magnitude guidance",
            "same_type_reference": "Reference items of the same category:",
            "same_type_same_realm_reference": "Reference items of the same category and realm:",
            "scope_without_realm": "This is a new {category_label}; no realm needs to be specified.",
            "scope_with_realm": "This is a {category_label} at the \"{realm}\" realm tier.",
        },
    },
    "zh-TW": {
        "categories": {
            "technique": "功法",
            "weapon": "兵器",
            "auxiliary": "輔助裝備",
        },
        "labels": {
            "name": "名稱",
            "desc": "描述",
            "attribute": "屬性",
            "grade": "品階",
            "weapon_type": "兵器類型",
            "realm": "境界",
            "effect_desc": "效果說明",
            "effects": "effects",
            "value_type": "值類型",
            "example": "示例",
            "magnitude_guidance": "量級參考",
            "same_type_reference": "同類型參考資料：",
            "same_type_same_realm_reference": "同類型、同境界參考資料：",
            "scope_without_realm": "這是一個新的{category_label}，不需要額外指定境界。",
            "scope_with_realm": "這是一個「{realm}」層級的{category_label}。",
        },
    },
    "vi-VN": {
        "categories": {
            "technique": "công pháp",
            "weapon": "binh khí",
            "auxiliary": "trang bị phụ trợ",
        },
        "labels": {
            "name": "Tên",
            "desc": "Mô tả",
            "attribute": "Thuộc tính",
            "grade": "Phẩm cấp",
            "weapon_type": "Loại binh khí",
            "realm": "Cảnh giới",
            "effect_desc": "Tóm tắt hiệu ứng",
            "effects": "effects",
            "value_type": "kiểu giá trị",
            "example": "ví dụ",
            "magnitude_guidance": "mức độ tham khảo",
            "same_type_reference": "Tư liệu tham khảo cùng loại:",
            "same_type_same_realm_reference": "Tư liệu tham khảo cùng loại và cùng cảnh giới:",
            "scope_without_realm": "Đây là một {category_label} mới, không cần chỉ định thêm cảnh giới.",
            "scope_with_realm": "Đây là một {category_label} thuộc tầng cảnh giới \"{realm}\".",
        },
    },
}


def _get_prompt_locale() -> str:
    lang = str(language_manager.current)
    return lang if lang in _PROMPT_I18N else "zh-CN"


def _prompt_text(key: str) -> str:
    locale = _get_prompt_locale()
    return str(_PROMPT_I18N.get(locale, _PROMPT_I18N["zh-CN"])["labels"][key])


def _category_label(category: CustomCategory) -> str:
    locale = _get_prompt_locale()
    return str(_PROMPT_I18N.get(locale, _PROMPT_I18N["zh-CN"])["categories"][category])


def _format_effect_examples() -> str:
    lines: list[str] = []
    reference_text_map = _load_effect_reference_text_map()
    for effect_key in ALL_EFFECTS:
        if effect_key in FORBIDDEN_EFFECT_KEYS:
            continue
        effect_name = get_effect_desc(effect_key)
        example = _EXAMPLE_VALUES.get(effect_key, 1)
        type_name = type(example).__name__
        reference_text = reference_text_map.get(effect_key, "")
        if reference_text:
            lines.append(
                f"- {effect_key}: {effect_name}, {_prompt_text('value_type')} {type_name}, {_prompt_text('example')} {example}. {_prompt_text('magnitude_guidance')}: {reference_text}"
            )
        else:
            lines.append(f"- {effect_key}: {effect_name}, {_prompt_text('value_type')} {type_name}, {_prompt_text('example')} {example}")
    return "\n".join(lines)


@lru_cache(maxsize=1)
def _load_effect_reference_text_map() -> dict[str, str]:
    source_path = Path(effect_consts.__file__ or "")
    if not source_path.exists():
        return {}

    text = source_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r'^[A-Z0-9_]+\s*=\s*"(?P<effect_key>[^"]+)"\s*\n"""(?P<doc>.*?)"""',
        re.MULTILINE | re.DOTALL,
    )

    result: dict[str, str] = {}
    for match in pattern.finditer(text):
        effect_key = match.group("effect_key").strip()
        doc = match.group("doc")
        reference_text = _extract_reference_text(doc)
        if reference_text:
            result[effect_key] = reference_text
    return result


def _extract_reference_text(doc: str) -> str:
    marker = "数值参考"
    if marker not in doc:
        return ""

    lines = [line.rstrip() for line in doc.splitlines()]
    collecting = False
    collected: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not collecting:
            if line.startswith(marker):
                collecting = True
            continue

        if not line:
            if collected:
                break
            continue

        if line.startswith("说明:") or line.startswith("类型:") or line.startswith("结算:") or line.startswith("限制:"):
            if collected:
                break
            continue

        if line.startswith("-"):
            normalized = _normalize_reference_line(line.lstrip("-").strip())
            if normalized:
                collected.append(normalized)
        elif collected:
            break

    return "; ".join(collected)


def _normalize_reference_line(line: str) -> str:
    line = _strip_parenthetical_text(line)
    if ":" not in line:
        return _normalize_spacing(line)

    label, value = line.split(":", 1)
    label = _REFERENCE_LABEL_MAP.get(label.strip(), _normalize_label(label))
    value = _normalize_value_text(value)
    if value:
        return f"{label}: {value}"
    return label


def _strip_parenthetical_text(text: str) -> str:
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"（[^）]*）", "", text)
    return _normalize_spacing(text)


def _normalize_label(label: str) -> str:
    normalized = _normalize_spacing(label).lower()
    normalized = normalized.replace("%", " percent")
    normalized = normalized.replace("+", " plus ")
    normalized = re.sub(r"[^a-z0-9._\-/ ]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _normalize_value_text(value: str) -> str:
    value = _normalize_spacing(value)
    value = value.replace("~", " to ")
    value = value.replace("～", " to ")
    value = value.replace("，", ", ")
    value = value.replace("、", ", ")
    value = value.replace("％", "%")
    value = value.replace("−", "-")
    value = re.sub(r"\s+", " ", value).strip(" .;")
    return value


def _normalize_spacing(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _serialize_reference_item(item: Technique | Weapon | Auxiliary, category: CustomCategory) -> str:
    base = [
        f"{_prompt_text('name')}: {item.name}",
        f"{_prompt_text('desc')}: {item.desc}",
    ]
    if category == "technique":
        technique = item
        base.append(f"{_prompt_text('attribute')}: {technique.attribute.value}")
        base.append(f"{_prompt_text('grade')}: {technique.grade.value}")
    elif category == "weapon":
        weapon = item
        base.append(f"{_prompt_text('weapon_type')}: {weapon.weapon_type.value}")
        base.append(f"{_prompt_text('realm')}: {weapon.realm.value}")
    else:
        auxiliary = item
        base.append(f"{_prompt_text('realm')}: {auxiliary.realm.value}")

    if item.effect_desc:
        base.append(f"{_prompt_text('effect_desc')}: {item.effect_desc}")
    if item.effects:
        base.append(f"{_prompt_text('effects')}: {item.effects}")
    return "; ".join(base)


def build_reference_items_text(category: CustomCategory, realm: Realm | None, *, limit: int = 8) -> str:
    if category == "technique":
        items = list(techniques_by_id.values())
    elif category == "weapon":
        if realm is None:
            raise HTTPException(status_code=400, detail="realm is required for weapon generation")
        exact_matches = [item for item in weapons_by_id.values() if item.realm == realm]
        items = exact_matches or list(weapons_by_id.values())
    else:
        if realm is None:
            raise HTTPException(status_code=400, detail="realm is required for auxiliary generation")
        exact_matches = [item for item in auxiliaries_by_id.values() if item.realm == realm]
        items = exact_matches or list(auxiliaries_by_id.values())

    items = sorted(items, key=lambda item: (is_custom_content_id(getattr(item, "id", 0)), getattr(item, "id", 0)))
    return "\n".join(
        f"{idx}. {_serialize_reference_item(item, category)}"
        for idx, item in enumerate(items[:limit], start=1)
    )


def validate_custom_effects(effects: object) -> dict[str, object]:
    if not isinstance(effects, dict) or not effects:
        raise HTTPException(status_code=400, detail="effects must be a non-empty object")

    validated: dict[str, object] = {}
    allowed_keys = set(ALL_EFFECTS) - FORBIDDEN_EFFECT_KEYS
    for key, value in effects.items():
        if key not in allowed_keys:
            raise HTTPException(status_code=400, detail=f"Unsupported custom effect: {key}")
        if key in {"when", "_desc"}:
            raise HTTPException(status_code=400, detail=f"Unsupported custom effect field: {key}")
        if isinstance(value, str):
            if "avatar." in value or value.strip().startswith("eval("):
                raise HTTPException(status_code=400, detail=f"Dynamic effect value is not allowed: {key}")
            raise HTTPException(status_code=400, detail=f"String effect value is not allowed: {key}")
        if isinstance(value, list):
            raise HTTPException(status_code=400, detail=f"List effect value is not allowed: {key}")
        if not isinstance(value, (int, float, bool)):
            raise HTTPException(status_code=400, detail=f"Unsupported effect value type: {key}")
        validated[str(key)] = value
    return validated


def normalize_custom_draft(category: CustomCategory, draft: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(draft, dict):
        raise HTTPException(status_code=400, detail="draft must be an object")

    name = str(draft.get("name", "") or "").strip()
    desc = str(draft.get("desc", "") or "").strip()
    if not name or not desc:
        raise HTTPException(status_code=400, detail="name and desc are required")

    effects = validate_custom_effects(draft.get("effects"))

    normalized: dict[str, Any] = {
        "category": category,
        "name": name,
        "desc": desc,
        "effects": effects,
        "effect_desc": format_effects_to_text(effects),
        "is_custom": True,
    }

    if category == "technique":
        try:
            normalized["attribute"] = TechniqueAttribute(str(draft.get("attribute", "GOLD"))).value
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid technique attribute") from exc
        normalized["grade"] = TechniqueGrade.from_str(str(draft.get("grade", "LOWER"))).value
    elif category == "weapon":
        realm_raw = draft.get("realm")
        if not realm_raw:
            raise HTTPException(status_code=400, detail="realm is required for weapon")
        normalized["realm"] = Realm.from_str(str(realm_raw)).value
        normalized["weapon_type"] = WeaponType.from_str(str(draft.get("weapon_type", "SWORD"))).value
    else:
        realm_raw = draft.get("realm")
        if not realm_raw:
            raise HTTPException(status_code=400, detail="realm is required for auxiliary")
        normalized["realm"] = Realm.from_str(str(realm_raw)).value

    return normalized


async def generate_custom_content_draft(category: CustomCategory, realm: Realm | None, user_prompt: str) -> dict[str, Any]:
    prompt = str(user_prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="user_prompt is required")

    template_path = CONFIG.paths.templates / "custom_content.txt"
    if not template_path.exists():
        template_path = CONFIG.paths.locales / "zh-CN" / "templates" / "custom_content.txt"

    infos = {
        "category_label": _category_label(category),
        "scope_hint": _prompt_text("scope_with_realm").format(realm=str(realm), category_label=_category_label(category))
        if realm is not None
        else _prompt_text("scope_without_realm").format(category_label=_category_label(category)),
        "reference_hint": _prompt_text("same_type_same_realm_reference")
        if realm is not None
        else _prompt_text("same_type_reference"),
        "user_prompt": prompt,
        "reference_items": build_reference_items_text(category, realm),
        "allowed_effects": _format_effect_examples(),
    }
    result = await call_llm_with_task_name(
        task_name="custom_content_generation",
        template_path=template_path,
        infos=infos,
        max_retries=2,
    )
    if not isinstance(result, dict):
        raise HTTPException(status_code=500, detail="LLM draft result is invalid")

    if realm is not None:
        result["realm"] = realm.value
    return normalize_custom_draft(category, result)


def create_custom_content_from_draft(category: CustomCategory, draft: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_custom_draft(category, draft)
    effects = dict(normalized["effects"])
    if category == "technique":
        item = Technique(
            id=CustomContentRegistry.allocate_id("technique"),
            name=normalized["name"],
            attribute=TechniqueAttribute(str(normalized["attribute"])),
            grade=TechniqueGrade.from_str(str(normalized["grade"])),
            desc=normalized["desc"],
            weight=0.0,
            condition="",
            realm=None,
            sect_id=None,
            effects=effects,
            effect_desc=normalized["effect_desc"],
        )
        CustomContentRegistry.register_technique(item)
    elif category == "weapon":
        realm = Realm.from_str(normalized["realm"])
        item = Weapon(
            id=CustomContentRegistry.allocate_id("weapon"),
            name=normalized["name"],
            weapon_type=WeaponType.from_str(str(normalized["weapon_type"])),
            realm=realm,
            desc=normalized["desc"],
            effects=effects,
            effect_desc=normalized["effect_desc"],
        )
        CustomContentRegistry.register_weapon(item)
    else:
        realm = Realm.from_str(normalized["realm"])
        item = Auxiliary(
            id=CustomContentRegistry.allocate_id("auxiliary"),
            name=normalized["name"],
            realm=realm,
            desc=normalized["desc"],
            effects=effects,
            effect_desc=normalized["effect_desc"],
        )
        CustomContentRegistry.register_auxiliary(item)

    payload = item.get_structured_info()
    payload["id"] = int(payload["id"])
    payload["is_custom"] = True
    if "realm" in normalized:
        payload["realm"] = normalized["realm"]
    return payload
