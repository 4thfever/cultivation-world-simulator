from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.classes.effect import load_effect_from_str
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
    royal_surname: str = ""
    effect_desc: str = ""
    effects: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    is_low_magic: bool = True
    current_emperor: Emperor | None = None

    @property
    def title(self) -> str:
        return f"{self.name}朝"

    @property
    def royal_house_name(self) -> str:
        if not self.royal_surname:
            return ""
        return f"{self.royal_surname}氏"

    def create_runtime(self, royal_surname: str) -> "Dynasty":
        return Dynasty(
            id=int(self.id),
            name=str(self.name),
            desc=str(self.desc),
            royal_surname=str(royal_surname or ""),
            effect_desc=str(self.effect_desc or ""),
            effects=dict(self.effects or {}),
            weight=float(self.weight),
            is_low_magic=bool(self.is_low_magic),
            current_emperor=None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": int(self.id),
            "name": str(self.name),
            "desc": str(self.desc),
            "royal_surname": str(self.royal_surname or ""),
            "effect_desc": str(self.effect_desc or ""),
            "effects": dict(self.effects or {}),
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
            royal_surname=str(data.get("royal_surname", "") or ""),
            effect_desc=str(data.get("effect_desc", "") or ""),
            effects=dict(data.get("effects", {}) or {}),
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
            weight=get_float(row, "weight", 1.0),
        )
        if dynasty.id <= 0 or not dynasty.name:
            continue
        new_by_id[dynasty.id] = dynasty
        new_by_name[dynasty.name] = dynasty

    return new_by_id, new_by_name


dynasties_by_id: dict[int, Dynasty] = {}
dynasties_by_name: dict[str, Dynasty] = {}


def reload() -> None:
    new_by_id, new_by_name = _load_dynasties_data()
    dynasties_by_id.clear()
    dynasties_by_id.update(new_by_id)
    dynasties_by_name.clear()
    dynasties_by_name.update(new_by_name)


reload()
