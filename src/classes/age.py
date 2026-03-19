import random

from src.systems.time import MonthStamp


class Age:
    """
    角色寿元管理。

    新模型：
    - 先天寿元 `innate_max_lifespan`：角色出生/创建时随机得到
    - 实际寿元 `max_lifespan`：先天寿元 + 所有效果中的 extra_max_lifespan
    - 不再存在“衰老区”或缓慢老死概率；达到/超过寿元时立即死亡
    """

    INITIAL_MAX_LIFESPAN_MIN = 60
    INITIAL_MAX_LIFESPAN_MAX = 90

    def __init__(
        self,
        age: int,
        realm=None,
        innate_max_lifespan: int | None = None,
    ):
        self.age = age
        self.innate_max_lifespan = (
            int(innate_max_lifespan)
            if innate_max_lifespan is not None
            else self.roll_innate_max_lifespan()
        )
        # 初始实际寿元先等于先天寿元，Avatar.__post_init__/recalc_effects 会重新汇总。
        self.max_lifespan = self.innate_max_lifespan

    @classmethod
    def roll_innate_max_lifespan(cls) -> int:
        return random.randint(cls.INITIAL_MAX_LIFESPAN_MIN, cls.INITIAL_MAX_LIFESPAN_MAX)

    @property
    def value(self) -> int:
        return self.age

    def get_age(self) -> int:
        return self.age

    def recalculate_max_lifespan(self, extra_bonus: int = 0) -> int:
        self.max_lifespan = self.innate_max_lifespan + int(extra_bonus or 0)
        return self.max_lifespan

    def get_expected_lifespan(self, realm=None) -> int:
        return self.max_lifespan

    def increase_max_lifespan(self, years: int) -> None:
        if years <= 0:
            return
        self.innate_max_lifespan += years
        self.max_lifespan += years

    def decrease_max_lifespan(self, years: int) -> None:
        if years <= 0:
            return
        self.innate_max_lifespan -= years
        self.max_lifespan -= years

    def get_death_probability(self, realm=None) -> float:
        return 1.0 if self.age >= self.max_lifespan else 0.0

    def death_by_old_age(self, realm=None) -> bool:
        return random.random() < self.get_death_probability(realm)

    def calculate_age(self, current_month_stamp: MonthStamp, birth_month_stamp: MonthStamp) -> int:
        return max(0, (current_month_stamp - birth_month_stamp) // 12)

    def update_age(self, current_month_stamp: MonthStamp, birth_month_stamp: MonthStamp):
        self.age = self.calculate_age(current_month_stamp, birth_month_stamp)

    def get_lifespan_progress(self, realm=None) -> tuple[int, int]:
        return self.age, self.max_lifespan

    def is_elderly(self, realm=None) -> bool:
        return self.age >= self.max_lifespan

    def __str__(self) -> str:
        return f"{self.age}/{self.max_lifespan}"

    def __repr__(self) -> str:
        return f"Age({self.age})"

    def to_dict(self) -> dict:
        return {
            "age": self.age,
            "innate_max_lifespan": self.innate_max_lifespan,
        }

    @classmethod
    def from_dict(cls, data: dict, realm=None) -> "Age":
        age_obj = cls(
            data["age"],
            realm=realm,
            innate_max_lifespan=data["innate_max_lifespan"],
        )
        return age_obj
