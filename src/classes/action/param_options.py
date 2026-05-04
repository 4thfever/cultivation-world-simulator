from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.environment.region import Region


MAX_PARAM_OPTIONS = 20


def build_param_options(action_cls: type, avatar: "Avatar") -> dict[str, list[dict[str, Any]]]:
    params = getattr(action_cls, "PARAMS", {}) or {}
    options: dict[str, list[dict[str, Any]]] = {}
    for param_name, param_type in params.items():
        param_options = _options_for_param(action_cls, avatar, param_name, param_type)
        if param_options:
            options[param_name] = param_options
    return options


def _options_for_param(action_cls: type, avatar: "Avatar", param_name: str, param_type: object) -> list[dict[str, Any]]:
    action_name = action_cls.__name__
    normalized_type = str(param_type).lower().replace(" ", "")

    if action_name == "Buy" and param_name == "target_name":
        return _store_item_options(avatar)
    if action_name == "Sell" and param_name == "target_name":
        return _sellable_item_options(avatar)
    if action_name == "Gift" and param_name == "item_id":
        return _gift_item_options(avatar)
    if param_name in {"avatar_name", "target_avatar"} or "avatarname" in normalized_type:
        return _avatar_options(avatar)
    if param_name in {"region", "region_name"} or "regionname" in normalized_type or "region_name" in normalized_type:
        return _known_region_options(avatar, cultivate_only=action_name == "Occupy")
    if param_name == "target_realm":
        return _realm_options_for_material_action(action_cls, avatar)
    if param_name == "direction" or "direction" in normalized_type:
        return _direction_options()
    return []


def _limit_options(options: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return options[:MAX_PARAM_OPTIONS]


def _item_kind(item: object) -> str:
    from src.classes.items.auxiliary import Auxiliary
    from src.classes.items.elixir import Elixir
    from src.classes.items.weapon import Weapon
    from src.classes.material import Material

    if isinstance(item, Elixir):
        return "elixir"
    if isinstance(item, Weapon):
        return "weapon"
    if isinstance(item, Auxiliary):
        return "auxiliary"
    if isinstance(item, Material):
        return "material"
    return type(item).__name__


def _item_option(
    item: object,
    *,
    price: int | None = None,
    count: int | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    option: dict[str, Any] = {
        "id": str(getattr(item, "id", "")),
        "name": str(getattr(item, "name", "")),
        "type": _item_kind(item),
    }
    realm = getattr(item, "realm", None)
    if realm is not None:
        option["realm"] = str(realm)
        option["realm_id"] = str(getattr(realm, "value", realm))
    if price is not None:
        option["price"] = int(price)
    if count is not None:
        option["count"] = int(count)
    if source is not None:
        option["source"] = source
    return option


def _store_item_options(avatar: "Avatar") -> list[dict[str, Any]]:
    from src.classes.prices import prices

    region = getattr(getattr(avatar, "tile", None), "region", None)
    store_items = list(getattr(region, "store_items", []) or [])
    options = []
    for item in store_items:
        options.append(_item_option(item, price=prices.get_buying_price(item, avatar), source="current_city_store"))
    return _limit_options(options)


def _sellable_item_options(avatar: "Avatar") -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    for material, count in getattr(avatar, "materials", {}).items():
        if int(count) > 0:
            options.append(_item_option(material, count=int(count), source="inventory"))

    weapon = getattr(avatar, "weapon", None)
    if weapon is not None:
        options.append(_item_option(weapon, source="equipped_weapon"))

    auxiliary = getattr(avatar, "auxiliary", None)
    if auxiliary is not None:
        options.append(_item_option(auxiliary, source="equipped_auxiliary"))

    return _limit_options(options)


def _gift_item_options(avatar: "Avatar") -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    magic_stone = getattr(avatar, "magic_stone", 0)
    stone_amount = int(getattr(magic_stone, "value", magic_stone) or 0)
    if stone_amount > 0:
        from src.i18n import t

        options.append({
            "id": "SPIRIT_STONE",
            "name": t("spirit stones"),
            "type": "spirit_stone",
            "max_amount": stone_amount,
        })

    for material, count in getattr(avatar, "materials", {}).items():
        if int(count) > 0:
            options.append(_item_option(material, count=int(count), source="inventory"))

    weapon = getattr(avatar, "weapon", None)
    if weapon is not None:
        options.append(_item_option(weapon, source="equipped_weapon"))

    auxiliary = getattr(avatar, "auxiliary", None)
    if auxiliary is not None:
        options.append(_item_option(auxiliary, source="equipped_auxiliary"))

    return _limit_options(options)


def _avatar_options(avatar: "Avatar") -> list[dict[str, Any]]:
    world = getattr(avatar, "world", None)
    manager = getattr(world, "avatar_manager", None)
    if manager is None:
        return []

    candidates = []
    if hasattr(manager, "get_observable_avatars"):
        candidates = manager.get_observable_avatars(avatar)
    if not candidates and hasattr(manager, "get_living_avatars"):
        candidates = [item for item in manager.get_living_avatars() if item is not avatar]

    options = []
    for other in candidates:
        if other is avatar or getattr(other, "is_dead", False):
            continue
        option = {
            "id": str(getattr(other, "id", "")),
            "name": str(getattr(other, "name", "")),
            "realm": str(getattr(getattr(other, "cultivation_progress", None), "get_info", lambda: "")()),
        }
        sect = getattr(other, "sect", None)
        if sect is not None:
            option["sect"] = str(getattr(sect, "name", ""))
        options.append(option)
    return _limit_options(options)


def _known_region_options(avatar: "Avatar", *, cultivate_only: bool = False) -> list[dict[str, Any]]:
    from src.classes.environment.region import CultivateRegion

    world = getattr(avatar, "world", None)
    game_map = getattr(world, "map", None)
    regions = list(getattr(game_map, "regions", {}).values())
    known_regions = getattr(avatar, "known_regions", None)

    options = []
    for region in regions:
        if known_regions is not None and region.id not in known_regions:
            continue
        if cultivate_only and not isinstance(region, CultivateRegion):
            continue
        if cultivate_only and getattr(region, "host_avatar", None) is avatar:
            continue
        options.append(_region_option(region))
    return _limit_options(options)


def _region_option(region: "Region") -> dict[str, Any]:
    return {
        "id": str(getattr(region, "id", "")),
        "name": str(getattr(region, "name", "")),
        "type": str(region.get_region_type() if hasattr(region, "get_region_type") else type(region).__name__),
    }


def _realm_options_for_material_action(action_cls: type, avatar: "Avatar") -> list[dict[str, Any]]:
    from src.systems.cultivation import Realm

    cost = int(getattr(action_cls, "COST", 0) or 0)
    counts = {realm: 0 for realm in Realm}
    for material, qty in getattr(avatar, "materials", {}).items():
        realm = getattr(material, "realm", None)
        if realm in counts:
            counts[realm] += int(qty)

    options = []
    for realm, count in counts.items():
        if cost > 0 and count < cost:
            continue
        options.append({
            "id": realm.value,
            "name": str(realm),
            "material_count": count,
            "required_material_count": cost,
        })
    return _limit_options(options)


def _direction_options() -> list[dict[str, Any]]:
    return [
        {"id": "north", "name": "north"},
        {"id": "south", "name": "south"},
        {"id": "east", "name": "east"},
        {"id": "west", "name": "west"},
    ]
