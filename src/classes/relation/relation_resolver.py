from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple, Optional
import asyncio

from src.i18n import t
from src.classes.relation.relation import Relation
from src.classes.relation.relations import (
    set_relation,
    cancel_relation,
)
from src.systems.time import get_date_str
from src.classes.event import Event
from src.classes.close_relation_event_service import (
    apply_positive_bond_warmth,
    configure_positive_bond_event,
)
from src.utils.llm import call_llm_with_task_name
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar

class RelationResolver:
    TEMPLATE_PATH = CONFIG.paths.templates / "relation_update.txt"
    
    @staticmethod
    def _build_prompt_data(avatar_a: "Avatar", avatar_b: "Avatar") -> dict:
        # 1. 获取近期交互记录
        # 优先使用 EventManager 的索引
        event_manager = avatar_a.world.event_manager
        
        # 获取已归档的历史事件 (取最近10条)
        # get_events_between 返回的是按时间正序排列的
        recent_events = event_manager.get_events_between(avatar_a.id, avatar_b.id, limit=10)
        
        event_lines = [str(e) for e in recent_events]
            
        recent_events_text = "\n".join(event_lines) if event_lines else t("No significant recent interactions.")
        
        # 2. 获取当前关系描述
        current_rel = avatar_a.get_relation(avatar_b)
        rel_desc = t("None")
        if current_rel:
            rel_name = str(current_rel)
            rel_desc = f"{rel_name}"
        
        # 获取当前世界时间
        current_time_str = get_date_str(avatar_a.world.month_stamp)
        
        return {
            "relation_rules_desc": "",
            "avatar_a_name": avatar_a.name,
            "avatar_a_info": str(avatar_a.get_info(detailed=True)),
            "avatar_b_name": avatar_b.name,
            "avatar_b_info": str(avatar_b.get_info(detailed=True)),
            "current_relations": t("Current relations: {rel_desc}", rel_desc=rel_desc),
            "recent_events_text": recent_events_text,
            "current_time": current_time_str
        }

    @staticmethod
    async def resolve_pair(avatar_a: "Avatar", avatar_b: "Avatar") -> Optional[Event]:
        """
        处理一对角色的关系变化，返回产生的事件
        """
        infos = RelationResolver._build_prompt_data(avatar_a, avatar_b)
        
        result = await call_llm_with_task_name("relation_resolver", RelationResolver.TEMPLATE_PATH, infos)
            
        changed = result.get("changed", False)
        if not changed:
            return None
            
        month_stamp = avatar_a.world.month_stamp
        
        c_type = result.get("change_type")
        rel_name = result.get("relation")
        reason = result.get("reason", "")
        
        if not rel_name:
            return None

        # 解析关系枚举
        try:
            # 尝试通过新名称获取
            rel = Relation[rel_name]
        except KeyError:
            return None
            
        display_name = str(rel)
        event = None
            
        if c_type == "ADD":
            # 逻辑说明：如果 LLM 输出 "IS_MASTER_OF" (Key) 或 "master" (Value)
            # 意味着 A 是 B 的 Master。
            # set_relation(from, to, rel) 意为：from 认为 to 是 rel。
            # 如果 A 是 B 的 Master，那么 B 应该认为 A 是 IS_MASTER_OF。
            # 所以调用 set_relation(B, A, IS_MASTER_OF)。
            
            event_type = "relationship_major"
            # 使用新语义方法更安全
            target_method = None
            if rel == Relation.IS_MASTER_OF:
                # A 是 B 的 Master -> B 拜 A 为师
                avatar_b.acknowledge_master(avatar_a)
                event_type = "bond_master_disciple_formed"
            elif rel == Relation.IS_DISCIPLE_OF:
                # A 是 B 的 Disciple -> B 收 A 为徒
                avatar_b.accept_disciple(avatar_a)
                event_type = "bond_master_disciple_formed"
            elif rel == Relation.IS_PARENT_OF:
                # A 是 B 的 Parent -> B 认 A 为父/母
                avatar_b.acknowledge_parent(avatar_a)
            elif rel == Relation.IS_CHILD_OF:
                # A 是 B 的 Child -> B 认 A 为子/女
                avatar_b.acknowledge_child(avatar_a)
            elif rel == Relation.IS_LOVER_OF:
                avatar_b.become_lovers_with(avatar_a)
                event_type = "bond_lovers_formed"
            else:
                # 回退到底层方法 (set_relation(B, A, rel))
                avatar_b.set_relation(avatar_a, rel)
                if rel == Relation.IS_SWORN_SIBLING_OF:
                    event_type = "bond_sworn_sibling_formed"
            
            event_text = t(
                "Because {reason}, {avatar_a} became {avatar_b}'s {relation}.",
                reason=reason,
                avatar_a=avatar_a.name,
                avatar_b=avatar_b.name,
                relation=display_name,
            )
            event = Event(
                month_stamp,
                event_text,
                related_avatars=[avatar_a.id, avatar_b.id],
                is_major=True,
                event_type=event_type,
            )
            if event_type in {
                "bond_master_disciple_formed",
                "bond_lovers_formed",
                "bond_sworn_sibling_formed",
            }:
                configure_positive_bond_event(event, avatar_a=avatar_a, avatar_b=avatar_b)
                apply_positive_bond_warmth(subject=avatar_a, other_party=avatar_b, event_type=event_type)
                apply_positive_bond_warmth(subject=avatar_b, other_party=avatar_a, event_type=event_type)
            
        elif c_type == "REMOVE":
            # 同样反转调用
            # 移除关系只能用底层 cancel_relation
            success = cancel_relation(avatar_b, avatar_a, rel)
            if success:
                event_text = t(
                    "Because {reason}, {avatar_a} is no longer {avatar_b}'s {relation}.",
                    reason=reason,
                    avatar_a=avatar_a.name,
                    avatar_b=avatar_b.name,
                    relation=display_name,
                )
                event = Event(month_stamp, event_text, related_avatars=[avatar_a.id, avatar_b.id], is_major=True)

        if event:
            return event
            
        return None

    @staticmethod
    async def run_batch(pairs: List[Tuple["Avatar", "Avatar"]]) -> List[Event]:
        """
        批量并发处理，返回产生的所有事件
        """
        if not pairs:
            return []

        # 并发执行所有任务
        tasks = [RelationResolver.resolve_pair(a, b) for a, b in pairs]
        results = await asyncio.gather(*tasks)
        
        # 过滤掉 None 结果 (resolve_pair 失败或无变化时返回 None)
        return [res for res in results if res]
