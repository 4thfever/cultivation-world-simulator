"""
两个角色之间的关系操作函数
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List

from src.classes.relation import Relation, INNATE_RELATIONS, get_reciprocal, is_innate

if TYPE_CHECKING:
    from src.classes.avatar import Avatar


def get_possible_new_relations(from_avatar: "Avatar", to_avatar: "Avatar") -> List[Relation]:
    """
    评估"to_avatar 相对于 from_avatar"可能新增的后天关系集合（方向性明确）。

    清晰规则：
    - LOVERS(道侣)：要求男女异性；若已存在 to->from 的相同关系则不重复
    - MASTER(师傅)：要求 to.level >= from.level + 20
    - APPRENTICE(徒弟)：要求 to.level <= from.level - 20
    - FRIEND(朋友)：始终可能(若未已存在)
    - ENEMY(仇人)：始终可能(若未已存在)

    说明：本函数只判断"是否可能"，不做概率与人格相关控制；概率留给上层逻辑。
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


def set_relation(from_avatar: "Avatar", to_avatar: "Avatar", relation: Relation) -> None:
    """
    设置 from_avatar 对 to_avatar 的关系。
    - 对称关系（如 FRIEND/ENEMY/LOVERS/SIBLING/KIN）会在对方处写入相同的关系。
    - 有向关系（如 MASTER、APPRENTICE、PARENT、CHILD）会在对方处写入对偶关系。
    """
    if to_avatar is from_avatar:
        return
    from_avatar.relations[to_avatar] = relation
    # 写入对方的对偶关系（对称关系会得到同一枚举值）
    to_avatar.relations[from_avatar] = get_reciprocal(relation)


def get_relation(from_avatar: "Avatar", to_avatar: "Avatar") -> Relation | None:
    """
    获取 from_avatar 对 to_avatar 的关系。
    """
    return from_avatar.relations.get(to_avatar)


def clear_relation(from_avatar: "Avatar", to_avatar: "Avatar") -> None:
    """
    清除 from_avatar 和 to_avatar 之间的关系（双向清除）。
    """
    from_avatar.relations.pop(to_avatar, None)
    to_avatar.relations.pop(from_avatar, None)


def cancel_relation(from_avatar: "Avatar", to_avatar: "Avatar", relation: Relation) -> bool:
    """
    取消指定的后天关系。
    - 只能取消后天关系（INNATE_RELATIONS 不可取消）
    - 检查该关系是否存在且匹配
    - 双向清除
    
    返回：是否成功取消
    """
    # 先天关系不可取消
    if is_innate(relation):
        return False
    
    # 检查关系是否存在且匹配
    existing = get_relation(from_avatar, to_avatar)
    if existing != relation:
        return False
    
    # 清除关系
    clear_relation(from_avatar, to_avatar)
    return True


def get_possible_cancel_relations(from_avatar: "Avatar", to_avatar: "Avatar") -> List[Relation]:
    """
    获取可能取消的关系列表（仅后天关系）。
    
    返回：from_avatar 对 to_avatar 的可取消关系列表
    """
    existing = get_relation(from_avatar, to_avatar)
    if existing is None:
        return []
    
    # 只有后天关系可以取消
    if is_innate(existing):
        return []
    
    return [existing]

