import asyncio
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar

from src.classes.ai import call_llm_with_task_name
from src.utils.config import CONFIG
from src.run.log import get_logger

logger = get_logger().logger

def can_get_backstory(avatar: "Avatar") -> bool:
    """
    判断角色是否需要生成身世。
    """
    if avatar.is_dead:
        return False
    
    # 如果已经有身世了，就不再生成
    if avatar.backstory is not None:
        return False
        
    return True

async def generate_backstory(avatar: "Avatar") -> Optional[str]:
    """
    调用 LLM 生成角色身世。
    """
    try:
        from src.classes.core.world import World
        
        infos = {
            "world_info": str(avatar.world.get_info()),
            "world_lore": avatar.world.world_lore.text,
            "avatar_info": str(avatar.get_expanded_info(detailed=True))
        }
        
        template_path = CONFIG.paths.templates / "backstory.txt"
        
        # 调用 LLM，使用配置中的 backstory task (默认 fast)
        response_data = await call_llm_with_task_name("backstory", template_path, infos)
        
        backstory = response_data.get("backstory", "").strip()
        
        if not backstory:
            return None
            
        logger.info(f"为角色 {avatar.name} 生成身世：{backstory}")
        return backstory
        
    except Exception as e:
        logger.error(f"生成身世失败 {avatar.name}: {e}")
        return None

async def process_avatar_backstory(avatar: "Avatar") -> None:
    """
    为角色生成并设置身世（如果不满足条件则跳过）。
    无返回值，直接修改 avatar 属性。
    """
    if not can_get_backstory(avatar):
        return
        
    backstory = await generate_backstory(avatar)
    
    if backstory:
        avatar.backstory = backstory
