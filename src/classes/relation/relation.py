from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from collections import defaultdict


class Relation(Enum):
    # —— 血缘（先天） ——
    IS_PARENT_OF = "parent"              # 对方是我的父/母（有向）
    IS_CHILD_OF = "child"                # 对方是我的子/女（有向）
    IS_SIBLING_OF = "sibling"            # 对方是我的兄弟姐妹（对称）
    IS_KIN_OF = "kin"                    # 对方是我的其他亲属（对称，泛化）

    # —— 后天（社会/情感） ——
    IS_SWORN_SIBLING_OF = "sworn_sibling"  # 对方是我的义兄弟/义姐妹（对称）
    IS_MASTER_OF = "master"              # 对方是我的师傅（有向）
    IS_DISCIPLE_OF = "apprentice"        # 对方是我的徒弟（有向）
    IS_LOVER_OF = "lovers"               # 对方是我的道侣（对称）
    IS_FRIEND_OF = "friend"              # 对方是我的朋友（对称）
    IS_ENEMY_OF = "enemy"                # 对方是我的仇人/敌人（对称）
    
    # —— 二阶衍生关系 (Calculated) ——
    IS_GRAND_PARENT_OF = "grand_parent"    # Parent's Parent (对方是我的祖父母)
    IS_GRAND_CHILD_OF = "grand_child"      # Child's Child (对方是我的孙辈)
    # IS_SIBLING_OF 也可以是 calculated
    
    # 师门系 (Distance: 2)
    IS_MARTIAL_GRANDMASTER_OF = "martial_grandmaster" # Master's Master (对方是我的师祖)
    IS_MARTIAL_GRANDCHILD_OF = "martial_grandchild"   # Apprentice's Apprentice (对方是我的徒孙)
    IS_MARTIAL_SIBLING_OF = "martial_sibling"         # Shared Master (对方是我的同门)

    def __str__(self) -> str:
        from src.i18n import t
        return t(relation_msg_ids.get(self, self.value))

    @classmethod
    def from_chinese(cls, name_cn: str) -> "Relation|None":
        """
        依据中文显示名解析关系；无法解析返回 None。
        """
        if not name_cn:
            return None
        s = str(name_cn).strip()
        
        # 动态查找：遍历所有关系，翻译后比对
        from src.i18n import t
        for rel, msg_id in relation_msg_ids.items():
            # 这里假设当前环境语言是中文，或者我们需要强制用中文比对
            # 如果 name_cn 是 LLM 返回的中文，我们需要确保 t() 返回的是中文
            # 由于 gettext 通常基于全局上下文，这里依赖全局语言设置
            # 如果需要强制中文，可能需要临时切换 locale，但这里简化处理，假设 LLM 输出语言与当前 locale 一致
            if s == t(msg_id):
                return rel
        return None


relation_msg_ids = {
    Relation.IS_PARENT_OF: "parent",
    Relation.IS_CHILD_OF: "child",
    Relation.IS_SIBLING_OF: "sibling",
    Relation.IS_KIN_OF: "kin",
    Relation.IS_MASTER_OF: "master",
    Relation.IS_DISCIPLE_OF: "apprentice",
    Relation.IS_LOVER_OF: "lovers",
    Relation.IS_FRIEND_OF: "friend",
    Relation.IS_ENEMY_OF: "enemy",
    Relation.IS_SWORN_SIBLING_OF: "sworn_sibling",
    
    Relation.IS_GRAND_PARENT_OF: "grand_parent",
    Relation.IS_GRAND_CHILD_OF: "grand_child",
    Relation.IS_MARTIAL_GRANDMASTER_OF: "martial_grandmaster",
    Relation.IS_MARTIAL_GRANDCHILD_OF: "martial_grandchild",
    Relation.IS_MARTIAL_SIBLING_OF: "martial_sibling",
}

