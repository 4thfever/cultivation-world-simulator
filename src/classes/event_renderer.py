from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.event import Event


def render_observed_event(event: "Event", observation_row) -> str:
    propagation_kind = str(observation_row["propagation_kind"] or "self_direct")
    if propagation_kind == "self_direct":
        return event.content

    params = event.render_params or {}
    subject_avatar_id = str(observation_row["subject_avatar_id"] or "")

    if subject_avatar_id and subject_avatar_id == str(params.get("avatar_a_id") or ""):
        subject_name = str(params.get("avatar_a_name") or "某人")
        other_name = str(params.get("avatar_b_name") or "某人")
    elif subject_avatar_id and subject_avatar_id == str(params.get("avatar_b_id") or ""):
        subject_name = str(params.get("avatar_b_name") or "某人")
        other_name = str(params.get("avatar_a_name") or "某人")
    else:
        subject_name = str(params.get("subject_name") or params.get("victim_name") or params.get("avatar_name") or "某人")
        other_name = str(params.get("other_name") or "某人")

    if propagation_kind == "close_relation_killed":
        killer_name = str(params.get("killer_name") or "某人")
        return f"你得知 {subject_name} 被 {killer_name} 杀害。"

    if propagation_kind == "close_relation_positive_bond":
        bond_label = str(params.get("bond_label") or "建立了重要关系")
        return f"你得知 {subject_name} 与 {other_name}{bond_label}。"

    if propagation_kind == "close_relation_major":
        if event.content:
            return f"你得知 {subject_name} 发生了一件大事：{event.content}"
        return f"你得知 {subject_name} 发生了一件大事。"

    return event.content
