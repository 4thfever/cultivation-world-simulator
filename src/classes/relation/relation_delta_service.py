from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.i18n import t
from src.classes.relation.relation import NumericRelation, Relation
from src.classes.relation.relations import add_friendliness
from src.utils.config import CONFIG
from src.utils.llm import call_llm_with_task_name

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


@dataclass(frozen=True)
class RelationDelta:
    from_avatar: "Avatar"
    to_avatar: "Avatar"
    delta: int
    reason: str


class RelationDeltaService:
    TEMPLATE_PATH = CONFIG.paths.templates / "relation_delta.txt"

    @staticmethod
    def get_action_mode(action_key: str) -> str:
        action_modes = getattr(CONFIG.social.relation, "action_modes", None)
        return str(getattr(action_modes, action_key, "fixed") or "fixed").lower()

    @staticmethod
    def get_llm_delta_bounds() -> tuple[int, int]:
        llm_delta = getattr(CONFIG.social.relation, "llm_delta", None)
        min_delta = int(getattr(llm_delta, "min", -6))
        max_delta = int(getattr(llm_delta, "max", 6))
        return min_delta, max_delta

    @staticmethod
    def get_fixed_delta(action_key: str, outcome_key: str) -> tuple[int, int]:
        fixed_deltas = getattr(CONFIG.social.relation, "fixed_deltas", None)
        action_config = getattr(fixed_deltas, action_key, None)
        outcome_config = getattr(action_config, outcome_key, None)
        if outcome_config is None:
            return 0, 0
        return int(getattr(outcome_config, "a_to_b", 0)), int(getattr(outcome_config, "b_to_a", 0))

    @classmethod
    async def resolve_event_text_delta(
        cls,
        *,
        action_key: str,
        avatar_a: "Avatar",
        avatar_b: "Avatar",
        event_text: str,
    ) -> tuple[int, int]:
        mode = cls.get_action_mode(action_key)
        if mode != "llm":
            return 0, 0

        min_delta, max_delta = cls.get_llm_delta_bounds()
        infos = {
            "avatar_a_name": avatar_a.name,
            "avatar_b_name": avatar_b.name,
            "avatar_a_personas": "、".join(p.get_info() for p in avatar_a.personas[:3]) if avatar_a.personas else t("None"),
            "avatar_b_personas": "、".join(p.get_info() for p in avatar_b.personas[:3]) if avatar_b.personas else t("None"),
            "avatar_a_to_b_numeric_relation": str(avatar_a.get_numeric_relation(avatar_b)),
            "avatar_b_to_a_numeric_relation": str(avatar_b.get_numeric_relation(avatar_a)),
            "avatar_a_to_b_friendliness": avatar_a.get_friendliness(avatar_b),
            "avatar_b_to_a_friendliness": avatar_b.get_friendliness(avatar_a),
            "identity_relations": "、".join(
                sorted(rel.value for rel in (avatar_a.get_relation_state(avatar_b).identity_relations if avatar_a.get_relation_state(avatar_b) else set()))
            ) or t("None"),
            "event_text": event_text,
            "min_delta": min_delta,
            "max_delta": max_delta,
        }
        result = await call_llm_with_task_name("relation_delta", cls.TEMPLATE_PATH, infos)
        a_to_b = int(result.get("delta_a_to_b", 0) or 0)
        b_to_a = int(result.get("delta_b_to_a", 0) or 0)
        return max(min_delta, min(max_delta, a_to_b)), max(min_delta, min(max_delta, b_to_a))

    @staticmethod
    def apply_bidirectional_delta(
        avatar_a: "Avatar",
        avatar_b: "Avatar",
        a_to_b: int,
        b_to_a: int,
    ) -> None:
        current_month = int(avatar_a.world.month_stamp)
        add_friendliness(avatar_a, avatar_b, a_to_b, current_month=current_month)
        add_friendliness(avatar_b, avatar_a, b_to_a, current_month=current_month)

    @staticmethod
    def set_hostility(avatar_a: "Avatar", avatar_b: "Avatar") -> None:
        current_month = int(avatar_a.world.month_stamp)
        add_friendliness(avatar_a, avatar_b, -1000, current_month=current_month)
        add_friendliness(avatar_b, avatar_a, -1000, current_month=current_month)

    @staticmethod
    def get_numeric_relation_rank(relation: NumericRelation) -> int:
        ranks = {
            NumericRelation.ARCHENEMY: 0,
            NumericRelation.DISLIKED: 1,
            NumericRelation.STRANGER: 2,
            NumericRelation.FRIEND: 3,
            NumericRelation.BEST_FRIEND: 4,
        }
        if not isinstance(relation, NumericRelation):
            relation = NumericRelation.STRANGER
        return ranks[relation]

    @staticmethod
    def is_friend_or_better(avatar_a: "Avatar", avatar_b: "Avatar") -> bool:
        return RelationDeltaService.get_numeric_relation_rank(avatar_a.get_numeric_relation(avatar_b)) >= RelationDeltaService.get_numeric_relation_rank(NumericRelation.FRIEND)

    @staticmethod
    def has_identity(avatar_a: "Avatar", avatar_b: "Avatar", relation: Relation) -> bool:
        return avatar_a.has_identity_relation(avatar_b, relation)