# 关系是否属于“先天”（血缘），其余为“后天”
INNATE_RELATIONS: set[Relation] = {
    Relation.IS_PARENT_OF, Relation.IS_CHILD_OF, Relation.IS_SIBLING_OF, Relation.IS_KIN_OF,
    Relation.IS_GRAND_PARENT_OF, Relation.IS_GRAND_CHILD_OF
}

# 自动计算的关系集合
CALCULATED_RELATIONS: set[Relation] = {
    Relation.IS_GRAND_PARENT_OF, Relation.IS_GRAND_CHILD_OF,
    Relation.IS_MARTIAL_GRANDMASTER_OF, Relation.IS_MARTIAL_GRANDCHILD_OF, Relation.IS_MARTIAL_SIBLING_OF,
    Relation.IS_SIBLING_OF 
}


# —— 规则定义 ——

ADD_RELATION_RULES: dict[Relation, str] = {
    Relation.IS_LOVER_OF: "relation_rule_lovers_add",
    Relation.IS_FRIEND_OF: "relation_rule_friend_add",
    Relation.IS_ENEMY_OF: "relation_rule_enemy_add",
    Relation.IS_MASTER_OF: "relation_rule_master_add",
    Relation.IS_DISCIPLE_OF: "relation_rule_apprentice_add",
    Relation.IS_SWORN_SIBLING_OF: "relation_rule_sworn_sibling_add",
}

CANCEL_RELATION_RULES: dict[Relation, str] = {
    Relation.IS_LOVER_OF: "relation_rule_lovers_cancel",
    Relation.IS_FRIEND_OF: "relation_rule_friend_cancel",
    Relation.IS_ENEMY_OF: "relation_rule_enemy_cancel",
    Relation.IS_MASTER_OF: "relation_rule_master_cancel",
    Relation.IS_DISCIPLE_OF: "relation_rule_apprentice_cancel",
    Relation.IS_SWORN_SIBLING_OF: "relation_rule_sworn_sibling_cancel",
}


def get_relation_rules_desc() -> str:
    """获取关系规则的描述文本，用于 Prompt"""
    from src.i18n import t
    lines = [t("relation_rule_establish_title")]
    for rel, desc in ADD_RELATION_RULES.items():
        lines.append(f"- {t(desc)}")
    lines.append(f"\n{t('relation_rule_cancel_title')}")
    for rel, desc in CANCEL_RELATION_RULES.items():
        lines.append(f"- {t(desc)}")
    return "\n".join(lines)


def is_innate(relation: Relation) -> bool:
    return relation in INNATE_RELATIONS


# 有向关系的对偶映射；对称关系映射到自身
RECIPROCAL_RELATION: dict[Relation, Relation] = {
    # 血缘
    Relation.IS_PARENT_OF: Relation.IS_CHILD_OF,  # 对方是我的父母 -> 对方看我是子女
    Relation.IS_CHILD_OF: Relation.IS_PARENT_OF,  # 对方是我的子女 -> 对方看我是父母
    Relation.IS_SIBLING_OF: Relation.IS_SIBLING_OF,  # 对方是我的兄弟姐妹 -> 对方看我是兄弟姐妹
    Relation.IS_KIN_OF: Relation.IS_KIN_OF,  # 亲属 -> 亲属
    Relation.IS_GRAND_PARENT_OF: Relation.IS_GRAND_CHILD_OF,
    Relation.IS_GRAND_CHILD_OF: Relation.IS_GRAND_PARENT_OF,

    # 后天
    Relation.IS_MASTER_OF: Relation.IS_DISCIPLE_OF,  # 对方是我的师傅 -> 对方看我是徒弟
    Relation.IS_DISCIPLE_OF: Relation.IS_MASTER_OF,  # 对方是我的徒弟 -> 对方看我是师傅
    Relation.IS_LOVER_OF: Relation.IS_LOVER_OF,  # 道侣 -> 道侣
    Relation.IS_FRIEND_OF: Relation.IS_FRIEND_OF,  # 朋友 -> 朋友
    Relation.IS_ENEMY_OF: Relation.IS_ENEMY_OF,  # 仇人 -> 仇人
    Relation.IS_MARTIAL_GRANDMASTER_OF: Relation.IS_MARTIAL_GRANDCHILD_OF,
    Relation.IS_MARTIAL_GRANDCHILD_OF: Relation.IS_MARTIAL_GRANDMASTER_OF,
    Relation.IS_MARTIAL_SIBLING_OF: Relation.IS_MARTIAL_SIBLING_OF,
    Relation.IS_SWORN_SIBLING_OF: Relation.IS_SWORN_SIBLING_OF,
}


