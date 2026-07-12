from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


def build_other_avatar_text(from_avatar: "Avatar", to_avatar: "Avatar") -> str:
    from src.classes.core.avatar.info_presenter import _get_race_info
    from src.classes.relation.relation import get_relation_label
    from src.i18n import t
    from src.systems.cultivation_display import build_avatar_cultivation_display

    nickname = to_avatar.nickname.value if to_avatar.nickname else t("None")
    sect = to_avatar.sect.name if to_avatar.sect else t("Rogue Cultivator")
    tech = to_avatar.technique.get_info() if to_avatar.technique else t("None")
    weapon = to_avatar.weapon.get_info() if to_avatar.weapon else t("None")
    aux = to_avatar.auxiliary.get_info() if to_avatar.auxiliary else t("None")
    goldfinger = to_avatar.goldfinger.get_info() if getattr(to_avatar, "goldfinger", None) else t("None")
    cultivation = build_avatar_cultivation_display(to_avatar)

    relation_state = from_avatar.get_relation_state(to_avatar)
    if relation_state is None:
        relation = t("None")
    else:
        labels = []
        if relation_state.blood_relation is not None:
            labels.append(get_relation_label(relation_state.blood_relation, from_avatar, to_avatar))
        labels.extend(
            get_relation_label(rel, from_avatar, to_avatar)
            for rel in sorted(relation_state.identity_relations, key=lambda item: item.value)
        )
        labels.append(str(from_avatar.get_numeric_relation(to_avatar)))
        relation = "/".join(labels)

    return t(
        "{name}, Nickname: {nickname}, Race: {race}, Realm: {realm}, Relation: {relation}, Sect: {sect}, Alignment: {alignment}, Appearance: {appearance}, Goldfinger: {goldfinger}, Technique: {technique}, Weapon: {weapon}, Auxiliary: {aux}, HP: {hp}",
        name=to_avatar.name,
        nickname=nickname,
        race=_get_race_info(to_avatar).get("name", ""),
        realm=cultivation["display_full_name"],
        relation=relation,
        sect=sect,
        alignment=to_avatar.alignment,
        appearance=to_avatar.appearance.get_info(),
        goldfinger=goldfinger,
        technique=tech,
        weapon=weapon,
        aux=aux,
        hp=to_avatar.hp,
    )


def build_avatar_description_text(avatar: "Avatar", detailed: bool = False) -> str:
    from src.classes.core.avatar.info_presenter import _get_race_behavior_desc, _get_race_info
    from src.i18n import t
    from src.systems.cultivation_display import build_avatar_cultivation_display

    born_region_name = t("Unknown")
    if avatar.born_region_id and avatar.born_region_id != -1:
        region = avatar.world.map.regions.get(avatar.born_region_id)
        if region:
            born_region_name = region.name

    lines = [t("【{name}】 {gender} {age} years old", name=avatar.name, gender=avatar.gender, age=avatar.age)]
    lines.append(t("Origin: {origin}", origin=born_region_name))
    lines.append(t("Race: {race}", race=_get_race_info(avatar).get("name", "")))
    race_behavior_desc = _get_race_behavior_desc(avatar)
    if detailed and race_behavior_desc:
        lines.append(t("Race Behavior Priority: {behavior}", behavior=race_behavior_desc))
    cultivation = build_avatar_cultivation_display(avatar)
    lines.append(t("Realm: {realm}", realm=cultivation["display_full_name"]))
    lines.append(t("Current Action: {action}", action=avatar.current_action_name))
    if avatar.sect:
        lines.append(t("Identity: {identity}", identity=avatar.get_sect_str()))

    if detailed:
        if avatar.backstory:
            lines.append(t("Backstory: {backstory}", backstory=avatar.backstory))
        lines.append(t("\n--- Current Effects Detail ---"))
        breakdown = avatar.get_effect_breakdown()
        from src.classes.effect import format_effects_to_text

        if not breakdown:
            lines.append(t("No additional effects"))
        else:
            for source_name, effects in breakdown:
                desc_str = format_effects_to_text(effects)
                if desc_str:
                    lines.append(f"[{source_name}]: {desc_str}")

    return "\n".join(lines)
