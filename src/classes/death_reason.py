from enum import Enum

class DeathReason(Enum):
    OLD_AGE = "老死"
    BATTLE = "战死"
    SERIOUS_INJURY = "重伤"
    UNKNOWN = "未知"

    def __str__(self) -> str:
        return self.value

