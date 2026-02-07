"""
宗门等级系统
定义宗门内的职位等级及其与修仙境界的映射关系
"""
from enum import Enum
from functools import total_ordering
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.systems.cultivation import Realm
    from src.classes.core.sect import Sect


@total_ordering
class SectRank(Enum):
    """
    宗门职位等级
    从高到低：掌门 > 长老 > 内门弟子 > 外门弟子
    """
    Patriarch = "patriarch"      # 掌门
    Elder = "elder"              # 长老
    InnerDisciple = "inner"      # 内门弟子
    OuterDisciple = "outer"      # 外门弟子
    
    def __str__(self) -> str:
        from src.i18n import t
        return t(sect_rank_msg_ids.get(self, self.value))
    
    def __lt__(self, other):
        if not isinstance(other, SectRank):
            return NotImplemented
        # 数字越小职位越高，所以比较时反过来
        return RANK_ORDER[self] > RANK_ORDER[other]
    
    def __le__(self, other):
        if not isinstance(other, SectRank):
            return NotImplemented
        return RANK_ORDER[self] >= RANK_ORDER[other]
    
    def __gt__(self, other):
        if not isinstance(other, SectRank):
            return NotImplemented
        # 数字越小职位越高，所以比较时反过来
        return RANK_ORDER[self] < RANK_ORDER[other]
    
    def __ge__(self, other):
        if not isinstance(other, SectRank):
            return NotImplemented
        return RANK_ORDER[self] <= RANK_ORDER[other]


# 宗门职位顺序（数字越小职位越高）
RANK_ORDER = {
    SectRank.Patriarch: 0,
    SectRank.Elder: 1,
    SectRank.InnerDisciple: 2,
    SectRank.OuterDisciple: 3,
}

# msgid映射
sect_rank_msg_ids = {
    SectRank.Patriarch: "patriarch",
    SectRank.Elder: "elder",
    SectRank.InnerDisciple: "inner_disciple",
    SectRank.OuterDisciple: "outer_disciple",
}

# 默认职位名称（可被宗门自定义覆盖）
DEFAULT_RANK_NAMES = {
    SectRank.Patriarch: "patriarch",
    SectRank.Elder: "elder",
    SectRank.InnerDisciple: "inner_disciple",
    SectRank.OuterDisciple: "outer_disciple",
}


def get_rank_from_realm(realm: "Realm") -> SectRank:
    """
    根据修仙境界映射为宗门职位
    
    映射规则：
    - 练气 → 外门弟子
    - 筑基 → 内门弟子
    - 金丹 → 长老
    - 元婴 → 掌门（需要额外检查唯一性）
    
    Args:
        realm: 修仙境界
        
    Returns:
        对应的宗门职位
    """
    from src.systems.cultivation import Realm
    
    mapping = {
        Realm.Qi_Refinement: SectRank.OuterDisciple,
        Realm.Foundation_Establishment: SectRank.InnerDisciple,
        Realm.Core_Formation: SectRank.Elder,
        Realm.Nascent_Soul: SectRank.Patriarch,
    }
    return mapping.get(realm, SectRank.OuterDisciple)


def get_rank_display_name(rank: SectRank, sect: Optional["Sect"] = None) -> str:
    """
    获取职位的显示名称（支持宗门自定义）
    
    Args:
        rank: 宗门职位
        sect: 宗门对象（可选，如果提供则使用其自定义名称）
        
    Returns:
        职位的显示名称
    """
    from src.i18n import t
    if sect is not None:
        custom_name = sect.get_rank_name(rank)
        if custom_name:
            return custom_name
    val = DEFAULT_RANK_NAMES.get(rank, "弟子")
    return t(val)


def should_auto_promote(old_realm: "Realm", new_realm: "Realm") -> bool:
    """
    判断境界突破后是否应该自动晋升宗门职位
    
    Args:
        old_realm: 旧境界
        new_realm: 新境界
        
    Returns:
        是否应该晋升
    """
    if old_realm == new_realm:
        return False
    
    from src.systems.cultivation import Realm
    
    # 检查境界是否提升
    old_rank = get_rank_from_realm(old_realm)
    new_rank = get_rank_from_realm(new_realm)
    
    # 只有当新境界对应的职位更高时才晋升（职位枚举中 > 表示更高）
    return new_rank > old_rank


def check_and_promote_sect_rank(avatar: "Avatar", old_realm: "Realm", new_realm: "Realm") -> None:
    """
    检查境界突破后是否需要晋升宗门职位，并执行晋升
    
    Args:
        avatar: 要检查的角色
        old_realm: 旧境界
        new_realm: 新境界
    """
    # 无宗门或无职位，不需要晋升
    if avatar.sect is None or avatar.sect_rank is None:
        return
    
    # 检查是否应该晋升
    if not should_auto_promote(old_realm, new_realm):
        return
    
    new_rank = get_rank_from_realm(new_realm)
    
    # 如果新职位是掌门，需要检查该宗门是否已有掌门
    if new_rank == SectRank.Patriarch:
        if sect_has_patriarch(avatar):
            # 已有掌门，只能晋升为长老
            new_rank = SectRank.Elder
    
    # 执行晋升
    avatar.sect_rank = new_rank


def sect_has_patriarch(avatar: "Avatar") -> bool:
    """
    检查当前宗门是否已有掌门（不包括自己）
    
    Args:
        avatar: 要检查的角色
        
    Returns:
        是否已有其他掌门
    """
    if avatar.sect is None:
        return False
    
    # 从world中查找同宗门的其他avatar
    for other in avatar.world.avatar_manager.avatars.values():
        if other is avatar:
            continue
        if other.sect == avatar.sect and other.sect_rank == SectRank.Patriarch:
            return True
    
    return False

