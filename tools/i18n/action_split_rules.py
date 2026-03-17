"""Shared action module split rules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SplitRule:
    target_file: str
    prefixes: tuple[str, ...] = ()
    exact_msgids: frozenset[str] = frozenset()
    contains: tuple[str, ...] = ()

    def matches(self, msgid: str) -> bool:
        return (
            msgid in self.exact_msgids
            or any(msgid.startswith(prefix) for prefix in self.prefixes)
            or any(token in msgid for token in self.contains)
        )


ACTION_SPLIT_RULES: tuple[SplitRule, ...] = (
    SplitRule(
        target_file="action_combat.po",
        prefixes=(
            "assassinate_",
            "attack_",
            "catch_",
            "escape_",
            "hunt_",
            "devour_people_",
            "plunder_people_",
        ),
        exact_msgids=frozenset(
            {
                "{avatar} assassinated successfully! {target} fell without any defense.",
                "{avatar} lurks in the shadows, attempting to assassinate {target}...",
                "{avatar} begins devouring people in town",
                "{avatar} begins plundering people in town",
                "{avatar} failed to tame spirit beast",
            }
        ),
    ),
    SplitRule(
        target_file="action_progression.po",
        prefixes=(
            "breakthrough_",
            "cast_",
            "dual_cultivation_",
            "educate_",
            "harvest_",
            "meditate_",
            "nurture_weapon_",
            "refine_",
            "respire_",
            "self_heal_",
            "temper_",
        ),
        exact_msgids=frozenset(
            {
                "breakthrough probability increased by {val:.1%}",
                "gained {val} cultivation",
                "excellent progress",
                "slow progress (essence mismatch)",
                "slow progress (sparse essence)",
                "{avatar} begins Zen Meditation.",
                "{avatar} begins attempting breakthrough",
                "{avatar} begins attempting to cast {realm}-tier treasure",
                "{avatar} begins attempting to refine {realm}-tier elixir",
                "{avatar} begins educating people in {city}.",
                "{avatar} begins tempering body strength",
                "{avatar} completed meditation with a peaceful mind.",
                "{avatar} finished educating people. Merit accumulated (+{exp}).",
                "{avatar} healing completed (recovered {amount} HP, current HP {hp})",
                "{avatar} successfully cast {realm}-tier {label} '{item}'",
                "{avatar} successfully refined {realm}-tier elixir '{item}'",
                "{initiator} invites {target} for dual cultivation",
            }
        ),
    ),
    SplitRule(
        target_file="action_world.po",
        prefixes=(
            "buy_",
            "help_people_",
            "mine_",
            "move_",
            "sell_",
            "plant_",
        ),
        exact_msgids=frozenset(
            {
                "bought",
                "bought and consumed",
                "bought and equipped",
                "{avatar} attempted to move but target is invalid",
                "{avatar} begins helping people in town",
                "{avatar} sold {item} in town",
                "{avatar} begins planting at {location}",
                "{avatar} finished planting, earned {stones} Spirit Stones",
                "wilderness",
            }
        ),
    ),
)


def get_action_target_file(msgid: str) -> str:
    for rule in ACTION_SPLIT_RULES:
        if rule.matches(msgid):
            return rule.target_file
    return "action.po"
