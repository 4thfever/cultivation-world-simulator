from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class DeathType(Enum):
    OLD_AGE = "老死"
    BATTLE = "战死"
    SERIOUS_INJURY = "重伤"

@dataclass
class DeathReason:
    death_type: DeathType
    killer_name: Optional[str] = None

    def __str__(self) -> str:
        if self.death_type == DeathType.BATTLE:
            killer = self.killer_name if self.killer_name else "未知角色"
            return f"被{killer}杀害"
        elif self.death_type == DeathType.SERIOUS_INJURY:
            return "重伤不治身亡"
        elif self.death_type == DeathType.OLD_AGE:
            return "寿元耗尽而亡"
        return self.death_type.value
