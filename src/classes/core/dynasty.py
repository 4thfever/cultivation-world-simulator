from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.classes.effect import load_effect_from_str
from src.classes.effect.desc import format_effects_to_text
from src.i18n import t
from src.utils.config import CONFIG
from src.utils.df import game_configs, get_float, get_int, get_str


@dataclass
class Emperor:
    surname: str
    given_name: str
    birth_month_stamp: int
    max_age: int = 80
    is_dead: bool = False

    @property
    def name(self) -> str:
        return f"{self.surname}{self.given_name}"

    def get_age(self, current_month_stamp: int) -> int:
        return max(0, (int(current_month_stamp) - int(self.birth_month_stamp)) // 12)

    def should_die(self, current_month_stamp: int) -> bool:
        return self.get_age(current_month_stamp) >= int(self.max_age)

    def to_dict(self) -> dict[str, Any]:
        return {
            "surname": str(self.surname or ""),
            "given_name": str(self.given_name or ""),
            "birth_month_stamp": int(self.birth_month_stamp),
            "max_age": int(self.max_age),
            "is_dead": bool(self.is_dead),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Emperor":
        return cls(
            surname=str(data.get("surname", "") or ""),
            given_name=str(data.get("given_name", "") or ""),
            birth_month_stamp=int(data.get("birth_month_stamp", 0) or 0),
            max_age=int(data.get("max_age", 80) or 80),
            is_dead=bool(data.get("is_dead", False)),
        )


@dataclass
class Dynasty:
    id: int
    name: str
    desc: str
    template_name: str = ""
    royal_surname: str = ""
    effect_desc: str = ""
    effects: dict[str, Any] = field(default_factory=dict)
    style_tag: str = ""
    official_preference_type: str = ""
    official_preference_value: str = ""
    weight: float = 1.0
    is_low_magic: bool = True
    current_emperor: Emperor | None = None

    def _get_localized_template(self) -> "Dynasty | None":
        template = dynasties_by_id.get(int(self.id))
        if template is None or template is self:
            return None
        if not self._matches_template_identity(template):
            return None
        return template

    def _matches_template_identity(self, template: "Dynasty") -> bool:
        source_name = source_dynasty_names_by_id.get(int(self.id), "")
        candidate_names = {
            str(self.template_name or "").strip(),
            str(self.name or "").strip(),
        }
        candidate_names.discard("")
        return bool(candidate_names & {str(template.name or "").strip(), str(source_name or "").strip()})

    @property
    def localized_name(self) -> str:
        template = self._get_localized_template()
        return str(getattr(template, "name", "") or self.name or "")

    @property
    def localized_desc(self) -> str:
        template = self._get_localized_template()
        return str(getattr(template, "desc", "") or self.desc or "")

    @property
    def localized_effect_desc(self) -> str:
        template = self._get_localized_template()
        if template is not None and getattr(template, "effect_desc", ""):
            return str(template.effect_desc or "")
        if self.effect_desc:
            return str(self.effect_desc or "")
        if self.effects:
            return format_effects_to_text(self.effects)
        return ""

    @property
    def title(self) -> str:
        name = self.localized_name
        if not name:
            return ""
        translated = t("dynasty_title_format", name=name)
        return translated if translated != "dynasty_title_format" else f"{name}朝"

    @property
    def royal_house_name(self) -> str:
        if not self.royal_surname:
            return ""
        translated = t("dynasty_royal_house_format", surname=self.royal_surname)
        return translated if translated != "dynasty_royal_house_format" else f"{self.royal_surname}氏"

    def create_runtime(self, royal_surname: str) -> "Dynasty":
        source_name = source_dynasty_names_by_id.get(int(self.id), str(self.name or ""))
        return Dynasty(
            id=int(self.id),
            name=str(self.name),
            desc=str(self.desc),
            template_name=str(source_name or ""),
            royal_surname=str(royal_surname or ""),
            effect_desc=str(self.effect_desc or ""),
            effects=dict(self.effects or {}),
            style_tag=str(self.style_tag or ""),
            official_preference_type=str(self.official_preference_type or ""),
            official_preference_value=str(self.official_preference_value or ""),
            weight=float(self.weight),
            is_low_magic=bool(self.is_low_magic),
            current_emperor=None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": int(self.id),
            "name": str(self.name),
            "desc": str(self.desc),
            "template_name": str(self.template_name or ""),
            "royal_surname": str(self.royal_surname or ""),
            "effect_desc": str(self.effect_desc or ""),
            "effects": dict(self.effects or {}),
            "style_tag": str(self.style_tag or ""),
            "official_preference_type": str(self.official_preference_type or ""),
            "official_preference_value": str(self.official_preference_value or ""),
            "weight": float(self.weight),
            "is_low_magic": bool(self.is_low_magic),
            "current_emperor": self.current_emperor.to_dict() if self.current_emperor is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Dynasty":
        return cls(
            id=int(data["id"]),
            name=str(data.get("name", "") or ""),
            desc=str(data.get("desc", "") or ""),
            template_name=str(data.get("template_name", "") or ""),
            royal_surname=str(data.get("royal_surname", "") or ""),
            effect_desc=str(data.get("effect_desc", "") or ""),
            effects=dict(data.get("effects", {}) or {}),
            style_tag=str(data.get("style_tag", "") or ""),
            official_preference_type=str(data.get("official_preference_type", "") or ""),
            official_preference_value=str(data.get("official_preference_value", "") or ""),
            weight=float(data.get("weight", 1.0) or 1.0),
            is_low_magic=bool(data.get("is_low_magic", True)),
            current_emperor=Emperor.from_dict(data["current_emperor"]) if data.get("current_emperor") else None,
        )


def _load_dynasties_data() -> tuple[dict[int, Dynasty], dict[str, Dynasty]]:
    new_by_id: dict[int, Dynasty] = {}
    new_by_name: dict[str, Dynasty] = {}

    for row in game_configs.get("dynasty", []) or []:
        dynasty = Dynasty(
            id=get_int(row, "id"),
            name=get_str(row, "name"),
            desc=get_str(row, "desc"),
            effect_desc=get_str(row, "effect_desc"),
            effects=load_effect_from_str(get_str(row, "effects")),
            style_tag=get_str(row, "style_tag"),
            official_preference_type=get_str(row, "official_preference_type"),
            official_preference_value=get_str(row, "official_preference_value"),
            weight=get_float(row, "weight", 1.0),
        )
        if not dynasty.effect_desc and dynasty.effects:
            dynasty.effect_desc = format_effects_to_text(dynasty.effects)
        if dynasty.id <= 0 or not dynasty.name:
            continue
        new_by_id[dynasty.id] = dynasty
        new_by_name[dynasty.name] = dynasty

    return new_by_id, new_by_name


def _load_source_dynasty_names() -> dict[int, str]:
    source_names: dict[int, str] = {}
    csv_path = Path(CONFIG.paths.shared_game_configs) / "dynasty.csv"
    if not csv_path.exists():
        return source_names

    with csv_path.open("r", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))

    if len(rows) < 3:
        return source_names

    headers = [str(header or "").strip() for header in rows[0]]
    if headers and headers[0].startswith("\ufeff"):
        headers[0] = headers[0][1:]

    try:
        id_index = headers.index("id")
        name_index = headers.index("name")
    except ValueError:
        return source_names

    for row in rows[2:]:
        if not row or id_index >= len(row):
            continue
        raw_id = str(row[id_index] or "").strip()
        raw_name = str(row[name_index] or "").strip() if name_index < len(row) else ""
        if not raw_id or not raw_name:
            continue
        try:
            source_names[int(float(raw_id))] = raw_name
        except ValueError:
            continue

    return source_names


dynasties_by_id: dict[int, Dynasty] = {}
dynasties_by_name: dict[str, Dynasty] = {}
source_dynasty_names_by_id: dict[int, str] = _load_source_dynasty_names()


def reload() -> None:
    new_by_id, new_by_name = _load_dynasties_data()
    dynasties_by_id.clear()
    dynasties_by_id.update(new_by_id)
    dynasties_by_name.clear()
    dynasties_by_name.update(new_by_name)


reload()
