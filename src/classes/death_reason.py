from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class DeathType(Enum):
    OLD_AGE = "old_age"
    BATTLE = "battle"
    SERIOUS_INJURY = "serious_injury"
    HIDDEN_DOMAIN = "hidden_domain"

@dataclass
class DeathReason:
    death_type: DeathType
    killer_name: Optional[str] = None

    def __str__(self) -> str:
        from src.i18n import t
        if self.death_type == DeathType.BATTLE:
            killer = self.killer_name if self.killer_name else t("Unknown character")
            return t("Killed by {killer}", killer=killer)
        elif self.death_type == DeathType.SERIOUS_INJURY:
            return t("Died from severe injuries")
        elif self.death_type == DeathType.HIDDEN_DOMAIN:
            return t("Perished in a Hidden Domain")
        elif self.death_type == DeathType.OLD_AGE:
            return t("Died of old age")
        return t(self.death_type.value)
