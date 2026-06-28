from __future__ import annotations

from typing import TYPE_CHECKING

from src.classes.action import InstantAction
from src.classes.action.param_options import ParamOptionSource
from src.classes.event import Event
from src.i18n import t
from src.systems.formation import (
    build_formation_record,
    compute_formation_cost,
    get_formation_disk_config,
    get_formation_type_name,
    has_formation_permission,
    is_formation_allowed_in_region,
    is_valid_formation_type,
    normalize_formation_type,
    place_region_formation,
)

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


class SetFormation(InstantAction):
    """布置阵法：装备阵盘后，在当前 region 布置一个限时区域效果。"""

    ACTION_NAME_ID = "set_formation_action_name"
    DESC_ID = "set_formation_description"
    REQUIREMENTS_ID = "set_formation_requirements"

    EMOJI = "🧭"
    PARAMS = {
        "formation_type": "FormationType",
    }
    PARAM_OPTION_SOURCES = {
        "formation_type": ParamOptionSource.AVAILABLE_FORMATION_TYPE,
    }

    def __init__(self, avatar: "Avatar", world):
        super().__init__(avatar, world)
        self._last_region = None
        self._last_formation_type = ""
        self._last_replaced = False
        self._last_cost = 0

    def can_possibly_start(self) -> bool:
        if not has_formation_permission(self.avatar):
            return False
        disk_cfg = get_formation_disk_config(getattr(self.avatar, "auxiliary", None))
        if disk_cfg is None:
            return False
        region = getattr(getattr(self.avatar, "tile", None), "region", None)
        if region is None:
            return False
        from src.systems.formation import get_available_formation_types_for_region

        available = get_available_formation_types_for_region(region)
        if not available:
            return False
        stone = int(getattr(getattr(self.avatar, "magic_stone", 0), "value", getattr(self.avatar, "magic_stone", 0)) or 0)
        return any(
            stone >= compute_formation_cost(self.avatar, cfg.key, region, disk_cfg)
            for cfg in available
        )

    def can_start(self, formation_type: str) -> tuple[bool, str]:
        if not has_formation_permission(self.avatar):
            return False, t("Missing formation disk")
        disk_cfg = get_formation_disk_config(getattr(self.avatar, "auxiliary", None))
        if disk_cfg is None:
            return False, t("Missing formation disk")
        normalized = normalize_formation_type(formation_type)
        if not is_valid_formation_type(normalized):
            return False, t("Invalid formation type")

        region = getattr(getattr(self.avatar, "tile", None), "region", None)
        if region is None:
            return False, t("Current location cannot set formation")
        if not is_formation_allowed_in_region(normalized, region):
            return False, t("Formation cannot be set in current region")

        cost = compute_formation_cost(self.avatar, normalized, region, disk_cfg)
        stone = int(getattr(getattr(self.avatar, "magic_stone", 0), "value", getattr(self.avatar, "magic_stone", 0)) or 0)
        if stone < cost:
            return False, t("Not enough spirit stones")
        return True, ""

    def start(self, formation_type: str) -> Event:
        region = getattr(getattr(self.avatar, "tile", None), "region", None)
        region_name = getattr(region, "name", t("Current region"))
        formation_name = get_formation_type_name(formation_type)
        content = t(
            "{avatar} begins setting {formation} in {region}.",
            avatar=self.avatar.name,
            formation=formation_name,
            region=region_name,
        )
        return Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])

    def _execute(self, formation_type: str) -> None:
        self._last_region = getattr(getattr(self.avatar, "tile", None), "region", None)
        self._last_formation_type = normalize_formation_type(formation_type)
        self._last_replaced = False
        self._last_cost = 0

        if self._last_region is None:
            return
        disk_cfg = get_formation_disk_config(getattr(self.avatar, "auxiliary", None))
        if disk_cfg is None or not is_valid_formation_type(self._last_formation_type):
            return
        if not is_formation_allowed_in_region(self._last_formation_type, self._last_region):
            return

        cost = compute_formation_cost(self.avatar, self._last_formation_type, self._last_region, disk_cfg)
        stone = int(getattr(getattr(self.avatar, "magic_stone", 0), "value", getattr(self.avatar, "magic_stone", 0)) or 0)
        if stone < cost:
            return

        self.avatar.magic_stone -= cost
        formation = build_formation_record(self.avatar, self._last_formation_type, self._last_region, disk_cfg)
        formation["cost"] = cost
        old = place_region_formation(self.world, int(self._last_region.id), formation)
        self._last_cost = cost
        self._last_replaced = old is not None

    async def finish(self, formation_type: str) -> list[Event]:
        region = self._last_region or getattr(getattr(self.avatar, "tile", None), "region", None)
        if region is None:
            return []
        formation_name = get_formation_type_name(self._last_formation_type or formation_type)
        if self._last_replaced:
            content = t(
                "{avatar} set {formation} in {region}; the original formation in this region was replaced.",
                avatar=self.avatar.name,
                formation=formation_name,
                region=region.name,
            )
        else:
            content = t(
                "{avatar} set {formation} in {region}.",
                avatar=self.avatar.name,
                formation=formation_name,
                region=region.name,
            )
        return [Event(self.world.month_stamp, content, related_avatars=[self.avatar.id])]
