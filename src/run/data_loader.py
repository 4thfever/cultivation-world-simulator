from src.classes.core.sect import reload as reload_sects, sects_by_id
from src.classes.technique import reload as reload_techniques, techniques_by_id
from src.classes.items.weapon import reload as reload_weapons, weapons_by_id
from src.classes.items.auxiliary import reload as reload_auxiliaries, auxiliaries_by_id
from src.classes.persona import reload as reload_personas, personas_by_id
from src.classes.celestial_phenomenon import reload as reload_phenomena, celestial_phenomena_by_id
from src.utils.name_generator import reload as reload_names
from src.classes.animal import reload as reload_animals
from src.classes.environment.plant import reload as reload_plants
from src.classes.material import reload as reload_materials
from src.classes.environment.lode import reload as reload_lodes
from src.classes.items.elixir import reload as reload_elixirs
from src.classes.items.registry import ItemRegistry
from src.run.log import get_logger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.classes.core.world import World

def reload_all_static_data():
    """
    重置所有游戏静态数据到初始状态。
    必须在每次 init_game 之前调用。
    """
    logger = get_logger().logger
    logger.info("[DataLoader] 开始重置静态游戏数据...")
    
    # 1. 清空物品注册表
    ItemRegistry.reset()
    
    # 2. 重新加载各模块数据
    # 注意顺序：有些模块可能依赖其他模块（如功法可能依赖宗门ID，虽通常只有弱引用）
    reload_sects()
    reload_techniques()
    reload_weapons() 
    reload_auxiliaries()
    reload_personas()
    reload_phenomena()
    reload_names()
    reload_animals()
    reload_plants()
    reload_materials()
    reload_lodes()
    reload_elixirs()
    
    logger.info("[DataLoader] 静态数据重置完成，环境已净化。")

def fix_runtime_references(world: "World"):
    """
    修复运行时对象的引用（在热重载后调用）。
    主要解决：
    1. Avatar.sect 指向旧对象，导致新加载的 Sect.members 为空。
    2. Avatar.technique/weapon/persona 等指向旧对象。
    3. 重建宗门成员关系。
    """
    if not world or not world.avatar_manager:
        return

    logger = get_logger().logger
    logger.info("[DataLoader] 开始修复运行时引用...")
    
    # 收集所有角色（活人 + 死者）
    # 注意：dead_avatars 可能是 dict 或 list，根据 avatar_manager 实现
    # 查看 main.py 中 world.avatar_manager.avatars.values()，应该是 dict
    all_avatars = list(world.avatar_manager.avatars.values())
    if hasattr(world.avatar_manager, "dead_avatars"):
        all_avatars.extend(list(world.avatar_manager.dead_avatars.values()))
    
    count = 0
    fixed_sects = set()
    
    for avatar in all_avatars:
        count += 1
        
        # 1. 修复宗门引用并重建成员关系
        if avatar.sect:
            # 尝试从新加载的字典中获取同 ID 的新对象
            new_sect = sects_by_id.get(avatar.sect.id)
            if new_sect:
                # 更新引用
                avatar.sect = new_sect
                # 重新加入成员列表（Sect.add_member 会处理去重）
                new_sect.add_member(avatar)
                fixed_sects.add(new_sect.name)
            else:
                logger.warning(f"Avatar {avatar.name} 引用了不存在的宗门 ID: {avatar.sect.id}")
                # 如果找不到新宗门，可能需要置空，或者保持旧引用（但会由旧引用导致Bug）
                # 这里选择保留旧引用，以免破坏数据，但记录警告
                
        # 2. 修复功法引用
        if avatar.technique:
            new_tech = techniques_by_id.get(avatar.technique.id)
            if new_tech:
                avatar.technique = new_tech
                
        # 3. 修复武器引用
        if avatar.weapon:
            new_weapon = weapons_by_id.get(avatar.weapon.id)
            if new_weapon:
                avatar.weapon = new_weapon
                 
        # 4. 修复辅助法宝引用
        if avatar.auxiliary:
            new_aux = auxiliaries_by_id.get(avatar.auxiliary.id)
            if new_aux:
                avatar.auxiliary = new_aux
                
        # 5. 修复性格引用 (列表)
        if avatar.personas:
            new_personas = []
            for p in avatar.personas:
                new_p = personas_by_id.get(p.id)
                if new_p:
                    new_personas.append(new_p)
                else:
                    new_personas.append(p) # Fallback
            avatar.personas = new_personas

    # 6. 修复天地灵机引用
    if hasattr(world, "current_phenomenon") and world.current_phenomenon:
        new_p = celestial_phenomena_by_id.get(world.current_phenomenon.id)
        if new_p:
            world.current_phenomenon = new_p

    logger.info(f"[DataLoader] 已修复 {count} 个角色的引用关系，涉及宗门: {list(fixed_sects)}。")
