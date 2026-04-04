from __future__ import annotations

from typing import TYPE_CHECKING

from src.i18n import t

if TYPE_CHECKING:
    from src.classes.event import Event


def render_observed_event(event: "Event", observation_row) -> str:
    propagation_kind = str(observation_row["propagation_kind"] or "self_direct")
    if propagation_kind == "self_direct":
        return event.content

    params = event.render_params or {}
    subject_avatar_id = str(observation_row["subject_avatar_id"] or "")

    if subject_avatar_id and subject_avatar_id == str(params.get("avatar_a_id") or ""):
        subject_name = str(params.get("avatar_a_name") or t("Someone"))
        other_name = str(params.get("avatar_b_name") or t("Someone"))
    elif subject_avatar_id and subject_avatar_id == str(params.get("avatar_b_id") or ""):
        subject_name = str(params.get("avatar_b_name") or t("Someone"))
        other_name = str(params.get("avatar_a_name") or t("Someone"))
    else:
        subject_name = str(params.get("subject_name") or params.get("victim_name") or params.get("avatar_name") or t("Someone"))
        other_name = str(params.get("other_name") or t("Someone"))

    if propagation_kind == "close_relation_killed":
        killer_name = str(params.get("killer_name") or t("Someone"))
        return t("You learned that {subject_name} was killed by {killer_name}.", subject_name=subject_name, killer_name=killer_name)

    if propagation_kind == "close_relation_positive_bond":
        bond_label = t(str(params.get("bond_label_id") or "bond_label_major_relationship"))
        return t("You learned that {subject_name} and {other_name} {bond_label}.", subject_name=subject_name, other_name=other_name, bond_label=bond_label)

    if propagation_kind == "close_relation_major":
        if event.content:
            return t("You learned that {subject_name} experienced a major event: {content}", subject_name=subject_name, content=event.content)
        return t("You learned that {subject_name} experienced a major event.", subject_name=subject_name)

    return event.content
