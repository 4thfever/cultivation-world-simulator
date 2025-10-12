from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Tuple


@dataclass
class Appearance:
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
    (1, "奇丑", "你相貌奇丑，难掩瑕疵，路人避之。", "你容貌奇丑，难掩瑕疵，旁人多避。"),
    (2, "丑陋", "你五官粗劣，谈不上顺眼。", "你五官粗劣，称不上好看。"),
    (3, "粗陋", "你面貌粗陋，胜在耐看尚欠。", "你面貌粗陋，略显刻薄之相。"),
    (4, "寒素", "你相貌寒素，平平无奇。", "你容颜寒素，谈不上出众。"),
    (5, "清秀", "你眉目尚算清秀。", "你眉眼清秀，颇为耐看。"),
    (6, "秀致", "你神情秀致，气质端正。", "你姿容秀致，气韵娴雅。"),
    (7, "俊美", "你面如冠玉，俊美非常。", "你明眸皓齿，艳若桃李。"),
    (8, "倾城", "你丰神俊朗，姿容可称倾城。", "你貌若倾城，一笑百媚生。"), 
    (9, "绝色", "你风采绝伦，行止如玉，令人侧目。", "你美绝人寰，风华绝代，惊艳四座。"),
    (10, "惊艳", "你容止惊艳，如谪仙临尘。", "你美若天仙，惊鸿一瞥，群芳失色。"),
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


__all__ = [
    "Appearance",
    "get_random_appearance",
]


