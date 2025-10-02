from __future__ import annotations

from enum import Enum


class Relation(Enum):
    # —— 血缘（先天） ——
    PARENT = "parent"              # 父/母 -> 子（有向）
    CHILD = "child"                # 子 -> 父/母（有向）
    SIBLING = "sibling"            # 兄弟姐妹（对称）
    KIN = "kin"                    # 其他亲属（对称，泛化）

    # —— 后天（社会/情感） ——
    MASTER = "master"              # 师傅 -> 徒弟（有向）
    APPRENTICE = "apprentice"      # 徒弟 -> 师傅（有向）
    LOVERS = "lovers"              # 情侣/道侣（对称）
    FRIEND = "friend"              # 朋友（对称）
    ENEMY = "enemy"                # 仇人/敌人（对称）

    def __str__(self) -> str:
        return relation_display_names.get(self, self.value)


relation_display_names = {
    # 血缘（先天）
    Relation.PARENT: "父母",
    Relation.CHILD: "子女",
    Relation.SIBLING: "兄弟姐妹",
    Relation.KIN: "亲属",

    # 后天（社会/情感）
    Relation.MASTER: "师傅",
    Relation.APPRENTICE: "徒弟",
    Relation.LOVERS: "情侣",
    Relation.FRIEND: "朋友",
    Relation.ENEMY: "仇人",
}

# 关系是否属于“先天”（血缘），其余为“后天”
INNATE_RELATIONS: set[Relation] = {
    Relation.PARENT, Relation.CHILD, Relation.SIBLING, Relation.KIN,
}


def is_innate(relation: Relation) -> bool:
    return relation in INNATE_RELATIONS


# 有向关系的对偶映射；对称关系映射到自身
RECIPROCAL_RELATION: dict[Relation, Relation] = {
    # 血缘
    Relation.PARENT: Relation.CHILD,
    Relation.CHILD: Relation.PARENT,
    Relation.SIBLING: Relation.SIBLING,
    Relation.KIN: Relation.KIN,

    # 后天
    Relation.MASTER: Relation.APPRENTICE,
    Relation.APPRENTICE: Relation.MASTER,
    Relation.LOVERS: Relation.LOVERS,
    Relation.FRIEND: Relation.FRIEND,
    Relation.ENEMY: Relation.ENEMY,
}


def get_reciprocal(relation: Relation) -> Relation:
    """
    给定 A->B 的关系，返回应当写入 B->A 的关系。
    对于对称关系（如 FRIEND/ENEMY/LOVERS/SIBLING/KIN），返回其本身。
    """
    return RECIPROCAL_RELATION.get(relation, relation)

