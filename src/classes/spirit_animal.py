from __future__ import annotations

from dataclasses import dataclass

from src.systems.cultivation import Realm


@dataclass
class SpiritAnimal:
    """
    灵兽：附着于 Avatar 的唯一“守护灵兽”。
    仅记录名称与境界，并据境界提供固定战斗力点数加成。
    
    规则：
    - 练气/筑基/金丹/元婴 对应战斗力点数 +2/+4/+6/+8
    - Avatar 最多只能拥有一个 spirit_animal；新的会覆盖旧的。
    """

    name: str
    realm: Realm

    def get_extra_strength_points(self) -> int:
        mapping = {
            Realm.Qi_Refinement: 2,
            Realm.Foundation_Establishment: 4,
            Realm.Core_Formation: 6,
            Realm.Nascent_Soul: 8,
        }
        return mapping.get(self.realm, 0)

    def get_info(self) -> str:
        return f"{self.name}（{str(self.realm)}）"

    @property
    def effects(self) -> dict[str, object]:
        """
        灵兽提供的效果集合。当前仅包含战斗力点数，后续可扩展其他键。
        """
        pts = self.get_extra_strength_points()
        return {"extra_battle_strength_points": pts} if pts else {}

    def get_structured_info(self) -> dict:
        from src.classes.effect import format_effects_to_text
        return {
            "name": self.name,
            "desc": f"境界：{str(self.realm)}",
            "grade": str(self.realm),
            "effect_desc": format_effects_to_text(self.effects),
        }


