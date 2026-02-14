import random
from src.classes.core.world import World
from src.classes.core.avatar import Avatar, Gender
from src.classes.relation.relation import Relation
from src.classes.mortal import Mortal
from src.classes.event import Event
from src.utils.config import CONFIG
from src.utils.name_generator import get_random_name_with_surname
from src.utils.id_generator import get_avatar_id
from src.utils.born_region import get_born_region_id
from src.i18n import t

def process_births(world: World) -> list[Event]:
    """
    处理世界中的生育逻辑。
    遍历所有存活角色，检查符合条件的道侣并尝试生成子女。
    
    Returns:
        生成的事件列表
    """
    events = []
    
    birth_rate = CONFIG.game.birth_rate_per_month
    max_children = CONFIG.game.max_children_per_couple
    current_time = int(world.month_stamp)
    processed_couples = set()

    living_avatars = world.avatar_manager.get_living_avatars()

    for avatar in living_avatars:
        # 1. 寻找道侣
        partner: Avatar | None = None
        for target, rel in avatar.relations.items():
            if rel == Relation.IS_LOVER_OF:
                partner = target
                break
        
        if not partner:
            continue
            
        if partner.is_dead:
            continue
        
        # 2. 去重 (只处理一次 A-B)
        # 使用ID排序确保唯一性
        id1, id2 = sorted([str(avatar.id), str(partner.id)])
        couple_id = (id1, id2)
        
        if couple_id in processed_couples:
            continue
        processed_couples.add(couple_id)
        
        # 3. 检查时间 (关系需持续 > 12 个月)
        start_time = avatar.relation_start_dates.get(partner.id, 0)
        if partner.id not in avatar.relation_start_dates:
             # 补录时间为当前时间，避免每帧都检查
             avatar.relation_start_dates[partner.id] = current_time
             partner.relation_start_dates[avatar.id] = current_time
             start_time = current_time

        if current_time - start_time <= 12:
            continue
        
        # 4. 检查数量限制 (任一方达到上限即停止)
        if len(avatar.children) >= max_children or len(partner.children) >= max_children:
            continue
            
        # 5. 概率判定
        if random.random() < birth_rate:
            event = _create_child_for_couple(world, avatar, partner)
            if event:
                events.append(event)

    return events

def _create_child_for_couple(world: World, parent1: Avatar, parent2: Avatar) -> Event:
    """
    为一对伴侣创建子女
    """
    # 1. 确定父系 (用于姓氏)
    # 优先取男性为父，若同性则随机或取 parent1
    father = parent1 if parent1.gender == Gender.MALE else (parent2 if parent2.gender == Gender.MALE else parent1)
    
    # 2. 生成基础信息
    child_gender = random.choice(list(Gender))
    
    # 获取父姓
    father_surname = father.name[0] # 简单取首字
    
    # 使用公共API生成名字
    child_name = get_random_name_with_surname(child_gender, father_surname, sect=None)
    
    # 3. 创建对象
    child = Mortal(
        id=get_avatar_id(),
        name=child_name,
        gender=child_gender,
        birth_month_stamp=world.month_stamp,
        parents=[str(parent1.id), str(parent2.id)],
        born_region_id=get_born_region_id(world, parents=[parent1, parent2])
    )
    
    # 4. 绑定关系
    parent1.children.append(child)
    parent2.children.append(child)
    
    # 5. 注册到世界凡人管理器
    world.mortal_manager.register_mortal(child)
    
    # 6. 生成事件文本
    # key: "{p1} and {p2} gave birth to a {gender} named {child}."
    gender_str_key = "son" if child_gender == Gender.MALE else "daughter"
    gender_str = t(gender_str_key)
    
    event_desc = t(
        "{p1} and {p2} gave birth to a {gender} named {child}.", 
        p1=parent1.name, 
        p2=parent2.name, 
        gender=gender_str, 
        child=child.name
    )
    
    event = Event(
        world.month_stamp,
        event_desc,
        related_avatars=[parent1.id, parent2.id]
    )
    
    return event
