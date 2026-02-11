from typing import Dict, List, Optional
import random
from src.classes.core.avatar import Avatar
from src.classes.core.world import World
from src.systems.time import MonthStamp
from src.classes.relation.relation import Relation
from src.sim.avatar_init import create_avatar_from_request
from src.utils.df import game_configs, get_int, get_str, get_list_int

# ==========================================
# 2. 执行生成与关系绑定逻辑
# ==========================================

def spawn_protagonists(
    world: World, 
    current_month_stamp: MonthStamp, 
    probability: float = 1.0
) -> Dict[str, Avatar]:
    """
    遍历配置生成角色，并处理特殊关系。
    :param probability: 每个角色生成的概率 (0.0 - 1.0)。
    """
    created_avatars = {}
    
    # 1. 批量生成
    # 从全局配置中读取 protagonist.csv 加载的数据
    configs = game_configs.get("protagonist", [])

    for config in configs:
        # 概率判定
        if probability < 1.0 and random.random() > probability:
            continue
            
        try:
            key = get_str(config, "key")
            
            # 使用 get_* 辅助函数安全获取数据
            # 注意：name 会由 df.py 自动处理 name_id -> name 的翻译
            avatar = create_avatar_from_request(
                world=world,
                current_month_stamp=current_month_stamp,
                name=get_str(config, "name"),
                gender=get_str(config, "gender"),
                age=get_int(config, "age"),
                level=get_int(config, "level"),
                sect=get_int(config, "sect_id"),
                technique=get_int(config, "technique_id"),
                weapon=get_int(config, "weapon_id"),
                auxiliary=get_int(config, "auxiliary_id"),
                personas=get_list_int(config, "personas"),
                appearance=get_int(config, "appearance"),
            )
            created_avatars[key] = avatar
        except Exception:
            pass # 忽略生成错误，避免中断

    # 2. 绑定关系
    # 注意：需要确保双方都已生成
    for config in configs:
        src_key = get_str(config, "key")
        if src_key not in created_avatars:
            continue
            
        src_avatar = created_avatars[src_key]
        relations_str = get_str(config, "relations")
        
        if not relations_str:
            continue
            
        # 解析关系字符串: "key1:type1;key2:type2"
        for rel_item in relations_str.split(";"):
            if ":" not in rel_item: 
                continue
                
            target_key, rel_type = rel_item.split(":")
            target_key = target_key.strip()
            rel_type = rel_type.strip()
            
            if target_key in created_avatars:
                target_avatar = created_avatars[target_key]
                
                # 应用关系
                if rel_type == "friend":
                    src_avatar.make_friend_with(target_avatar)
                elif rel_type == "lover":
                    src_avatar.become_lovers_with(target_avatar)
                elif rel_type == "enemy":
                    src_avatar.make_enemy_of(target_avatar)
                elif rel_type == "child":
                    # src 认 target 为子女
                    src_avatar.acknowledge_child(target_avatar)

    # 返回 ID -> Avatar 字典，方便合并
    return {av.id: av for av in created_avatars.values()}