def get_reciprocal(relation: Relation) -> Relation:
    """
    给定 A->B 的关系，返回应当写入 B->A 的关系。
    对于对称关系（如 FRIEND/ENEMY/LOVERS/SIBLING/KIN），返回其本身。
    """
    return RECIPROCAL_RELATION.get(relation, relation)


if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


# ——— 显示层：性别化称谓映射与标签工具 ———

GENDERED_DISPLAY: dict[tuple[Relation, str], str] = {
    # 我 -> 对方：CHILD（我为子，对方为父/母） → 显示对方为 父亲/母亲
    # NOW: 对方 IS_PARENT -> 显示对方为 父亲/母亲
    (Relation.IS_PARENT_OF, "male"): "relation_father",
    (Relation.IS_PARENT_OF, "female"): "relation_mother",
    # 我 -> 对方：PARENT（我为父/母，对方为子） → 显示对方为 儿子/女儿
    # NOW: 对方 IS_CHILD_OF -> 显示对方为 儿子/女儿
    (Relation.IS_CHILD_OF, "male"): "relation_son",
    (Relation.IS_CHILD_OF, "female"): "relation_daughter",
    # 祖父母 (对方 IS_GRAND_PARENT_OF)
    (Relation.IS_GRAND_PARENT_OF, "male"): "relation_grandfather",
    (Relation.IS_GRAND_PARENT_OF, "female"): "relation_grandmother",
    # 孙辈 (对方 IS_GRAND_CHILD_OF)
    (Relation.IS_GRAND_CHILD_OF, "male"): "relation_grandson",
    (Relation.IS_GRAND_CHILD_OF, "female"): "relation_granddaughter",
}

# 显示顺序配置
DISPLAY_ORDER = [
    "martial_grandmaster", "master", "martial_sibling", "apprentice", "martial_grandchild",
    "lovers",
    "relation_sworn_older_brother", "relation_sworn_younger_brother", "relation_sworn_older_sister", "relation_sworn_younger_sister",
    "sworn_sibling",
    "relation_grandfather", "relation_grandmother", "grand_parent", # 祖父母
    "relation_father", "relation_mother",
    "relation_older_brother", "relation_younger_brother", "relation_older_sister", "relation_younger_sister",
    "sibling", 
    "relation_son", "relation_daughter",
    "relation_grandson", "relation_granddaughter", "grand_child", # 孙辈
    "friend", "enemy",
    "kin"
]

