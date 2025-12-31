from __future__ import annotations

from src.classes.action import InstantAction
from src.classes.event import Event
from src.classes.weapon import get_random_weapon_by_realm
from src.classes.weapon_type import WeaponType
from src.classes.cultivation import Realm
from src.classes.normalize import normalize_weapon_type


class SwitchWeapon(InstantAction):
    """
    切换兵器：将当前兵器切换为指定类型的练气兵器。
    熟练度重置为0。
    """

    ACTION_NAME = "切换兵器"
    DESC = "切换到指定类型的练气兵器，或卸下兵器。当前兵器会丧失，熟练度会重置为0。适用于想要更换兵器类型或从头修炼新兵器的情况。"
    DOABLES_REQUIREMENTS = "无前置条件"
    PARAMS = {"weapon_type_name": "str"}

    def _execute(self, weapon_type_name: str) -> None:
        # 处理卸下兵器的情况
        if weapon_type_name in ["无", "None", "none", ""]:
            self.avatar.change_weapon(None)
            return

        # 规范化兵器类型名称
        normalized_type = normalize_weapon_type(weapon_type_name)
        
        # 匹配 WeaponType 枚举
        target_weapon_type = None
        for wt in WeaponType:
            if wt.value == normalized_type:
                target_weapon_type = wt
                break
        
        if target_weapon_type is None:
            return
        
        # 获取练气兵器（练气期）
        common_weapon = get_random_weapon_by_realm(Realm.Qi_Refinement, target_weapon_type)
        if common_weapon is None:
            return
        
        # 切换兵器（使用 Avatar 的 change_weapon 方法）
        self.avatar.change_weapon(common_weapon)

    def can_start(self, weapon_type_name: str | None = None) -> tuple[bool, str]:
        if weapon_type_name is None:
            # AI调用：总是可以切换兵器
            return True, ""
        
        # 处理卸下兵器的情况
        if weapon_type_name in ["无", "None", "none", ""]:
            if self.avatar.weapon is None:
                return False, "当前已处于无兵器状态"
            return True, ""

        # 规范化并验证兵器类型
        normalized_type = normalize_weapon_type(weapon_type_name)
        target_weapon_type = None
        for wt in WeaponType:
            if wt.value == normalized_type:
                target_weapon_type = wt
                break
        
        if target_weapon_type is None:
            return False, f"未知兵器类型: {weapon_type_name}（支持的类型：剑/刀/枪/棍/扇/鞭/琴/笛/暗器/无）"
        
        # 检查是否已经是该类型的练气兵器
        if self.avatar.weapon is not None and \
           self.avatar.weapon.weapon_type == target_weapon_type and \
           self.avatar.weapon.realm == Realm.Qi_Refinement:
            return False, f"已经装备了基础{target_weapon_type.value}"
        
        # 检查练气兵器是否存在
        common_weapon = get_random_weapon_by_realm(Realm.Qi_Refinement, target_weapon_type)
        if common_weapon is None:
            return False, f"系统中不存在练气{target_weapon_type.value}"
        
        return True, ""

    def start(self, weapon_type_name: str) -> Event:
        if weapon_type_name in ["无", "None", "none", ""]:
            return Event(
                self.world.month_stamp,
                f"{self.avatar.name} 卸下了兵器",
                related_avatars=[self.avatar.id]
            )

        normalized_type = normalize_weapon_type(weapon_type_name)
        return Event(
            self.world.month_stamp,
            f"{self.avatar.name} 切换兵器为练气{normalized_type}",
            related_avatars=[self.avatar.id]
        )

    async def finish(self, weapon_type_name: str) -> list[Event]:
        return []

