"""
两个角色之间的关系操作函数
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List

from src.classes.relation.relation import (
    Relation, 
    INNATE_RELATIONS, 
    get_reciprocal, 
    is_innate, 
    CALCULATED_RELATIONS
)
from src.classes.event import Event
from src.classes.action.event_helper import EventHelper

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


def update_second_degree_relations(avatar: "Avatar") -> None:
    """
    计算并更新角色的二阶关系缓存。
    覆盖 SIBLING, GRAND_PARENT, MARTIAL_SIBLING 等。
    """
    computed = {}
    
    # 1. 预筛选一阶关键人 (中间节点)
    relations = getattr(avatar, "relations", {})
    
    parents = [t for t, r in relations.items() if r == Relation.IS_PARENT_OF]
    children = [t for t, r in relations.items() if r == Relation.IS_CHILD_OF]
    masters = [t for t, r in relations.items() if r == Relation.IS_MASTER_OF]
    apprentices = [t for t, r in relations.items() if r == Relation.IS_DISCIPLE_OF]

    # 2. 血缘推导
    # Sibling: 父母的子女 (排除自己)
    for p in parents:
        # 注意：这里需要访问 parent 的 relations
        # 如果 parent 是死者或者未完全加载，需要确保其 relations 可用
        p_relations = getattr(p, "relations", {})
        for sib, r in p_relations.items():
            if r == Relation.IS_CHILD_OF and sib.id != avatar.id:
                computed[sib] = Relation.IS_SIBLING_OF
                
    # Grandparent: 父母的父母
    for p in parents:
        p_relations = getattr(p, "relations", {})
        for gp, r in p_relations.items():
            if r == Relation.IS_PARENT_OF:
                computed[gp] = Relation.IS_GRAND_PARENT_OF

    # Grandchild: 子女的子女
    for c in children:
        c_relations = getattr(c, "relations", {})
        for gc, r in c_relations.items():
            if r == Relation.IS_CHILD_OF:
                computed[gc] = Relation.IS_GRAND_CHILD_OF

    # 3. 师门推导
    # Martial Sibling: 师傅的徒弟 (排除自己)
    for m in masters:
        m_relations = getattr(m, "relations", {})
        for fellow, r in m_relations.items():
            if r == Relation.IS_DISCIPLE_OF and fellow.id != avatar.id:
                computed[fellow] = Relation.IS_MARTIAL_SIBLING_OF
                
    # Martial Grandmaster: 师傅的师傅
    for m in masters:
        m_relations = getattr(m, "relations", {})
        for mgm, r in m_relations.items():
            if r == Relation.IS_MASTER_OF:
                computed[mgm] = Relation.IS_MARTIAL_GRANDMASTER_OF

    # Martial Grandchild: 徒弟的徒弟
    for app in apprentices:
        app_relations = getattr(app, "relations", {})
        for mgc, r in app_relations.items():
            if r == Relation.IS_DISCIPLE_OF:
                computed[mgc] = Relation.IS_MARTIAL_GRANDCHILD_OF

    # 4. 更新缓存
    avatar.computed_relations = computed


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
    if existing_to_from != Relation.IS_FRIEND_OF:
        candidates.append(Relation.IS_FRIEND_OF)

    # - ENEMY
    if existing_to_from != Relation.IS_ENEMY_OF:
        candidates.append(Relation.IS_ENEMY_OF)

    # - LOVERS：异性（Avatar 定义确保性别存在）
    if from_avatar.gender != to_avatar.gender and existing_to_from != Relation.IS_LOVER_OF:
        candidates.append(Relation.IS_LOVER_OF)

    # - SWORN_SIBLING：结拜（不限性别）
    if existing_to_from != Relation.IS_SWORN_SIBLING_OF:
        candidates.append(Relation.IS_SWORN_SIBLING_OF)

    # - 师徒（方向性）：
    #   MASTER：to 是 from 的师傅 → to.level >= from.level + 20
    #   APPRENTICE：to 是 from 的徒弟 → to.level <= from.level - 20
    if level_to >= level_from + 20 and existing_to_from != Relation.IS_MASTER_OF:
        candidates.append(Relation.IS_MASTER_OF)
    if level_to <= level_from - 20 and existing_to_from != Relation.IS_DISCIPLE_OF:
        candidates.append(Relation.IS_DISCIPLE_OF)

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
    
    # [新增] 如果是道侣关系，记录开始时间
    if relation == Relation.IS_LOVER_OF:
        current_time = int(from_avatar.world.month_stamp)
        # 双方都记录
        from_avatar.relation_start_dates[to_avatar.id] = current_time
        to_avatar.relation_start_dates[from_avatar.id] = current_time

    # [新增] 师徒强绑定宗门
    if relation == Relation.IS_MASTER_OF:
        # from 认 to 为师傅 (to 是师傅)
        if to_avatar.sect is not None and from_avatar.sect != to_avatar.sect:
            from src.classes.sect_ranks import get_rank_from_realm
            from_avatar.join_sect(to_avatar.sect, get_rank_from_realm(from_avatar.cultivation_progress.realm))
    elif relation == Relation.IS_DISCIPLE_OF:
        # from 收 to 为徒弟 (from 是师傅)
        if from_avatar.sect is not None and to_avatar.sect != from_avatar.sect:
            from src.classes.sect_ranks import get_rank_from_realm
            to_avatar.join_sect(from_avatar.sect, get_rank_from_realm(to_avatar.cultivation_progress.realm))



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

    # [新增] 清理时间记录
    from_avatar.relation_start_dates.pop(to_avatar.id, None)
    to_avatar.relation_start_dates.pop(from_avatar.id, None)



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


def get_relation_change_context(avatar1: "Avatar", avatar2: "Avatar") -> tuple[list[str], list[str]]:
    """
    获取两角色间可能的新增关系和取消关系的中文显示列表。
    用于构建 Prompt 上下文。
    
    返回：(possible_new_relations, possible_cancel_relations)
    """
    # 计算 avatar2 相对于 avatar1 的可能关系
    new_rels = get_possible_new_relations(avatar1, avatar2)
    cancel_rels = get_possible_cancel_relations(avatar1, avatar2)
    
    new_strs = [str(r) for r in new_rels]
    cancel_strs = [str(r) for r in cancel_rels]
    
    return new_strs, cancel_strs


def process_relation_changes(initiator: "Avatar", target: "Avatar", result_dict: dict, month_stamp: int) -> None:
    """
    处理 LLM 返回的关系变更请求。
    兼容 Conversation 和 StoryTeller 的通用逻辑。
    """
    new_relation_str = str(result_dict.get("new_relation", "")).strip()
    # 兼容模板中的拼写错误 (cancal -> cancel)
    cancel_relation_str = str(result_dict.get("cancel_relation", "")).strip()
    if not cancel_relation_str:
        cancel_relation_str = str(result_dict.get("cancal_relation", "")).strip()

    # 处理进入新关系
    if new_relation_str:
        rel = Relation.from_chinese(new_relation_str)
        if rel is not None:
            # 逻辑：new_relation_str 是显示名（如"朋友"），解析为 Relation.IS_FRIEND_OF
            # 意味着 initiator 和 target 建立这个关系。
            # 通常 StoryTeller 的语境是：initiator (我) 认为 target (对方) 是 new_relation_str
            # 所以调用 initiator.set_relation(target, rel)
            
            # 使用新语义方法
            if rel == Relation.IS_MASTER_OF:
                # initiator 视 target 为 Master -> initiator 拜 target 为师
                initiator.acknowledge_master(target)
            elif rel == Relation.IS_DISCIPLE_OF:
                # initiator 视 target 为 Disciple -> initiator 收 target 为徒
                initiator.accept_disciple(target)
            elif rel == Relation.IS_PARENT_OF:
                initiator.acknowledge_parent(target)
            elif rel == Relation.IS_CHILD_OF:
                initiator.acknowledge_child(target)
            elif rel == Relation.IS_LOVER_OF:
                initiator.become_lovers_with(target)
            elif rel == Relation.IS_SWORN_SIBLING_OF:
                initiator.become_sworn_sibling_with(target)
            elif rel == Relation.IS_FRIEND_OF:
                initiator.make_friend_with(target)
            elif rel == Relation.IS_ENEMY_OF:
                initiator.make_enemy_of(target)
            else:
                initiator.set_relation(target, rel)

            set_event = Event(
                month_stamp, 
                f"{initiator.name} 与 {target.name} 的关系变为：{str(rel)}", 
                related_avatars=[initiator.id, target.id],
                is_major=True
            )
            EventHelper.push_pair(set_event, initiator=initiator, target=target, to_sidebar_once=True)

    # 处理取消关系
    if cancel_relation_str:
        rel = Relation.from_chinese(cancel_relation_str)
        if rel is not None:
            success = cancel_relation(initiator, target, rel)
            if success:
                cancel_event = Event(
                    month_stamp, 
                    f"{initiator.name} 与 {target.name} 取消了关系：{str(rel)}", 
                    related_avatars=[initiator.id, target.id],
                    is_major=True
                )
                EventHelper.push_pair(cancel_event, initiator=initiator, target=target, to_sidebar_once=True)
