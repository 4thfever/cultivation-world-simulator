import random
import asyncio
from typing import Optional

from src.utils.config import CONFIG
from src.classes.core.avatar import Avatar
from src.classes.core.world import World
from src.classes.event import Event
from src.utils.llm.client import call_llm_with_task_name
from src.utils.df import game_configs
from src.i18n import t
from src.classes.observe import get_avatar_observation_radius
from src.run.log import get_logger

async def try_trigger_random_minor_event(avatar: Avatar, world: World) -> Optional[Event]:
    """
    尝试触发角色的随机小事。
    规则：
    - 根据 config 中的概率随机触发
    - 从 random_minor_event 配置中随机选择一个事由
    - 根据配置需要，单人或双人。如果是双人，在感知范围内找一个角色，找不到则使用路人（匿名群演）
    - 调用 LLM (fast mode) 生成事件文本
    - 产生一个小事件 (is_major=False)
    """
    base_prob = float(getattr(CONFIG.game, "random_minor_event_prob", 0.05))
    if base_prob <= 0.0:
        return None

    if not avatar.can_trigger_world_event:
        return None

    if random.random() >= base_prob:
        return None

    # Load configs
    records = game_configs.get("random_minor_event", [])
    if not records:
        return None

    record = random.choice(records)
    participants = int(record.get("participants", 1))
    desc = str(record.get("desc_id", ""))

    related_avatars = [avatar.id]
    target_info = ""
    target_avatar = None

    if participants == 2:
        radius = get_avatar_observation_radius(avatar)
        
        candidates = []
        for other in world.avatar_manager.get_living_avatars():
            if other.id == avatar.id:
                continue
            
            dist = abs(other.pos_x - avatar.pos_x) + abs(other.pos_y - avatar.pos_y)
            if dist <= radius:
                candidates.append(other)
        
        target_avatar = None
        if candidates:
            target_avatar = random.choice(candidates)
            related_avatars.append(target_avatar.id)
            import json
            target_info = json.dumps(target_avatar.get_info(detailed=True), ensure_ascii=False)
        else:
            # Fallback to anonymous extra
            target_info = t("An anonymous passerby (extra)")

    location_name = avatar.tile.region.name if avatar.tile and avatar.tile.region else t("unknown location")

    import json
    # Avatar info
    if participants == 2 and target_avatar is not None:
        avatar_dict = avatar.get_expanded_info(other_avatar=target_avatar, detailed=True)
    else:
        avatar_dict = avatar.get_expanded_info(detailed=True)
    
    avatar_info = json.dumps(avatar_dict, ensure_ascii=False)

    # World info
    # Gather active celestial phenomenon if any
    world_info = ""
    if world.current_phenomenon:
        world_info = t("Current world celestial phenomenon: {name}", name=world.current_phenomenon.name)

    # LLM request
    infos = {
        "avatar_info": avatar_info,
        "location": location_name,
        "world_info": world_info,
        "cause": t(desc),
        "target_info": target_info
    }

    try:
        result = await call_llm_with_task_name(
            task_name="random_minor_event",
            template_path=CONFIG.paths.templates / "random_minor_event.txt",
            infos=infos
        )
        event_text = result.get("event_text", "").strip()
    except Exception as e:
        get_logger().logger.error(f"Failed to generate random minor event for {avatar.name}: {e}")
        return None

    if not event_text:
        return None
        
    return Event(world.month_stamp, event_text, related_avatars=related_avatars, is_major=False, is_story=False)
