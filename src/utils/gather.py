from __future__ import annotations
import random
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar

def check_can_start_gather(
    avatar: Avatar,
    resource_attr: str,  # "lodes", "animals", "plants"
    resource_name_cn: str  # "矿脉", "动物", "植物"
) -> tuple[bool, str]:
    from src.classes.environment.region import NormalRegion
    
    region = avatar.tile.region
    if not isinstance(region, NormalRegion):
        return False, "当前不在普通区域"
        
    resources = getattr(region, resource_attr, [])
    if not resources:
        return False, f"当前区域没有{resource_name_cn}"
        
    # 筛选境界符合的资源
    available = [
        r for r in resources
        if avatar.cultivation_progress.realm >= r.realm
    ]
    if not available:
        return False, f"当前区域的{resource_name_cn}境界过高"
        
    return True, ""

def execute_gather(
    avatar: Avatar,
    resource_attr: str,
    extra_effect_key: str
) -> dict[str, int]:
    """
    执行采集逻辑。
    返回: {material_name: count}
    """
    from src.classes.environment.region import NormalRegion
    region = avatar.tile.region
    
    # 再次校验类型，防止运行时环境变化
    if not isinstance(region, NormalRegion):
        return {}

    resources = getattr(region, resource_attr, [])
    
    # 筛选
    available = [
        r for r in resources
        if avatar.cultivation_progress.realm >= r.realm
    ]
    
    if not available:
        return {}
        
    # 1. 随机选择资源点 (均匀分布)
    target = random.choice(available)
    
    # 2. 随机选择产出物
    if not hasattr(target, "materials") or not target.materials:
        return {}
        
    material = random.choice(target.materials)
    
    base_quantity = 1
    extra_materials = int(avatar.effects.get(extra_effect_key, 0) or 0)
    total_quantity = base_quantity + extra_materials
    
    avatar.add_material(material, total_quantity)
    
    return {material.name: total_quantity}

