from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, List
from collections import defaultdict


class Relation(Enum):
    # —— 血缘（先天） ——
    PARENT = "parent"              # 父/母 -> 子（有向）
    CHILD = "child"                # 子 -> 父/母（有向）
    SIBLING = "sibling"            # 兄弟姐妹（对称）
    KIN = "kin"                    # 其他亲属（对称，泛化）

    # —— 后天（社会/情感） ——
    MASTER = "master"              # 师傅 -> 徒弟（有向）
    APPRENTICE = "apprentice"      # 徒弟 -> 师傅（有向）
    LOVERS = "lovers"              # 道侣（对称）
    FRIEND = "friend"              # 朋友（对称）
    ENEMY = "enemy"                # 仇人/敌人（对称）

    def __str__(self) -> str:
        return relation_display_names.get(self, self.value)

    @classmethod
    def from_chinese(cls, name_cn: str) -> "Relation|None":
        """
        依据中文显示名解析关系；无法解析返回 None。
        """
        if not name_cn:
            return None
        s = str(name_cn).strip()
        for rel, cn in relation_display_names.items():
            if s == cn:
                return rel
        return None


relation_display_names = {
    # 血缘（先天）
    Relation.PARENT: "父母",
    Relation.CHILD: "子女",
    Relation.SIBLING: "兄弟姐妹",
    Relation.KIN: "亲属",

    # 后天（社会/情感）
    Relation.MASTER: "师傅",
    Relation.APPRENTICE: "徒弟",
    Relation.LOVERS: "道侣",
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
    Relation.PARENT: Relation.CHILD,  # 父母 -> 子女
    Relation.CHILD: Relation.PARENT,  # 子女 -> 父母
    Relation.SIBLING: Relation.SIBLING,  # 兄弟姐妹 -> 兄弟姐妹
    Relation.KIN: Relation.KIN,  # 亲属 -> 亲属

    # 后天
    Relation.MASTER: Relation.APPRENTICE,  # 师傅 -> 徒弟
    Relation.APPRENTICE: Relation.MASTER,  # 徒弟 -> 师傅
    Relation.LOVERS: Relation.LOVERS,  # 道侣 -> 道侣
    Relation.FRIEND: Relation.FRIEND,  # 朋友 -> 朋友
    Relation.ENEMY: Relation.ENEMY,  # 仇人 -> 仇人
}


def get_reciprocal(relation: Relation) -> Relation:
    """
    给定 A->B 的关系，返回应当写入 B->A 的关系。
    对于对称关系（如 FRIEND/ENEMY/LOVERS/SIBLING/KIN），返回其本身。
    """
    return RECIPROCAL_RELATION.get(relation, relation)


# ——— 新增：评估两名角色可能新增的后天关系 ———
if TYPE_CHECKING:
    from src.classes.avatar import Avatar


def get_possible_post_relations(from_avatar: "Avatar", to_avatar: "Avatar") -> List[Relation]:
    """
    评估“to_avatar 相对于 from_avatar”可能新增的后天关系集合（方向性明确）。

    清晰规则：
    - LOVERS(道侣)：要求男女异性；若已存在 to->from 的相同关系则不重复
    - MASTER(师傅)：要求 to.level >= from.level + 20
    - APPRENTICE(徒弟)：要求 to.level <= from.level - 20
    - FRIEND(朋友)：始终可能(若未已存在)
    - ENEMY(仇人)：始终可能(若未已存在)

    说明：本函数只判断“是否可能”，不做概率与人格相关控制；概率留给上层逻辑。
    返回的是 Relation 列表，均为 to_avatar 相对于 from_avatar 的候选。
    """
    # 方向相关：检查 to->from 已有关系，避免重复推荐
    existing_to_from = to_avatar.get_relation(from_avatar)

    candidates: list[Relation] = []

    # 基础信息（Avatar 定义确保存在）
    level_from = from_avatar.cultivation_progress.level
    level_to = to_avatar.cultivation_progress.level

    # - FRIEND
    if existing_to_from != Relation.FRIEND:
        candidates.append(Relation.FRIEND)

    # - ENEMY
    if existing_to_from != Relation.ENEMY:
        candidates.append(Relation.ENEMY)

    # - LOVERS：异性（Avatar 定义确保性别存在）
    if from_avatar.gender != to_avatar.gender and existing_to_from != Relation.LOVERS:
        candidates.append(Relation.LOVERS)

    # - 师徒（方向性）：
    #   MASTER：to 是 from 的师傅 → to.level >= from.level + 20
    #   APPRENTICE：to 是 from 的徒弟 → to.level <= from.level - 20
    if level_to >= level_from + 20 and existing_to_from != Relation.MASTER:
        candidates.append(Relation.MASTER)
    if level_to <= level_from - 20 and existing_to_from != Relation.APPRENTICE:
        candidates.append(Relation.APPRENTICE)

    return candidates


# ——— 显示层：性别化称谓映射与标签工具 ———
# 基于对方性别的细化：
GENDERED_DISPLAY: dict[tuple[Relation, str], str] = {
    # 我 -> 对方：CHILD（我为子，对方为父/母） → 显示对方为 父亲/母亲
    (Relation.CHILD, "male"): "父亲",
    (Relation.CHILD, "female"): "母亲",
    # 我 -> 对方：PARENT（我为父/母，对方为子） → 显示对方为 儿子/女儿
    (Relation.PARENT, "male"): "儿子",
    (Relation.PARENT, "female"): "女儿",
}


def _label_from_self_perspective(relation: Relation, other_gender: object | None = None) -> str:
    # 优先使用性别化细化
    if other_gender is not None:
        gender_value = getattr(other_gender, "value", None) or str(other_gender)
        s = GENDERED_DISPLAY.get((relation, gender_value))
        if s:
            return s
    # 其余关系：以“我”为参照，取对偶再显示（MASTER -> 徒弟）
    counterpart = get_reciprocal(relation)
    return relation_display_names.get(counterpart, str(counterpart))


def get_relations_strs(avatar: "Avatar", max_lines: int = 6) -> list[str]:
    """
    以“我”的视角整理关系，输出若干行：
    - 我的师傅：A，B
    - 我的徒弟：C
    - 兄弟姐妹：D，E
    等。
    """
    relations = getattr(avatar, "relations", None)
    if not relations:
        return []

    grouped: dict[str, list[str]] = defaultdict(list)
    for other, rel in relations.items():
        grouped[_label_from_self_perspective(rel, getattr(other, "gender", None))].append(other.name)

    lines: list[str] = []
    for key in sorted(grouped.keys()):
        names = "，".join(grouped[key])
        lines.append(f"{key}为：{names}")
        if len(lines) >= max_lines:
            break
    return lines


def relations_to_str(avatar: "Avatar", sep: str = "；", max_lines: int = 6) -> str:
    lines = get_relations_strs(avatar, max_lines=max_lines)
    return sep.join(lines) if lines else "无"

