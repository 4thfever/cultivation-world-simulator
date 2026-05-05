from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.classes.effect import format_effects_to_text, load_effect_from_str
from src.i18n import t
from src.utils.config import CONFIG
from src.utils.df import game_configs, get_float, get_str


HUMAN_RACE_ID = "human"


@dataclass(frozen=True)
class Race:
    id: str
    name: str
    desc: str
    effects: Dict[str, Any]
    effect_desc: str = ""
    weight: float = 0.0

    @property
    def is_yao(self) -> bool:
        return self.id != HUMAN_RACE_ID

    def get_info(self, detailed: bool = False) -> dict[str, Any]:
        info: dict[str, Any] = {
            "id": self.id,
            "name": t(self.name),
            "type_name": t("Race"),
        }
        if detailed:
            info["desc"] = t(self.desc)
            info["effect_desc"] = self.effect_desc
        return info

    def __str__(self) -> str:
        return t(self.name)


def _load_race_data() -> Dict[str, Race]:
    data: Dict[str, Race] = {}
    for row in game_configs.get("race", []) or []:
        race_id = get_str(row, "id")
        if not race_id or race_id == "id":
            continue
        effects = load_effect_from_str(get_str(row, "effects"))
        if not isinstance(effects, dict):
            effects = {}
        data[race_id] = Race(
            id=race_id,
            name=get_str(row, "name_id") or get_str(row, "name") or race_id,
            desc=get_str(row, "desc_id") or get_str(row, "desc"),
            effects=effects,
            effect_desc=format_effects_to_text(effects),
            weight=max(0.0, get_float(row, "weight", 0.0)),
        )
    if HUMAN_RACE_ID not in data:
        data[HUMAN_RACE_ID] = Race(
            id=HUMAN_RACE_ID,
            name="RACE_HUMAN_NAME",
            desc="RACE_HUMAN_DESC",
            effects={},
            weight=0.0,
        )
    return data


races_by_id: Dict[str, Race] = {}


def reload() -> None:
    new_data = _load_race_data()
    races_by_id.clear()
    races_by_id.update(new_data)


reload()


def get_race(race_id: str | None) -> Race:
    return races_by_id.get(str(race_id or HUMAN_RACE_ID), races_by_id[HUMAN_RACE_ID])


def is_yao_race(race: Race | str | None) -> bool:
    if isinstance(race, Race):
        return race.is_yao
    return get_race(str(race or HUMAN_RACE_ID)).is_yao


def get_avatar_race(avatar: object | None) -> Race:
    if avatar is None:
        return get_race(HUMAN_RACE_ID)
    return get_race(getattr(getattr(avatar, "race", None), "id", getattr(avatar, "race", HUMAN_RACE_ID)))


def is_yao_avatar(avatar: object | None) -> bool:
    return get_avatar_race(avatar).is_yao


def get_race_surname(race: Race | str | None) -> str:
    race_obj = race if isinstance(race, Race) else get_race(str(race or HUMAN_RACE_ID))
    mapping = {
        "fox": "狐",
        "wolf": "狼",
        "bird": "鸟",
        "snake": "蛇",
        "turtle": "龟",
    }
    return mapping.get(race_obj.id, "")


def is_cross_race(avatar_a: object | None, avatar_b: object | None) -> bool:
    return get_avatar_race(avatar_a).id != get_avatar_race(avatar_b).id


def roll_avatar_race(probability: Optional[float] = None) -> Race:
    if probability is None:
        avatar_config = getattr(CONFIG, "avatar", None)
        probability = float(getattr(avatar_config, "yao_race_probability", 0.1) or 0.0)
    probability = max(0.0, min(1.0, float(probability)))
    if random.random() >= probability:
        return get_race(HUMAN_RACE_ID)

    candidates = [race for race in races_by_id.values() if race.is_yao and race.weight > 0]
    if not candidates:
        return get_race(HUMAN_RACE_ID)
    weights = [race.weight for race in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]
