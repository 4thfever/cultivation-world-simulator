from __future__ import annotations
from typing import Any, Type, Optional, List, Union
from dataclasses import dataclass

from src.utils.normalize import normalize_goods_name, normalize_name, normalize_avatar_name
from src.classes.items.elixir import elixirs_by_name, Elixir
from src.classes.items.weapon import weapons_by_name, Weapon
from src.classes.items.auxiliary import auxiliaries_by_name, Auxiliary
from src.classes.material import materials_by_name, Material
from src.systems.cultivation import Realm

@dataclass
class ResolutionResult:
    """解析结果封装"""
    obj: Any | None              # 解析出的对象实例
    resolved_type: Type | None   # 对象的类型类
    is_valid: bool               # 是否成功
    error_msg: str = ""          # 错误信息
    
    @property
    def name(self) -> str:
        """尝试获取对象的名称"""
        if self.obj and hasattr(self.obj, "name"):
            return self.obj.name
        return ""

def resolve_query(
    query: Any, 
    world: Any = None, 
    expected_types: Optional[list[Type]] = None
) -> ResolutionResult:
    """
    统一解析入口。
    
    Args:
        query: 待解析的对象（字符串名 或 直接的对象实例）
        world: 世界对象上下文（用于查找 Avatar, Region）
        expected_types: 期望的类型列表。如果提供，将优先或仅尝试这些类型。
                        支持的类型: Material, Weapon, Elixir, Auxiliary, Region, Avatar, Realm 等类对象
                        必须直接传入类对象，不再支持字符串名。
    """
    if query is None:
        return ResolutionResult(None, None, False, "查询为空")

    # 0. 快速通道：如果已经是期望的对象实例
    if expected_types:
        for t in expected_types:
            if isinstance(query, t):
                return _success(query, t)
    
    # 如果不是字符串，且未命中上面的快速通道，可能输入了错误的对象
    # 严格模式：既然未命中 expected_types 中的任何类型，也必然无法通过下面的字符串查找逻辑。
    # 直接返回失败，除非 query 是字符串可以尝试查找。
    if not isinstance(query, str):
        return ResolutionResult(None, None, False, f"输入类型不支持且非字符串: {type(query)}")

    if not query:
        return ResolutionResult(None, None, False, "查询字符串为空")

    # 准备检查列表
    checks = []
    
    # 如果没有指定期望类型，则检查所有
    if not expected_types:
        checks = ["realm", "goods", "region", "avatar"]
    else:
        # 根据期望类型构建检查顺序
        for t in expected_types:
            # 必须是类对象
            if not isinstance(t, type):
                 # 这里可以抛出异常，或者忽略。既然是重构，假设调用方已经修正。
                 continue

            t_name = t.__name__
            
            if t_name in ["Material", "Weapon", "Elixir", "Auxiliary"]:
                if "goods" not in checks: checks.append("goods")
            elif t_name == "Region" or t_name == "CityRegion" or t_name == "SectRegion" or t_name == "CultivateRegion":
                if "region" not in checks: checks.append("region")
            elif t_name == "Avatar":
                if "avatar" not in checks: checks.append("avatar")
            elif t_name == "Realm":
                if "realm" not in checks: checks.append("realm")

    # 执行检查
    for check in checks:
        if check == "realm":
            res = _resolve_realm(query) # Realm 通常不需要 normalize 太多，或者在内部处理
            if res: return _success(res, Realm)
            
        elif check == "goods":
            # 物品解析
            obj = _resolve_goods(query)
            if obj: return _success(obj, type(obj))
            
        elif check == "region" and world:
            obj = _resolve_region(query, world)
            if obj: return _success(obj, type(obj))
            
        elif check == "avatar" and world:
            obj = _resolve_avatar(query, world)
            if obj: return _success(obj, type(obj))

    return ResolutionResult(None, None, False, f"无法解析: {query}")

def _success(obj: Any, type_cls: Type) -> ResolutionResult:
    return ResolutionResult(obj, type_cls, True)

# --- 内部具体的解析逻辑 ---

def _resolve_goods(name: str) -> Any | None:
    """解析物品/装备/丹药"""
    norm = normalize_goods_name(name)
    
    # 1. 丹药 (返回列表中的第一个)
    if norm in elixirs_by_name:
        return elixirs_by_name[norm][0]
        
    # 2. 兵器
    if norm in weapons_by_name:
        return weapons_by_name[norm]
        
    # 3. 辅助
    if norm in auxiliaries_by_name:
        return auxiliaries_by_name[norm]
        
    # 4. 材料
    if norm in materials_by_name:
        return materials_by_name[norm]
        
    return None

def _resolve_realm(name: str) -> Realm | None:
    """解析境界"""
    try:
        # 尝试直接匹配值
        return Realm(name)
    except ValueError:
        pass
    
    # 尝试匹配枚举名
    for r in Realm:
        if r.name == name or r.value == name:
            return r
    return None

def _resolve_region(name: str, world: Any) -> Any | None:
    """解析区域 - 遍历 regions.values() 查找，避免维护额外的 name 索引"""
    if not hasattr(world, 'map'):
        return None
    
    regions = getattr(world.map, "regions", {})
    if not regions:
        return None
    
    norm = normalize_name(name)
    
    # 1. 精确匹配 / 规范化匹配
    for region in regions.values():
        if region.name == name or region.name == norm:
            return region
    
    # 2. 包含匹配 (如果有唯一解)
    candidates = [r for r in regions.values() if (norm in r.name) or (name in r.name)]
    if len(candidates) == 1:
        return candidates[0]
        
    # 3. 宗门名称匹配 (解析到宗门驻地)
    from src.classes.core.sect import sects_by_name
    sect = sects_by_name.get(name) or sects_by_name.get(norm)
    if sect:
        sect_regions = getattr(world.map, "sect_regions", {})
        matched = [r for r in sect_regions.values() if getattr(r, "sect_name", None) == sect.name]
        if len(matched) == 1:
            return matched[0]
            
    return None

def _resolve_avatar(name: str, world: Any) -> Any | None:
    """解析角色"""
    if not hasattr(world, 'avatar_manager'):
        return None
        
    norm = normalize_avatar_name(name)
    
    # 遍历查找 (性能注意：如果角色极多可能需要优化为字典查找)
    # 假设 avatar_manager.avatars 是 dict[id, Avatar]
    for avatar in world.avatar_manager.avatars.values():
        if avatar.name == norm:
            return avatar
            
    return None
