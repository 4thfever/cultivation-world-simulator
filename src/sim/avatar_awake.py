import random
from typing import List, Optional

from src.classes.core.world import World
from src.classes.core.avatar import Avatar, Gender
from src.classes.mortal import Mortal
from src.systems.time import MonthStamp
from src.systems.cultivation import CultivationProgress, Realm
from src.classes.age import Age
from src.classes.relation.relation import Relation
from src.classes.root import Root
from src.classes.items.magic_stone import MagicStone
from src.classes.event import Event
from src.utils.id_generator import get_avatar_id
from src.classes.technique import attribute_to_root
from src.classes.items.weapon import get_random_weapon_by_realm
from src.utils.config import CONFIG
from src.utils.born_region import get_born_region_id
from src.i18n import t

# 常量
MIN_AWAKENING_AGE = 16
MAX_AWAKENING_AGE = 60 # 凡人觉醒的最大年龄
BLOODLINE_AWAKENING_RATE = 0.05 # 每个符合条件的凡人每月的觉醒概率
WILD_AWAKENING_RATE_BASE = 0.1 # 基础野生觉醒率 (如果没有配置)

def process_awakening(world: World) -> List[Event]:
    events = []
    
    # 1. 血脉觉醒 (Existing Mortals)
    events.extend(_process_bloodline_awakening(world))
    
    # 2. 机缘觉醒 (Wild Avatars)
    # 读取配置中的觉醒率
    wild_rate = getattr(CONFIG.game, "npc_awakening_rate_per_month", WILD_AWAKENING_RATE_BASE)
    
    if random.random() < wild_rate:
        wild_event = _process_wild_awakening(world)
        if wild_event:
            events.append(wild_event)
            
    return events

def _process_bloodline_awakening(world: World) -> List[Event]:
    events = []
    # 获取候选人
    candidates = world.mortal_manager.get_awakening_candidates(world.month_stamp, min_age=MIN_AWAKENING_AGE)
    
    for mortal in candidates:
        # 年龄超过上限则不再觉醒（只能等死）
        current_age_years = (int(world.month_stamp) - int(mortal.birth_month_stamp)) // 12
        if current_age_years > MAX_AWAKENING_AGE:
            continue
            
        # 判定是否觉醒
        if random.random() < BLOODLINE_AWAKENING_RATE:
            avatar = _promote_mortal_to_avatar(world, mortal)
            
            # 注册 Avatar
            world.avatar_manager.register_avatar(avatar, is_newly_born=True)
            
            # 移除 Mortal
            world.mortal_manager.remove_mortal(mortal.id)
            
            # 生成事件
            desc = t("{name} has awakened their spiritual roots and embarked on the path of cultivation.", name=avatar.name)
            event = Event(world.month_stamp, desc, related_avatars=[avatar.id])
            events.append(event)
            
    return events

def _process_wild_awakening(world: World) -> Optional[Event]:
    # 随机生成一个新的野生角色
    gender = random.choice(list(Gender))
    from src.utils.name_generator import get_random_name
    name = get_random_name(gender)
    
    age_val = random.randint(MIN_AWAKENING_AGE, 30)
    
    # 构造 Avatar
    born_id = get_born_region_id(world)
    avatar = _create_simple_avatar(world, name, gender, age_val, parents=[], born_region_id=born_id)
    
    # 注册
    world.avatar_manager.register_avatar(avatar, is_newly_born=True)
    
    desc = t("A rogue cultivator {name} has appeared in the world.", name=avatar.name)
    event = Event(world.month_stamp, desc, related_avatars=[avatar.id])
    return event

def _promote_mortal_to_avatar(world: World, mortal: Mortal) -> Avatar:
    # 计算当前年龄
    age_years = (int(world.month_stamp) - int(mortal.birth_month_stamp)) // 12
    
    avatar = _create_simple_avatar(
        world, 
        mortal.name, 
        mortal.gender, 
        age_years, 
        parents=mortal.parents,
        mortal_id=mortal.id, # 复用 ID
        born_region_id=mortal.born_region_id
    )
    
    return avatar

def _create_simple_avatar(
    world: World, 
    name: str, 
    gender: Gender, 
    age_years: int, 
    parents: List[str],
    mortal_id: Optional[str] = None,
    born_region_id: Optional[int] = None
) -> Avatar:
    # 1. 基础属性
    level = 1
    cultivation = CultivationProgress(level)
    age = Age(age_years, cultivation.realm)
    
    # 复用 ID 或生成新 ID
    aid = mortal_id if mortal_id else get_avatar_id()
    
    # 出生位置随机
    x = random.randint(0, world.map.width - 1)
    y = random.randint(0, world.map.height - 1)
    
    birth_stamp = world.month_stamp - age_years * 12
    
    avatar = Avatar(
        world=world,
        name=name,
        id=aid,
        birth_month_stamp=MonthStamp(int(birth_stamp)),
        age=age,
        gender=gender,
        cultivation_progress=cultivation,
        pos_x=x,
        pos_y=y,
        root=random.choice(list(Root)),
        sect=None, # 刚觉醒默认为散修
        born_region_id=born_region_id
    )
    
    avatar.magic_stone = MagicStone(10) # 少量灵石
    avatar.tile = world.map.get_tile(x, y)
    
    # 2. 装备与功法 (简化配置)
    # 武器：一把练气期武器
    avatar.weapon = get_random_weapon_by_realm(avatar.cultivation_progress.realm)
    # 辅助：无
    avatar.auxiliary = None
    
    # 功法：暂无
    # 凡人觉醒初期只有灵根，还未习得功法，或者设定为有一本基础的
    # avatar.technique = ...
    
    # 3. 关系绑定
    for pid in parents:
        parent = world.avatar_manager.get_avatar(pid)
        if parent:
            # 建立关系 (Parent -> Child)
            # 语义：Parent 认 Avatar 为子
            parent.acknowledge_child(avatar)
            
    return avatar
