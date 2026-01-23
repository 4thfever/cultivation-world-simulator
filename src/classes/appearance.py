from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Tuple


@dataclass
class Appearance:
    """
    外貌/颜值
    """
    level: int  # 1~10
    name: str
    desc_male: str
    desc_female: str

    def get_info(self) -> str:
        from src.i18n import t
        return f"{t(self.name)}({self.level})"

    def get_detailed_info(self, gender: object | None = None) -> str:
        """
        根据性别返回更贴切的描述；若未提供性别或无法识别，则默认使用男性描述。
        不依赖具体 Gender 类型，避免循环导入。
        """
        from src.i18n import t
        g = str(gender) if gender is not None else ""
        s = g.lower()
        use_female = (g == "女") or (s == "female")
        desc = self.desc_female if use_female else self.desc_male
        return f"{t(self.name)}({self.level}) - {t(desc)}"


_LEVEL_DATA: Tuple[Tuple[int, str, str, str], ...] = (
    # level, name, desc_male, desc_female
    (1, "appearance_1_name", "appearance_1_desc_male", "appearance_1_desc_female"),
    (2, "appearance_2_name", "appearance_2_desc_male", "appearance_2_desc_female"),
    (3, "appearance_3_name", "appearance_3_desc_male", "appearance_3_desc_female"),
    (4, "appearance_4_name", "appearance_4_desc_male", "appearance_4_desc_female"),
    (5, "appearance_5_name", "appearance_5_desc_male", "appearance_5_desc_female"),
    (6, "appearance_6_name", "appearance_6_desc_male", "appearance_6_desc_female"),
    (7, "appearance_7_name", "appearance_7_desc_male", "appearance_7_desc_female"),
    (8, "appearance_8_name", "appearance_8_desc_male", "appearance_8_desc_female"), 
    (9, "appearance_9_name", "appearance_9_desc_male", "appearance_9_desc_female"),
    (10, "appearance_10_name", "appearance_10_desc_male", "appearance_10_desc_female"),
)


def _build_pool(data: Iterable[Tuple[int, str, str, str]]) -> List[Appearance]:
    pool: List[Appearance] = []
    for level, name, dm, df in data:
        pool.append(Appearance(level=level, name=name, desc_male=dm, desc_female=df))
    return pool


_APPEARANCE_POOL: List[Appearance] = _build_pool(_LEVEL_DATA)


def get_random_appearance() -> Appearance:
    """返回一个随机外貌实例。"""
    # 重新构造实例，避免共享同一个对象引用
    base = random.choice(_APPEARANCE_POOL)
    return Appearance(level=base.level, name=base.name, desc_male=base.desc_male, desc_female=base.desc_female)


def get_appearance_by_level(level: int) -> Appearance:
    """
    按等级(1~10)返回外貌实例；越界时夹在范围内。
    返回新实例，避免外部持有池中引用。
    """
    lv = int(level)
    if lv < 1:
        lv = 1
    if lv > 10:
        lv = 10
    base = next((a for a in _APPEARANCE_POOL if a.level == lv), _APPEARANCE_POOL[-1])
    return Appearance(level=base.level, name=base.name, desc_male=base.desc_male, desc_female=base.desc_female)


__all__ = [
    "Appearance",
    "get_random_appearance",
    "get_appearance_by_level",
]


