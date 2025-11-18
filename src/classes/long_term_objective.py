"""
长期目标模块
为角色生成和管理长期目标（3-5年）
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
import random

if TYPE_CHECKING:
    from src.classes.avatar import Avatar

from src.classes.event import Event
from src.utils.config import CONFIG
from src.utils.llm import get_prompt_and_call_llm_async
from src.run.log import get_logger

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
    3. 距离上次设定 <3年，不生成
    4. 距离上次设定 ≥5年，必定生成
    5. 距离上次设定 3-5年，按概率生成（渐进概率）
    
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
    
    if years_passed < 3:
        return False
    elif years_passed >= 5:
        return True
    else:  # 3-5年之间
        # 渐进概率：3年时10%，4年时50%，接近5年时接近100%
        probability = (years_passed - 3) / 2 * 0.9 + 0.1
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

    # 准备世界信息
    world_info = avatar.world.get_info()
    
    # 准备角色信息
    avatar_info = avatar.get_info(detailed=True)
    avatar_info_str = "\n".join([f"{k}: {v}" for k, v in avatar_info.items()])
    
    # 获取事件历史
    em = avatar.world.event_manager
    major_limit = CONFIG.social.major_event_context_num
    minor_limit = CONFIG.social.minor_event_context_num
    major_events = em.get_major_events_by_avatar(avatar.id, limit=major_limit)
    minor_events = em.get_minor_events_by_avatar(avatar.id, limit=minor_limit)
    
    major_events_str = "\n".join([f"- {str(e)}" for e in major_events]) if major_events else "无"
    minor_events_str = "\n".join([f"- {str(e)}" for e in minor_events]) if minor_events else "无"
    
    # 准备模板参数
    template_path = CONFIG.paths.templates / "long_term_objective.txt"
    infos = {
        "world_info": world_info,
        "avatar_info": avatar_info_str,
        "major_events": major_events_str,
        "minor_events": minor_events_str
    }
    
    # 调用LLM并自动解析JSON（使用fast模型）
    response_data = await get_prompt_and_call_llm_async(template_path, infos, mode="fast")
    
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
            f"{avatar.name}经过深思熟虑，重新确定了自己的长期目标：{new_objective.content}",
            related_avatars=[avatar.id],
            is_major=False
        )
    else:
        # 首次设定目标
        event = Event(
            avatar.world.month_stamp,
            f"{avatar.name}确定了自己的长期目标：{new_objective.content}",
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
    logger.info(f"玩家为角色 {avatar.name} 设定长期目标：{objective_content}")

