from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple

from src.classes.relation import (
    Relation,
    get_relation_rules_desc,
    relation_display_names
)
from src.classes.relations import (
    set_relation,
    cancel_relation,
)
from src.classes.calendar import get_date_str
from src.classes.event import Event
from src.classes.action.event_helper import EventHelper
from src.utils.llm import call_llm_with_template, LLMMode
from src.utils.config import CONFIG

if TYPE_CHECKING:
    from src.classes.avatar import Avatar

from src.utils.ai_batch import AITaskBatch

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
            rel_name = relation_display_names.get(current_rel, current_rel.value)
            rel_desc = f"{rel_name}"
        
        # 获取当前世界时间
        current_time_str = get_date_str(avatar_a.world.month_stamp)
        
        return {
            "relation_rules_desc": get_relation_rules_desc(),
            "avatar_a_info": str(avatar_a.get_info(detailed=True)),
            "avatar_a_name": avatar_a.name,
            "avatar_b_info": str(avatar_b.get_info(detailed=True)),
            "current_relations": f"目前关系：{rel_desc}",
            "recent_events_text": recent_events_text,
            "current_time": current_time_str
        }

    @staticmethod
    async def resolve_pair(avatar_a: "Avatar", avatar_b: "Avatar") -> None:
        """
        处理一对角色的关系变化
        """
        infos = RelationResolver._build_prompt_data(avatar_a, avatar_b)
        
        result = await call_llm_with_template(RelationResolver.TEMPLATE_PATH, infos, mode=LLMMode.FAST)
            
        changed = result.get("changed", False)
        if not changed:
            return
            
        month_stamp = avatar_a.world.month_stamp
        
        c_type = result.get("change_type")
        rel_name = result.get("relation")
        reason = result.get("reason", "")
        
        if not rel_name:
            return

        # 解析关系枚举
        try:
            rel = Relation[rel_name]
        except KeyError:
            return
            
        display_name = relation_display_names.get(rel, rel_name)
            
        if c_type == "ADD":
            # 检查是否已有
            # Prompt 定义：输出 MASTER 意味着 A 是 B 的师傅
            # 代码逻辑：set_relation(from, to, rel) -> from.relations[to] = rel (from 认为 to 是 rel)
            # 因此，如果 LLM 输出 MASTER (A 是师傅)，意味着 A 认为 B 是徒弟(APPRENTICE)，B 认为 A 是师傅(MASTER)
            # 所以我们要调用 set_relation(B, A, MASTER) 或者 set_relation(A, B, APPRENTICE)
            # 统一逻辑：以“谁视谁为某个关系”来思考。
            # 如果 rel 是 A 的身份（如 MASTER），则 B 视 A 为 rel。
            # 调用 set_relation(B, A, rel) 会设置 B.relations[A] = rel
            # set_relation 内部会自动处理对偶关系，所以 A.relations[B] 也会被设为 APPRENTICE
            
            # 但要注意对称关系（LOVERS, FRIEND, ENEMY）。
            # A 是 B 的朋友 -> B 视 A 为 FRIEND。 set_relation(B, A, FRIEND) -> A.relations[B] = FRIEND (正确)
            
            # 结论：始终调用 set_relation(avatar_b, avatar_a, rel)
            
            current_rel = avatar_b.get_relation(avatar_a)
            if current_rel == rel:
                return
                
            set_relation(avatar_b, avatar_a, rel)
            
            event_text = f"【关系新增】{reason}，{avatar_a.name} 与 {avatar_b.name} 结为{display_name}。"
            event = Event(month_stamp, event_text, related_avatars=[avatar_a.id, avatar_b.id], is_major=True)
            EventHelper.push_pair(event, initiator=avatar_a, target=avatar_b, to_sidebar_once=True)
            
        elif c_type == "REMOVE":
            # 同样反转调用
            success = cancel_relation(avatar_b, avatar_a, rel)
            if success:
                event_text = f"【关系断绝】{reason}，{avatar_a.name} 与 {avatar_b.name} 不再是{display_name}。"
                event = Event(month_stamp, event_text, related_avatars=[avatar_a.id, avatar_b.id], is_major=True)
                EventHelper.push_pair(event, initiator=avatar_a, target=avatar_b, to_sidebar_once=True)

    @staticmethod
    async def run_batch(pairs: List[Tuple["Avatar", "Avatar"]]) -> None:
        """
        批量并发处理
        """
        if not pairs:
            return
            
        async with AITaskBatch() as batch:
            for a, b in pairs:
                batch.add(RelationResolver.resolve_pair(a, b))

