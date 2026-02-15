"""
绰号生成模块
为满足条件的角色生成修仙界绰号
"""
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.core.world import World

from src.classes.event import Event
from src.utils.config import CONFIG
from src.utils.llm import call_llm_with_task_name
from src.run.log import get_logger

from src.classes.nickname_data import Nickname

logger = get_logger().logger


def can_get_nickname(avatar: "Avatar") -> bool:
    """
    检查角色是否满足获得绰号的条件
    
    条件：
    1. 尚未拥有绰号（nickname为None）
    2. 长期事件数量 >= major_event_threshold
    3. 短期事件数量 >= minor_event_threshold
    
    Args:
        avatar: 要检查的角色
        
    Returns:
        是否满足条件
    """
    # 检查是否已有绰号及其有效期
    if avatar.nickname is not None:
        current_year = avatar.world.month_stamp.get_year()
        # 如果未满10年，则不生成
        if current_year - avatar.nickname.created_year < 10:
            return False
    
    # 检查事件数量
    em = avatar.world.event_manager
    major_threshold = CONFIG.nickname.major_event_threshold
    minor_threshold = CONFIG.nickname.minor_event_threshold
    
    major_events = em.get_major_events_by_avatar(avatar.id, limit=major_threshold)
    minor_events = em.get_minor_events_by_avatar(avatar.id, limit=minor_threshold)
    
    major_count = len(major_events)
    minor_count = len(minor_events)
    
    # AND逻辑：两个条件都要满足
    return major_count >= major_threshold and minor_count >= minor_threshold


async def generate_nickname(avatar: "Avatar") -> Optional[dict]:
    """
    为角色生成绰号
    
    调用LLM基于角色信息和事件历史生成合适的绰号
    
    Args:
        avatar: 要生成绰号的角色
        
    Returns:
        包含 nickname 和 reason 的字典，失败则返回None
    """
    try:
        # 获取 expanded_info（包含详细信息和事件历史）
        expanded_info = avatar.get_expanded_info(detailed=True)
        
        # 准备模板参数
        template_path = CONFIG.paths.templates / "nickname.txt"
        infos = {
            "world_info": avatar.world.static_info,
            "avatar_info": expanded_info,
        }
        
        # 调用LLM并自动解析JSON
        response_data = await call_llm_with_task_name("nickname", template_path, infos)
        
        nickname = response_data.get("nickname", "").strip()
        thinking = response_data.get("thinking", "")
        reason = response_data.get("reason", "").strip()
        
        if not nickname:
            logger.warning(f"为角色 {avatar.name} 生成绰号失败：返回空绰号")
            return None
        
        logger.info(f"为角色 {avatar.name} 生成绰号：{nickname} (原因：{reason})")
        logger.debug(f"绰号生成思考过程：{thinking}")
        
        return {
            "nickname": nickname,
            "reason": reason
        }
        
    except Exception as e:
        logger.error(f"生成绰号时出错：{e}")
        return None


async def process_avatar_nickname(avatar: "Avatar") -> Optional[Event]:
    """
    处理单个角色的绰号生成
    
    检查角色是否满足条件，满足则生成绰号并返回对应事件
    
    Args:
        avatar: 要处理的角色
        
    Returns:
        生成的事件，如果不满足条件或生成失败则返回None
    """
    if not can_get_nickname(avatar):
        return None
    
    result = await generate_nickname(avatar)
    if not result:
        return None
    
    nickname_str = result["nickname"]
    reason = result["reason"]
    
    current_year = avatar.world.month_stamp.get_year()
    avatar.nickname = Nickname(value=nickname_str, reason=reason, created_year=current_year)
    
    # 生成事件：角色获得绰号
    event = Event(
        avatar.world.month_stamp,
        f"{avatar.name}在修仙界中闯出名号，被人称为「{nickname_str}」。",
        related_avatars=[avatar.id],
        is_major=True
    )
    return event

