import random
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING, Any

from src.utils.df import game_configs, get_str, get_list_str, get_int
from src.classes.effect import load_effect_from_str, format_effects_to_text
from src.classes.rarity import Rarity, get_rarity_from_str

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


@dataclass
class Goldfinger:
    """
    角色外挂。
    用于承载主角模板、超规格命数和额外叙事视角。
    """

    id: int
    key: str
    name: str
    desc: str
    exclusion_keys: List[str]
    rarity: Rarity
    condition: str
    effects: dict[str, object] | list[dict[str, object]]
    mechanism_type: str
    story_prompt: str
    mechanism_config: dict[str, Any] | list[dict[str, Any]]
    effect_desc: str = ""

    @property
    def weight(self) -> float:
        return self.rarity.weight

    def get_info(self) -> str:
        return self.name

    def get_detailed_info(self) -> str:
        from src.i18n import t

        desc_part = f" ({self.desc})" if self.desc else ""
        effect_part = t("\nEffect: {effect_desc}", effect_desc=self.effect_desc) if self.effect_desc else ""
        return f"{self.name}{desc_part}{effect_part}"

    def get_structured_info(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "desc": self.desc,
            "key": self.key,
            "rarity": self.rarity.level.value,
            "color": self.rarity.color_rgb,
            "effect_desc": self.effect_desc,
            "story_prompt": self.story_prompt,
            "mechanism_type": self.mechanism_type,
        }


def _load_goldfingers() -> tuple[dict[int, Goldfinger], dict[str, Goldfinger]]:
    goldfingers_by_id: dict[int, Goldfinger] = {}
    goldfingers_by_name: dict[str, Goldfinger] = {}

    goldfinger_df = game_configs.get("goldfinger", [])
    for row in goldfinger_df:
        exclusion_keys = get_list_str(row, "exclusion_keys")
        rarity = get_rarity_from_str(get_str(row, "rarity", "N").upper())
        effects = load_effect_from_str(get_str(row, "effects"))
        mechanism_config = load_effect_from_str(get_str(row, "mechanism_config"))
        effect_desc = format_effects_to_text(effects)

        goldfinger = Goldfinger(
            id=get_int(row, "id"),
            key=get_str(row, "key").upper(),
            name=get_str(row, "name"),
            desc=get_str(row, "desc"),
            exclusion_keys=exclusion_keys,
            rarity=rarity,
            condition=get_str(row, "condition"),
            effects=effects,
            mechanism_type=get_str(row, "mechanism_type", "effect_only"),
            story_prompt=get_str(row, "story_prompt"),
            mechanism_config=mechanism_config,
            effect_desc=effect_desc,
        )
        goldfingers_by_id[goldfinger.id] = goldfinger
        goldfingers_by_name[goldfinger.name] = goldfinger

    return goldfingers_by_id, goldfingers_by_name


goldfingers_by_id: dict[int, Goldfinger] = {}
goldfingers_by_name: dict[str, Goldfinger] = {}


def reload() -> None:
    new_id, new_name = _load_goldfingers()

    goldfingers_by_id.clear()
    goldfingers_by_id.update(new_id)

    goldfingers_by_name.clear()
    goldfingers_by_name.update(new_name)


reload()


def build_goldfinger_story_hint(*avatars: Optional["Avatar"]) -> str:
    lines: list[str] = []
    seen_avatar_ids: set[str] = set()

    for avatar in avatars:
        if avatar is None:
            continue
        avatar_id = str(getattr(avatar, "id", "") or "")
        if avatar_id and avatar_id in seen_avatar_ids:
            continue

        goldfinger = getattr(avatar, "goldfinger", None)
        story_prompt = str(getattr(goldfinger, "story_prompt", "") or "").strip()
        if not story_prompt:
            continue

        if avatar_id:
            seen_avatar_ids.add(avatar_id)
        lines.append(f"{avatar.name}拥有外挂「{goldfinger.name}」：{story_prompt}")

    return "\n".join(lines)


def merge_story_prompt_with_goldfinger(base_prompt: str, *avatars: Optional["Avatar"]) -> str:
    prompt_parts: list[str] = []
    normalized_base_prompt = str(base_prompt or "").strip()
    if normalized_base_prompt:
        prompt_parts.append(normalized_base_prompt)

    goldfinger_hint = build_goldfinger_story_hint(*avatars).strip()
    if goldfinger_hint:
        prompt_parts.append(f"外挂相关重点：\n{goldfinger_hint}")

    return "\n\n".join(prompt_parts)


def _is_goldfinger_allowed(
    goldfinger_id: int,
    already_selected_ids: set[int],
    avatar: Optional["Avatar"],
) -> bool:
    goldfinger = goldfingers_by_id[goldfinger_id]

    if avatar is not None and goldfinger.condition:
        allowed = bool(eval(goldfinger.condition, {"__builtins__": {}}, {"avatar": avatar}))
        if not allowed:
            return False

    for selected_id in already_selected_ids:
        other = goldfingers_by_id[selected_id]
        if (goldfinger.key in other.exclusion_keys) or (other.key in goldfinger.exclusion_keys):
            return False
    return True


def get_random_compatible_goldfinger(avatar: Optional["Avatar"] = None) -> Goldfinger | None:
    initial_ids = set(goldfingers_by_id.keys())
    if avatar is not None:
        initial_ids = {gid for gid in initial_ids if _is_goldfinger_allowed(gid, set(), avatar)}

    if not initial_ids:
        return None

    candidates = [goldfingers_by_id[gid] for gid in initial_ids]
    weights = [max(0.0, candidate.weight) for candidate in candidates]
    if not any(weight > 0 for weight in weights):
        return None

    return random.choices(candidates, weights=weights, k=1)[0]
