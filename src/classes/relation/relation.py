from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING


class Relation(Enum):
    # Blood relations
    IS_PARENT_OF = "parent"
    IS_CHILD_OF = "child"
    IS_SIBLING_OF = "sibling"
    IS_KIN_OF = "kin"
    IS_GRAND_PARENT_OF = "grand_parent"
    IS_GRAND_CHILD_OF = "grand_child"

    # Identity relations
    IS_SWORN_SIBLING_OF = "sworn_sibling"
    IS_MASTER_OF = "master"
    IS_DISCIPLE_OF = "apprentice"
    IS_LOVER_OF = "lovers"
    # Deprecated compatibility aliases. New code should use friendliness-derived NumericRelation.
    IS_FRIEND_OF = "friend"
    IS_ENEMY_OF = "enemy"

    # Calculated relations
    IS_MARTIAL_GRANDMASTER_OF = "martial_grandmaster"
    IS_MARTIAL_GRANDCHILD_OF = "martial_grandchild"
    IS_MARTIAL_SIBLING_OF = "martial_sibling"

    def __str__(self) -> str:
        from src.i18n import t

        return t(relation_msg_ids.get(self, self.value))


class NumericRelation(Enum):
    ARCHENEMY = "archenemy"
    DISLIKED = "disliked"
    STRANGER = "stranger"
    FRIEND = "friend"
    BEST_FRIEND = "best_friend"

    def __str__(self) -> str:
        from src.i18n import t

        return t(numeric_relation_msg_ids[self])


relation_msg_ids = {
    Relation.IS_PARENT_OF: "parent",
    Relation.IS_CHILD_OF: "child",
    Relation.IS_SIBLING_OF: "sibling",
    Relation.IS_KIN_OF: "kin",
    Relation.IS_MASTER_OF: "master",
    Relation.IS_DISCIPLE_OF: "apprentice",
    Relation.IS_LOVER_OF: "lovers",
    Relation.IS_FRIEND_OF: "numeric_relation_friend",
    Relation.IS_ENEMY_OF: "numeric_relation_archenemy",
    Relation.IS_SWORN_SIBLING_OF: "sworn_sibling",
    Relation.IS_GRAND_PARENT_OF: "grand_parent",
    Relation.IS_GRAND_CHILD_OF: "grand_child",
    Relation.IS_MARTIAL_GRANDMASTER_OF: "martial_grandmaster",
    Relation.IS_MARTIAL_GRANDCHILD_OF: "martial_grandchild",
    Relation.IS_MARTIAL_SIBLING_OF: "martial_sibling",
}

numeric_relation_msg_ids = {
    NumericRelation.ARCHENEMY: "numeric_relation_archenemy",
    NumericRelation.DISLIKED: "numeric_relation_disliked",
    NumericRelation.STRANGER: "numeric_relation_stranger",
    NumericRelation.FRIEND: "numeric_relation_friend",
    NumericRelation.BEST_FRIEND: "numeric_relation_best_friend",
}

ADD_RELATION_RULES: dict[Relation, str] = {}
CANCEL_RELATION_RULES: dict[Relation, str] = {}

BLOOD_RELATIONS: set[Relation] = {
    Relation.IS_PARENT_OF,
    Relation.IS_CHILD_OF,
    Relation.IS_SIBLING_OF,
    Relation.IS_KIN_OF,
    Relation.IS_GRAND_PARENT_OF,
    Relation.IS_GRAND_CHILD_OF,
}

IDENTITY_RELATIONS: set[Relation] = {
    Relation.IS_SWORN_SIBLING_OF,
    Relation.IS_MASTER_OF,
    Relation.IS_DISCIPLE_OF,
    Relation.IS_LOVER_OF,
}

CALCULATED_RELATIONS: set[Relation] = {
    Relation.IS_GRAND_PARENT_OF,
    Relation.IS_GRAND_CHILD_OF,
    Relation.IS_MARTIAL_GRANDMASTER_OF,
    Relation.IS_MARTIAL_GRANDCHILD_OF,
    Relation.IS_MARTIAL_SIBLING_OF,
    Relation.IS_SIBLING_OF,
}

INNATE_RELATIONS: set[Relation] = {
    Relation.IS_PARENT_OF,
    Relation.IS_CHILD_OF,
    Relation.IS_SIBLING_OF,
    Relation.IS_KIN_OF,
    Relation.IS_GRAND_PARENT_OF,
    Relation.IS_GRAND_CHILD_OF,
}


