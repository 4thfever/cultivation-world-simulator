from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, List, Optional
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


# —— 规则定义 ——

ADD_RELATION_RULES: dict[Relation, str] = {
    Relation.LOVERS: "【道侣】需双方为异性。必须是双方非常相互认可且情投意合。",
    Relation.FRIEND: "【朋友】友善互动（交谈、切磋点到为止、治疗）。无实质利益冲突。",
    Relation.ENEMY: "【仇人】发生过实质性伤害（攻击致伤、偷窃、羞辱）。单次严重伤害或多次轻微摩擦。",
    Relation.MASTER: "【师傅】需境界显著高于徒弟（例如金丹vs练气）。",
    Relation.APPRENTICE: "【徒弟】相对于师傅的身份，通常由师傅关系自动确立。",
}

CANCEL_RELATION_RULES: dict[Relation, str] = {
    Relation.LOVERS: "【解除道侣】冲突、感情破裂、发生严重背叛。",
    Relation.FRIEND: "【绝交】发生利益冲突、背叛或长期无互动导致疏远。",
    Relation.ENEMY: "【化敌为友】一方主动示好并被接受，或共同经历生死患难，或仇恨被冲淡。",
    Relation.MASTER: "【逐出师门/叛出师门】徒弟大逆不道或师傅无力教导。",
    Relation.APPRENTICE: "【解除师徒】同上。",
}


def get_relation_rules_desc() -> str:
    """获取关系规则的描述文本，用于 Prompt"""
    lines = ["【建立关系规则】"]
    for rel, desc in ADD_RELATION_RULES.items():
        lines.append(f"- {desc}")
    lines.append("\n【取消关系规则】")
    for rel, desc in CANCEL_RELATION_RULES.items():
        lines.append(f"- {desc}")
    return "\n".join(lines)


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


if TYPE_CHECKING:
    from src.classes.avatar import Avatar


# ——— 显示层：性别化称谓映射与标签工具 ———

GENDERED_DISPLAY: dict[tuple[Relation, str], str] = {
    # 我 -> 对方：CHILD（我为子，对方为父/母） → 显示对方为 父亲/母亲
    (Relation.CHILD, "male"): "父亲",
    (Relation.CHILD, "female"): "母亲",
    # 我 -> 对方：PARENT（我为父/母，对方为子） → 显示对方为 儿子/女儿
    (Relation.PARENT, "male"): "儿子",
    (Relation.PARENT, "female"): "女儿",
}

# 显示顺序配置
DISPLAY_ORDER = [
    "师傅", "徒弟", "道侣",
    "父亲", "母亲",
    "儿子", "女儿",
    "哥哥", "弟弟", "姐姐", "妹妹",
    "兄弟", "姐妹", "兄弟姐妹", # 兜底
    "朋友", "仇人",
    "亲属"
]

def get_relation_label(relation: Relation, self_avatar: "Avatar", other_avatar: "Avatar") -> str:
    """
    获取 self_avatar 视角的 other_avatar 的称谓。
    例如：relation=CHILD (self是子), other是男 -> "父亲"
    relation=SIBLING, other比self大, other是女 -> "姐姐"
    """
    # 1. 处理兄弟姐妹 (涉及长幼比较)
    if relation == Relation.SIBLING:
        is_older = False
        # 比较出生时间 (MonthStamp 越小越早出生，年龄越大)
        if hasattr(other_avatar, "birth_month_stamp") and hasattr(self_avatar, "birth_month_stamp"):
            if other_avatar.birth_month_stamp < self_avatar.birth_month_stamp:
                is_older = True
            elif other_avatar.birth_month_stamp == self_avatar.birth_month_stamp:
                # 同月生，简单按 ID 排序保证一致性
                is_older = str(other_avatar.id) < str(self_avatar.id)
        
        gender_val = getattr(getattr(other_avatar, "gender", None), "value", "male")
        
        if gender_val == "male":
            return "哥哥" if is_older else "弟弟"
        else:
            return "姐姐" if is_older else "妹妹"

    # 2. 查表处理通用性别化称谓
    other_gender = getattr(other_avatar, "gender", None)
    gender_val = getattr(other_gender, "value", "male")
    
    label = GENDERED_DISPLAY.get((relation, gender_val))
    if label:
        return label

    # 3. 回退到默认显示名
    return relation_display_names.get(relation, relation.value)


def get_relations_strs(avatar: "Avatar", max_lines: int = 12) -> list[str]:
    """
    以“我”的视角整理关系，输出若干行。
    """
    relations = getattr(avatar, "relations", {}) or {}

    # 1. 收集并根据标签分组所有关系
    grouped: dict[str, list[str]] = defaultdict(list)
    for other, rel in relations.items():
        label = get_relation_label(rel, avatar, other)
        grouped[label].append(other.name)

    lines: list[str] = []
    processed_labels = set()

    # 2. 按照预定义顺序输出
    for label in DISPLAY_ORDER:
        if label in grouped:
            names = "，".join(grouped[label])
            lines.append(f"{label}：{names}")
            processed_labels.add(label)

    # 3. 处理未在配置中列出的其他关系（按字典序）
    for label in sorted(grouped.keys()):
        if label not in processed_labels:
            names = "，".join(grouped[label])
            lines.append(f"{label}：{names}")
            processed_labels.add(label)

    # 4. 若无任何关系
    if not lines:
        return ["无"]

    return lines[:max_lines]


def relations_to_str(avatar: "Avatar", sep: str = "；", max_lines: int = 6) -> str:
    lines = get_relations_strs(avatar, max_lines=max_lines)
    # 如果只有一行且是"无"，直接返回
    if len(lines) == 1 and lines[0] == "无":
        return "无"
    return sep.join(lines)