def get_relation_label(relation: Relation, self_avatar: "Avatar", other_avatar: "Avatar") -> str:
    """
    获取 self_avatar 视角的 other_avatar 的称谓。
    """
    from src.i18n import t
    
    # 1. 处理兄弟姐妹/同门 (涉及长幼比较)
    if relation == Relation.IS_SIBLING_OF or relation == Relation.IS_MARTIAL_SIBLING_OF or relation == Relation.IS_SWORN_SIBLING_OF:
        is_older = False
        # 比较出生时间 (MonthStamp 越小越早出生，年龄越大)
        if hasattr(other_avatar, "birth_month_stamp") and hasattr(self_avatar, "birth_month_stamp"):
            if other_avatar.birth_month_stamp < self_avatar.birth_month_stamp:
                is_older = True
            elif other_avatar.birth_month_stamp == self_avatar.birth_month_stamp:
                # 同月生，简单按 ID 排序保证一致性
                is_older = str(other_avatar.id) < str(self_avatar.id)
        
        gender_val = getattr(getattr(other_avatar, "gender", None), "value", "male")
        
        if relation == Relation.IS_SIBLING_OF:
            if gender_val == "male":
                return t("relation_older_brother") if is_older else t("relation_younger_brother")
            else:
                return t("relation_older_sister") if is_older else t("relation_younger_sister")
        elif relation == Relation.IS_SWORN_SIBLING_OF:
            if gender_val == "male":
                return t("relation_sworn_older_brother") if is_older else t("relation_sworn_younger_brother")
            else:
                return t("relation_sworn_older_sister") if is_older else t("relation_sworn_younger_sister")
        else: # MARTIAL_SIBLING
            # 这里简单复用兄弟姐妹的 key，或者需要定义新的 key 如 martial_older_brother
            # 暂时使用通用的 sibling 称谓，或者如果有专用的 key
            if gender_val == "male":
                return t("relation_martial_older_brother") if is_older else t("relation_martial_younger_brother")
            else:
                return t("relation_martial_older_sister") if is_older else t("relation_martial_younger_sister")

    # 2. 查表处理通用性别化称谓
    other_gender = getattr(other_avatar, "gender", None)
    gender_val = getattr(other_gender, "value", "male")
    
    label_key = GENDERED_DISPLAY.get((relation, gender_val))
    if label_key:
        return t(label_key)

    # 3. 回退到默认显示名
    # 使用 relation_msg_ids 获取 msgid
    key = relation_msg_ids.get(relation, relation.value)
    return t(key)


def get_relations_strs(avatar: "Avatar", max_lines: int = 12) -> list[str]:
    """
    以“我”的视角整理关系，输出若干行。
    """
    from src.i18n import t
    # 融合 relations 和 computed_relations
    # 优先显示一阶关系（如果同一个key在两个字典都存在，relations 覆盖 computed_relations）
    # 但一般不会有重叠，除了 SIBLING 可能被提升为一阶
    relations = getattr(avatar, "computed_relations", {}).copy()
    relations.update(getattr(avatar, "relations", {}) or {})

    # 1. 收集并根据标签分组所有关系
    grouped: dict[str, list[str]] = defaultdict(list)
    for other, rel in relations.items():
        label = get_relation_label(rel, avatar, other)
        
        display_name = other.name
        # 死亡标记
        if getattr(other, "is_dead", False):
            d_info = getattr(other, "death_info", None)
            reason = d_info["reason"] if d_info and "reason" in d_info else t("Unknown reason")
            # 注意：这里的 label 已经是翻译过的了，display_name 也应该是 localized 的格式
            display_name = t("{name} (Deceased: {reason})", name=other.name, reason=reason)
            
        grouped[label].append(display_name)

    lines: list[str] = []
    processed_labels = set()

    # 2. 按照预定义顺序输出
    # DISPLAY_ORDER 里的都是 msgid，需要翻译后才能去 grouped 里查
    for msgid in DISPLAY_ORDER:
        label = t(msgid)
        if label in grouped:
            names = t("comma_separator").join(grouped[label])
            lines.append(t("{label}: {names}", label=label, names=names))
            processed_labels.add(label)

    # 3. 处理未在配置中列出的其他关系（按字典序）
    for label in sorted(grouped.keys()):
        if label not in processed_labels:
            names = t("comma_separator").join(grouped[label])
            lines.append(t("{label}: {names}", label=label, names=names))
            processed_labels.add(label)

    # 4. 若无任何关系
    if not lines:
        return [t("None")]

    return lines[:max_lines]


def relations_to_str(avatar: "Avatar", sep: str = None, max_lines: int = 6) -> str:
    from src.i18n import t
    if sep is None:
        sep = t("semicolon_separator")
    lines = get_relations_strs(avatar, max_lines=max_lines)
    # 如果只有一行且是"无"，直接返回
    if len(lines) == 1 and lines[0] == t("None"):
        return t("None")
    return sep.join(lines)
