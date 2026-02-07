from __future__ import annotations

from typing import Iterable, List, TYPE_CHECKING

from src.systems.cultivation import Realm
from src.classes.environment.tile import get_avatar_distance

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


_OBSERVATION_RADIUS_BY_REALM: dict[Realm, int] = {
    Realm.Qi_Refinement: 2,            # 练气
    Realm.Foundation_Establishment: 3, # 筑基
    Realm.Core_Formation: 4,           # 金丹
    Realm.Nascent_Soul: 5,             # 元婴
}


def get_observation_radius_by_realm(realm: Realm) -> int:
    """
    根据境界返回感知半径（基于曼哈顿距离）。
    """
    return _OBSERVATION_RADIUS_BY_REALM.get(realm, 2)


def get_avatar_observation_radius(avatar: "Avatar") -> int:
    """
    获取角色的感知半径。
    """
    base = get_observation_radius_by_realm(avatar.cultivation_progress.realm)
    extra_raw = avatar.effects.get("extra_observation_radius", 0)
    extra = int(extra_raw or 0)
    return max(1, base + extra)


def is_within_observation(initiator: "Avatar", other: "Avatar") -> bool:
    """
    判断 other 是否处于 initiator 的交互范围内：
    汉明距离(曼哈顿距离) <= initiator 的感知半径。
    """
    return get_avatar_distance(initiator, other) <= get_avatar_observation_radius(initiator)


def get_observable_avatars(initiator: "Avatar", avatars: Iterable["Avatar"]) -> List["Avatar"]:
    """
    从给定集合中过滤出处于 initiator 交互范围内的角色（不包含 initiator 本人）。
    算法：线性扫描 O(N)，与现有管理器遍历复杂度一致。
    """
    result: list["Avatar"] = []
    for v in avatars:
        if v is initiator:
            continue
        if is_within_observation(initiator, v):
            result.append(v)
    return result