@dataclass
class RelationState:
    blood_relation: Relation | None = None
    identity_relations: set[Relation] = field(default_factory=set)
    friendliness: int = 0
    last_numeric_relation: NumericRelation = NumericRelation.STRANGER
    last_numeric_relation_change_month: int | None = None

    def copy(self) -> "RelationState":
        return RelationState(
            blood_relation=self.blood_relation,
            identity_relations=set(self.identity_relations),
            friendliness=self.friendliness,
            last_numeric_relation=self.last_numeric_relation,
            last_numeric_relation_change_month=self.last_numeric_relation_change_month,
        )

    def has_identity(self, relation: Relation) -> bool:
        return relation in self.identity_relations

    def set_identity(self, relation: Relation) -> None:
        if relation in IDENTITY_RELATIONS:
            self.identity_relations.add(relation)

    def remove_identity(self, relation: Relation) -> None:
        self.identity_relations.discard(relation)

    def is_empty(self) -> bool:
        return (
            self.blood_relation is None
            and not self.identity_relations
            and self.friendliness == 0
            and self.last_numeric_relation == NumericRelation.STRANGER
            and self.last_numeric_relation_change_month is None
        )

    def to_save_dict(self) -> dict:
        return {
            "blood_relation": self.blood_relation.value if self.blood_relation else None,
            "identity_relations": [rel.value for rel in sorted(self.identity_relations, key=lambda item: item.value)],
            "friendliness": int(self.friendliness),
            "last_numeric_relation": self.last_numeric_relation.value,
            "last_numeric_relation_change_month": self.last_numeric_relation_change_month,
        }

    @classmethod
    def from_save_dict(cls, data: dict) -> "RelationState":
        blood_relation = None
        if data.get("blood_relation"):
            blood_relation = Relation(data["blood_relation"])

        identity_relations = {
            Relation(value)
            for value in data.get("identity_relations", [])
            if value in {item.value for item in IDENTITY_RELATIONS}
        }

        last_numeric_value = data.get("last_numeric_relation", NumericRelation.STRANGER.value)
        try:
            last_numeric_relation = NumericRelation(last_numeric_value)
        except ValueError:
            last_numeric_relation = NumericRelation.STRANGER

        return cls(
            blood_relation=blood_relation,
            identity_relations=identity_relations,
            friendliness=int(data.get("friendliness", 0) or 0),
            last_numeric_relation=last_numeric_relation,
            last_numeric_relation_change_month=data.get("last_numeric_relation_change_month"),
        )


def is_innate(relation: Relation) -> bool:
    return relation in INNATE_RELATIONS


def get_relation_rules_desc() -> str:
    return ""


RECIPROCAL_RELATION: dict[Relation, Relation] = {
    Relation.IS_PARENT_OF: Relation.IS_CHILD_OF,
    Relation.IS_CHILD_OF: Relation.IS_PARENT_OF,
    Relation.IS_SIBLING_OF: Relation.IS_SIBLING_OF,
    Relation.IS_KIN_OF: Relation.IS_KIN_OF,
    Relation.IS_GRAND_PARENT_OF: Relation.IS_GRAND_CHILD_OF,
    Relation.IS_GRAND_CHILD_OF: Relation.IS_GRAND_PARENT_OF,
    Relation.IS_MASTER_OF: Relation.IS_DISCIPLE_OF,
    Relation.IS_DISCIPLE_OF: Relation.IS_MASTER_OF,
    Relation.IS_LOVER_OF: Relation.IS_LOVER_OF,
    Relation.IS_SWORN_SIBLING_OF: Relation.IS_SWORN_SIBLING_OF,
    Relation.IS_MARTIAL_GRANDMASTER_OF: Relation.IS_MARTIAL_GRANDCHILD_OF,
    Relation.IS_MARTIAL_GRANDCHILD_OF: Relation.IS_MARTIAL_GRANDMASTER_OF,
    Relation.IS_MARTIAL_SIBLING_OF: Relation.IS_MARTIAL_SIBLING_OF,
}


def get_reciprocal(relation: Relation) -> Relation:
    return RECIPROCAL_RELATION.get(relation, relation)


if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


GENDERED_DISPLAY: dict[tuple[Relation, str], str] = {
    (Relation.IS_PARENT_OF, "male"): "relation_father",
    (Relation.IS_PARENT_OF, "female"): "relation_mother",
    (Relation.IS_CHILD_OF, "male"): "relation_son",
    (Relation.IS_CHILD_OF, "female"): "relation_daughter",
    (Relation.IS_GRAND_PARENT_OF, "male"): "relation_grandfather",
    (Relation.IS_GRAND_PARENT_OF, "female"): "relation_grandmother",
    (Relation.IS_GRAND_CHILD_OF, "male"): "relation_grandson",
    (Relation.IS_GRAND_CHILD_OF, "female"): "relation_granddaughter",
}

DISPLAY_ORDER = [
    "martial_grandmaster",
    "master",
    "martial_sibling",
    "apprentice",
    "martial_grandchild",
    "lovers",
    "relation_sworn_older_brother",
    "relation_sworn_younger_brother",
    "relation_sworn_older_sister",
    "relation_sworn_younger_sister",
    "sworn_sibling",
    "relation_grandfather",
    "relation_grandmother",
    "grand_parent",
    "relation_father",
    "relation_mother",
    "relation_older_brother",
    "relation_younger_brother",
    "relation_older_sister",
    "relation_younger_sister",
    "sibling",
    "relation_son",
    "relation_daughter",
    "relation_grandson",
    "relation_granddaughter",
    "grand_child",
    "numeric_relation_best_friend",
    "numeric_relation_friend",
    "numeric_relation_stranger",
    "numeric_relation_disliked",
    "numeric_relation_archenemy",
    "kin",
]


