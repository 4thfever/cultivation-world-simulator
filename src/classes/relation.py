from __future__ import annotations

from enum import Enum


class Relation(Enum):
    KINSHIP = "kinship"            # 亲子/亲属
    LOVERS = "lovers"              # 情侣/道侣
    MASTER_APPRENTICE = "mentorship"  # 师徒
    FRIEND = "friend"              # 朋友
    ENEMY = "enemy"                # 仇人

    def __str__(self) -> str:
        return relation_strs.get(self, self.value)


relation_strs = {
    Relation.KINSHIP: "亲属",
    Relation.LOVERS: "情侣",
    Relation.MASTER_APPRENTICE: "师徒",
    Relation.FRIEND: "朋友",
    Relation.ENEMY: "仇人",
}


