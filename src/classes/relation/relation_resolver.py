from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple, Optional
import asyncio

from src.classes.relation.relation import (
    Relation,
    get_relation_rules_desc
)
from src.classes.relation.relations import (
    set_relation,
    cancel_relation,
)
from src.systems.time import get_date_str
from src.classes.event import Event
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
            
        recent_events_text = "\n".join(event_lines) if event_lines else "近期无显著交互记录。"
        
        # 2. 获取当前关系描述
        current_rel = avatar_a.get_relation(avatar_b)
        rel_desc = "无"
        if current_rel:
            rel_name = str(current_rel)
            rel_desc = f"{rel_name}"
        
        # 获取当前世界时间
        current_time_str = get_date_str(avatar_a.world.month_stamp)
        
        return {
            "relation_rules_desc": get_relation_rules_desc(),
            "avatar_a_name": avatar_a.name,
            "avatar_a_info": str(avatar_a.get_info(detailed=True)),
            "avatar_b_name": avatar_b.name,
            "avatar_b_info": str(avatar_b.get_info(detailed=True)),
            "current_relations": f"目前关系：{rel_desc}",
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
            
            # 使用新语义方法更安全
            target_method = None
            if rel == Relation.IS_MASTER_OF:
                # A 是 B 的 Master -> B 拜 A 为师
                avatar_b.acknowledge_master(avatar_a)
            elif rel == Relation.IS_DISCIPLE_OF:
                # A 是 B 的 Disciple -> B 收 A 为徒
                avatar_b.accept_disciple(avatar_a)
            elif rel == Relation.IS_PARENT_OF:
                # A 是 B 的 Parent -> B 认 A 为父/母
                avatar_b.acknowledge_parent(avatar_a)
            elif rel == Relation.IS_CHILD_OF:
                # A 是 B 的 Child -> B 认 A 为子/女
                avatar_b.acknowledge_child(avatar_a)
            elif rel == Relation.IS_LOVER_OF:
                avatar_b.become_lovers_with(avatar_a)
            elif rel == Relation.IS_FRIEND_OF:
                avatar_b.make_friend_with(avatar_a)
            elif rel == Relation.IS_ENEMY_OF:
                avatar_b.make_enemy_of(avatar_a)
            else:
                # 回退到底层方法 (set_relation(B, A, rel))
                avatar_b.set_relation(avatar_a, rel)
            
            event_text = f"因为{reason}，{avatar_a.name}成为{avatar_b.name}的{display_name}。"
            event = Event(month_stamp, event_text, related_avatars=[avatar_a.id, avatar_b.id], is_major=True)
            
        elif c_type == "REMOVE":
            # 同样反转调用
            # 移除关系只能用底层 cancel_relation
            success = cancel_relation(avatar_b, avatar_a, rel)
            if success:
                event_text = f"因为{reason}，{avatar_a.name}不再是{avatar_b.name}的{display_name}。"
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
