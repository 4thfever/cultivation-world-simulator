"""
长期目标模块
为角色生成和管理长期目标（5-10年）
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar

from src.classes.event import Event
from src.utils.config import CONFIG
from src.utils.llm import call_llm_with_task_name
from src.run.log import get_logger
from src.classes.actions import get_action_infos_str
from src.i18n import t

logger = get_logger().logger


@dataclass
class LongTermObjective:
    """长期目标类"""
    content: str  # 目标内容
    origin: str  # "llm" 或 "user"
    set_year: int  # 设定时的年份


def can_generate_long_term_objective(avatar: "Avatar") -> bool:
    """
    检查角色是否需要生成/更新长期目标
    
    规则：
    1. 已有用户设定的目标，永不自动生成
    2. 无目标时，可以生成
    3. 距离上次设定 <5年，不生成
    4. 距离上次设定 ≥10年，必定生成
    5. 距离上次设定 5-10年，按概率生成（渐进概率）
    
    Args:
        avatar: 要检查的角色
        
    Returns:
        是否应该生成长期目标
    """
    # 已有用户设定的目标，不再自动生成
    if avatar.long_term_objective and avatar.long_term_objective.origin == "user":
        return False
    
    current_year = avatar.world.month_stamp.get_year()
    
    # 首次设定（无目标）
    if not avatar.long_term_objective:
        return True
    
    years_passed = current_year - avatar.long_term_objective.set_year
    
    if years_passed < 5:
        return False
    elif years_passed >= 10:
        return True
    else:  # 5-10年之间
        # 渐进概率：5年时10%，随时间推移逐渐增加，接近10年时接近100%
        probability = (years_passed - 5) / 5 * 0.9 + 0.1
        return random.random() < probability


async def generate_long_term_objective(avatar: "Avatar") -> Optional[LongTermObjective]:
    """
    为角色生成长期目标
    
    调用LLM基于角色信息和事件历史生成合适的长期目标
    
    Args:
        avatar: 要生成长期目标的角色
        
    Returns:
        生成的LongTermObjective对象，失败则返回None
    """
    # 准备世界信息（仅获取已知区域 + 距离信息）
    world_info = avatar.world.get_info(avatar=avatar)
    
    # 获取 expanded_info（包含详细信息和事件历史）
    expanded_info = avatar.get_expanded_info(detailed=True)
    
    # 准备模板参数
    template_path = CONFIG.paths.templates / "long_term_objective.txt"
    infos = {
        "world_info": world_info,
        "avatar_info": expanded_info,
        "general_action_infos": get_action_infos_str(),
    }
    
    # 调用LLM并自动解析JSON（使用配置的模型模式）
    response_data = await call_llm_with_task_name("long_term_objective", template_path, infos)
    
    content = response_data.get("long_term_objective", "").strip()
    
    if not content:
        logger.warning(f"为角色 {avatar.name} 生成长期目标失败：返回空内容")
        return None
    
    current_year = avatar.world.month_stamp.get_year()
    objective = LongTermObjective(
        content=content,
        origin="llm",
        set_year=current_year
    )
    
    logger.info(f"为角色 {avatar.name} 生成长期目标：{content}")
    
    return objective
        


async def process_avatar_long_term_objective(avatar: "Avatar") -> Optional[Event]:
    """
    处理单个角色的长期目标生成/更新
    
    检查角色是否需要生成目标，需要则生成并返回对应事件
    
    Args:
        avatar: 要处理的角色
        
    Returns:
        生成的事件，如果不需要生成或生成失败则返回None
    """
    if not can_generate_long_term_objective(avatar):
        return None
    
    old_objective = avatar.long_term_objective
    new_objective = await generate_long_term_objective(avatar)
    
    if not new_objective:
        return None
    
    avatar.long_term_objective = new_objective
    
    # 生成事件
    if old_objective:
        # 更新目标
        event = Event(
            avatar.world.month_stamp,
            t("{avatar_name} deliberated and redefined their long-term objective: {objective}", avatar_name=avatar.name, objective=new_objective.content),
            related_avatars=[avatar.id],
            is_major=False
        )
    else:
        # 首次设定目标
        event = Event(
            avatar.world.month_stamp,
            t("{avatar_name} determined their long-term objective: {objective}", avatar_name=avatar.name, objective=new_objective.content),
            related_avatars=[avatar.id],
            is_major=False
        )
    
    return event


def set_user_long_term_objective(avatar: "Avatar", objective_content: str) -> None:
    """
    玩家设定角色的长期目标
    
    用户设定后，origin标记为"user"，系统将不再自动调用LLM更新该目标
    但允许玩家再次调用此函数修改
    
    Args:
        avatar: 要设定目标的角色
        objective_content: 目标内容
    """
    current_year = avatar.world.month_stamp.get_year()
    avatar.long_term_objective = LongTermObjective(
        content=objective_content,
        origin="user",
        set_year=current_year
    )
    
    # 用户手动设定长期目标时，清空短期目标和后续计划，以便AI重新规划
    avatar.short_term_objective = ""
    avatar.clear_plans()
    
    logger.info(f"玩家为角色 {avatar.name} 设定长期目标：{objective_content}，并已清空短期目标和后续计划")


def clear_user_long_term_objective(avatar: "Avatar") -> bool:
    """
    清空玩家设定的长期目标
    如果当前目标是 system/llm 生成的，则不清除并返回 False
    如果是 user 生成的，清除并返回 True
    """
    if avatar.long_term_objective and avatar.long_term_objective.origin == "user":
        avatar.long_term_objective = None
        logger.info(f"玩家清空了角色 {avatar.name} 的长期目标")
        return True
    return False
