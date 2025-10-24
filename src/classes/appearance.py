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
        return f"{self.name}({self.level})"

    def get_detailed_info(self, gender: object | None = None) -> str:
        """
        根据性别返回更贴切的描述；若未提供性别或无法识别，则默认使用男性描述。
        不依赖具体 Gender 类型，避免循环导入。
        """
        g = str(gender) if gender is not None else ""
        s = g.lower()
        use_female = (g == "女") or (s == "female")
        desc = self.desc_female if use_female else self.desc_male
        return f"{self.name}({self.level}) - {desc}"


_LEVEL_DATA: Tuple[Tuple[int, str, str, str], ...] = (
    # level, name, desc_male, desc_female
    (1, "奇丑", "你长得很丑，五官不协调，常被人躲着走。", "你长得很丑，五官不协调，旁人多会躲开。"),
    (2, "丑陋", "你五官粗糙，鼻梁塌，下巴有点外凸。", "你五官粗糙，颧骨偏高，嘴唇线条乱。"),
    (3, "粗陋", "你相貌粗陋，看久也不太顺眼。", "你相貌粗陋，神情略显刻薄。"),
    (4, "寒素", "你长相普通，眉目淡，穿着朴素，不显眼。", "你长相普通，气色淡，打扮简单，不出挑。"),
    (5, "清秀", "你眉眼清秀，看着顺眼。", "你眉眼清秀，挺耐看。"),
    (6, "秀致", "你五官精致，气质端正。", "你五官精致，气质温雅。"),
    (7, "俊美", "你长得很俊，回头率很高。", "你长得很美，很抢眼。"),
    (8, "倾城", "你外形出众，走到哪都很惹眼。", "你漂亮到让人惊艳。"), 
    (9, "绝色", "你长相和气质都很顶，常引人侧目。", "你美得很惊人，几乎一眼难忘。"),
    (10, "惊艳", "你漂亮得像不食人间烟火。", "你美到让人惊艳，一眼就记住你。"),
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