def get_relation_label(relation: Relation, self_avatar: "Avatar", other_avatar: "Avatar") -> str:
    from src.i18n import t

    if relation in {
        Relation.IS_SIBLING_OF,
        Relation.IS_MARTIAL_SIBLING_OF,
        Relation.IS_SWORN_SIBLING_OF,
    }:
        is_older = False
        if hasattr(other_avatar, "birth_month_stamp") and hasattr(self_avatar, "birth_month_stamp"):
            if other_avatar.birth_month_stamp < self_avatar.birth_month_stamp:
                is_older = True
            elif other_avatar.birth_month_stamp == self_avatar.birth_month_stamp:
                is_older = str(other_avatar.id) < str(self_avatar.id)

        gender_val = getattr(getattr(other_avatar, "gender", None), "value", "male")
        if relation == Relation.IS_SIBLING_OF:
            if gender_val == "male":
                return t("relation_older_brother") if is_older else t("relation_younger_brother")
            return t("relation_older_sister") if is_older else t("relation_younger_sister")
        if relation == Relation.IS_SWORN_SIBLING_OF:
            if gender_val == "male":
                return t("relation_sworn_older_brother") if is_older else t("relation_sworn_younger_brother")
            return t("relation_sworn_older_sister") if is_older else t("relation_sworn_younger_sister")
        if gender_val == "male":
            return t("relation_martial_older_brother") if is_older else t("relation_martial_younger_brother")
        return t("relation_martial_older_sister") if is_older else t("relation_martial_younger_sister")

    other_gender = getattr(other_avatar, "gender", None)
    gender_val = getattr(other_gender, "value", "male")
    label_key = GENDERED_DISPLAY.get((relation, gender_val))
    if label_key:
        return t(label_key)

    key = relation_msg_ids.get(relation, relation.value)
    return t(key)


def get_numeric_relation_label(relation: NumericRelation) -> str:
    from src.i18n import t

    msgid = numeric_relation_msg_ids[relation]
    return t(msgid)


def get_relation_state_labels(
    avatar: "Avatar",
    other_avatar: "Avatar",
    state: RelationState,
    computed_relation: Relation | None = None,
) -> list[str]:
    labels: list[str] = []

    if state.blood_relation is not None:
        labels.append(get_relation_label(state.blood_relation, avatar, other_avatar))

    ordered_identity_relations = sorted(state.identity_relations, key=lambda item: item.value)
    for relation in ordered_identity_relations:
        labels.append(get_relation_label(relation, avatar, other_avatar))

    if computed_relation is not None and state.blood_relation is None and computed_relation not in state.identity_relations:
        labels.append(get_relation_label(computed_relation, avatar, other_avatar))

    labels.append(get_numeric_relation_label(state.last_numeric_relation))
    return labels


def get_relations_strs(avatar: "Avatar", max_lines: int = 12) -> list[str]:
    from src.i18n import t
    from src.classes.relation.relations import iter_display_relation_items

    grouped: dict[str, list[str]] = defaultdict(list)
    relation_states = dict(iter_display_relation_items(avatar))
    computed_relations = getattr(avatar, "computed_relations", {}) or {}

    all_targets = set(relation_states.keys()) | set(computed_relations.keys())
    for other in all_targets:
        state = relation_states.get(other, RelationState())
        computed_relation = computed_relations.get(other)
        labels = get_relation_state_labels(avatar, other, state, computed_relation)

        display_name = other.name
        if getattr(other, "is_dead", False):
            d_info = getattr(other, "death_info", None)
            reason = d_info["reason"] if d_info and "reason" in d_info else t("Unknown reason")
            display_name = t("{name} (Deceased: {reason})", name=other.name, reason=reason)

        for label in labels:
            grouped[label].append(display_name)

    lines: list[str] = []
    processed_labels = set()
    for msgid in DISPLAY_ORDER:
        label = t(msgid)
        if label in grouped:
            names = t("comma_separator").join(grouped[label])
            lines.append(t("{label}: {names}", label=label, names=names))
            processed_labels.add(label)

    for label in sorted(grouped.keys()):
        if label in processed_labels:
            continue
        names = t("comma_separator").join(grouped[label])
        lines.append(t("{label}: {names}", label=label, names=names))

    if not lines:
        return [t("None")]
    return lines[:max_lines]


def relations_to_str(avatar: "Avatar", sep: str = None, max_lines: int = 6) -> str:
    from src.i18n import t

    if sep is None:
        sep = t("semicolon_separator")
    lines = get_relations_strs(avatar, max_lines=max_lines)
    if len(lines) == 1 and lines[0] == t("None"):
        return t("None")
    return sep.join(lines)
