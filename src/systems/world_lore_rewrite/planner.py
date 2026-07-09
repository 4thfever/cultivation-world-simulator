from __future__ import annotations

from typing import Any, Iterable

from omegaconf import OmegaConf

from src.classes.core.sect import sects_by_id
from src.classes.environment.sect_region import SectRegion
from src.classes.items.auxiliary import auxiliaries_by_id
from src.classes.items.weapon import weapons_by_id
from src.classes.sect_metadata import get_sect_region_by_sect_id
from src.classes.technique import techniques_by_id
from src.utils.config import CONFIG

from .models import RewriteJob, WorldLoreRewriteConfig, WorldLoreRewriteContext


def _get_config_value(section: Any, key: str, default: Any) -> Any:
    if section is None:
        return default
    try:
        return section.get(key, default)
    except AttributeError:
        return getattr(section, key, default)


def load_world_lore_rewrite_config() -> WorldLoreRewriteConfig:
    section = getattr(CONFIG, "world_lore", None)
    chunk_size = _get_config_value(section, "chunk_size", {}) or {}

    def chunk(key: str, default: int) -> int:
        return max(1, int(_get_config_value(chunk_size, key, default)))

    return WorldLoreRewriteConfig(
        rewrite_items=bool(_get_config_value(section, "rewrite_items", True)),
        total_timeout_seconds=float(_get_config_value(section, "total_timeout_seconds", 240)),
        task_timeout_seconds=float(_get_config_value(section, "task_timeout_seconds", 60)),
        min_retry_budget_seconds=float(_get_config_value(section, "min_retry_budget_seconds", 20)),
        max_parse_retries=max(0, int(_get_config_value(section, "max_parse_retries", 1))),
        max_transport_retries=max(0, int(_get_config_value(section, "max_transport_retries", 0))),
        chunk_size_regions=chunk("regions", 10),
        chunk_size_sect_groups=chunk("sect_groups", 6),
        chunk_size_techniques=chunk("techniques", 10),
        chunk_size_weapons=chunk("weapons", 10),
        chunk_size_auxiliaries=chunk("auxiliaries", 10),
    )


def build_world_lore_context(world: Any, lore_text: str) -> WorldLoreRewriteContext:
    return WorldLoreRewriteContext(
        world=world,
        lore_text=str(lore_text or "").strip(),
        map_summary=build_map_summary(world),
        style_guide=build_default_style_guide(lore_text),
        config=load_world_lore_rewrite_config(),
    )


def build_default_style_guide(lore_text: str) -> dict[str, Any]:
    text = str(lore_text or "").strip()
    keywords = _extract_keywords(text)
    return {
        "world_tone": "、".join(keywords[:6]) if keywords else "仙侠、历史感、地域感",
        "naming_rules": [
            "名称应明显贴合世界观，但避免所有名称重复同一关键词",
            "描述应具体、可视化，不解释游戏机制",
        ],
        "forbidden_patterns": [
            "不要写数值加成",
            "不要写玩家、系统、游戏机制",
            "不要输出详细思考过程",
        ],
        "description_style": "简洁、有画面感，保留实体原本玩法定位",
    }


def build_map_summary(world: Any) -> dict[str, Any]:
    game_map = getattr(world, "map", None)
    if game_map is None:
        return {}

    return {
        "map_id": str(getattr(game_map, "map_id", "") or ""),
        "map_name": str(getattr(game_map, "map_name", "") or ""),
        "preset_version": int(getattr(game_map, "preset_version", 0) or 0),
        "width": int(getattr(game_map, "width", 0) or 0),
        "height": int(getattr(game_map, "height", 0) or 0),
        "wilderness_tile": str(getattr(game_map, "wilderness_tile", "") or ""),
        "landmark_count": len(getattr(game_map, "landmarks", {}) or {}),
        "region_override_count": len(getattr(game_map, "region_overrides", {}) or {}),
    }


def build_world_lore_jobs(context: WorldLoreRewriteContext) -> list[RewriteJob]:
    jobs: list[RewriteJob] = []
    jobs.extend(_build_region_jobs(context))
    jobs.extend(_build_sect_group_jobs(context))

    if context.config.rewrite_items:
        jobs.extend(_build_item_jobs(context))

    return jobs


def _build_region_jobs(context: WorldLoreRewriteContext) -> list[RewriteJob]:
    game_map = getattr(context.world, "map", None)
    regions = getattr(game_map, "regions", {}) or {}
    region_entities = [
        _serialize_region(region, context.world)
        for _, region in sorted(regions.items(), key=lambda item: int(item[0]))
        if not isinstance(region, SectRegion)
    ]

    return [
        RewriteJob(
            id=f"regions#{index}",
            kind="regions",
            task_name="world_lore_region_rewrite",
            entities=chunk,
            entity_label="地点",
            instructions=(
                "重写地点 name/desc。desc 应描述地貌、建筑、环境异象、生活或修行氛围，"
                "必须匹配当前地图语义，不要写玩家加成、数值效果或系统机制。"
            ),
            result_field="entities",
            map_summary=context.map_summary,
            style_guide=context.style_guide,
            lore_text=context.lore_text,
        )
        for index, chunk in enumerate(_chunks(region_entities, context.config.chunk_size_regions), start=1)
    ]


def _build_sect_group_jobs(context: WorldLoreRewriteContext) -> list[RewriteJob]:
    sect_entities: list[dict[str, Any]] = []
    sect_region_entities: list[dict[str, Any]] = []

    for sect_id, sect in sorted(sects_by_id.items(), key=lambda item: int(item[0])):
        sect_entities.append(_serialize_sect(sect, context.world))
        region = get_sect_region_by_sect_id(context.world, int(sect_id))
        if region is not None:
            sect_region_entities.append(_serialize_region(region, context.world))

    jobs: list[RewriteJob] = []
    sect_chunks = list(_chunks(sect_entities, context.config.chunk_size_sect_groups))
    for index, sect_chunk in enumerate(sect_chunks, start=1):
        sect_ids = {int(entity["id"]) for entity in sect_chunk}
        paired_chunk = [
            entity
            for entity in sect_region_entities
            if int(entity.get("sect_id", -1)) in sect_ids
        ]
        jobs.append(
            RewriteJob(
                id=f"sect_group#{index}",
                kind="sect_group",
                task_name="world_lore_sect_group_rewrite",
                entities=sect_chunk,
                entity_label="宗门",
                instructions=(
                    "同时重写宗门本体和对应宗门驻地。宗门 desc 侧重宗门定位、修行方式、组织气质、"
                    "内部结构与潜在矛盾；驻地 desc 侧重地貌、建筑、空间层次和环境异象。"
                    "两者应互相配合但不要重复，不要写门规惩罚、玩家加成、数值效果或系统机制。"
                ),
                result_field="sects",
                map_summary=context.map_summary,
                style_guide=context.style_guide,
                lore_text=context.lore_text,
                paired_entities=paired_chunk,
                paired_result_field="sect_regions",
                paired_entity_label="宗门驻地",
            )
        )
    return jobs


def _build_item_jobs(context: WorldLoreRewriteContext) -> list[RewriteJob]:
    jobs: list[RewriteJob] = []
    jobs.extend(
        _build_entity_jobs(
            context=context,
            kind="techniques",
            task_name="world_lore_technique_rewrite",
            job_prefix="techniques",
            label="功法",
            entities=[_serialize_technique(item) for _, item in sorted(techniques_by_id.items())],
            chunk_size=context.config.chunk_size_techniques,
            instructions=(
                "重写功法 name/desc。保持原本属性、品阶、境界和玩法定位。"
                "desc 应描述修行路径、气息、风险和意象，不要写具体伤害、加成或游戏机制。"
            ),
        )
    )
    jobs.extend(
        _build_entity_jobs(
            context=context,
            kind="weapons",
            task_name="world_lore_weapon_rewrite",
            job_prefix="weapons",
            label="兵器",
            entities=[_serialize_weapon(item) for _, item in sorted(weapons_by_id.items())],
            chunk_size=context.config.chunk_size_weapons,
            instructions=(
                "重写兵器 name/desc。保持原本武器类型、境界和玩法定位。"
                "desc 应描述材质、形制、来历和使用气质，不要写数值加成或游戏机制。"
            ),
        )
    )
    jobs.extend(
        _build_entity_jobs(
            context=context,
            kind="auxiliaries",
            task_name="world_lore_auxiliary_rewrite",
            job_prefix="auxiliaries",
            label="辅助装备",
            entities=[_serialize_auxiliary(item) for _, item in sorted(auxiliaries_by_id.items())],
            chunk_size=context.config.chunk_size_auxiliaries,
            instructions=(
                "重写辅助装备 name/desc。保持原本境界和辅助定位。"
                "desc 应描述佩戴方式、法器性质、护持或辅助意象，不要写数值加成或不存在的机制。"
            ),
        )
    )
    return jobs


def _build_entity_jobs(
    *,
    context: WorldLoreRewriteContext,
    kind: Any,
    task_name: str,
    job_prefix: str,
    label: str,
    entities: list[dict[str, Any]],
    chunk_size: int,
    instructions: str,
) -> list[RewriteJob]:
    return [
        RewriteJob(
            id=f"{job_prefix}#{index}",
            kind=kind,
            task_name=task_name,
            entities=chunk,
            entity_label=label,
            instructions=instructions,
            result_field="entities",
            map_summary=context.map_summary,
            style_guide=context.style_guide,
            lore_text=context.lore_text,
        )
        for index, chunk in enumerate(_chunks(entities, chunk_size), start=1)
    ]


def _serialize_region(region: Any, world: Any) -> dict[str, Any]:
    game_map = getattr(world, "map", None)
    region_id = int(getattr(region, "id"))
    overrides = getattr(game_map, "region_overrides", {}) or {}
    landmarks = getattr(game_map, "landmarks", {}) or {}
    center = getattr(region, "center_loc", (0, 0))
    payload = {
        "id": region_id,
        "type": str(region.get_region_type() if hasattr(region, "get_region_type") else ""),
        "name": str(getattr(region, "name", "") or ""),
        "desc": str(getattr(region, "desc", "") or ""),
        "tile_count": len(getattr(region, "cors", []) or []),
        "center": [int(center[0]), int(center[1])] if isinstance(center, tuple) and len(center) == 2 else [0, 0],
        "map_override": region_id in overrides,
    }
    if region_id in landmarks:
        payload["landmark"] = dict(landmarks[region_id])
    if isinstance(region, SectRegion):
        payload["sect_id"] = int(getattr(region, "sect_id", -1))
        payload["sect_name"] = str(getattr(region, "sect_name", "") or "")
    return payload


def _serialize_sect(sect: Any, world: Any) -> dict[str, Any]:
    region = get_sect_region_by_sect_id(world, int(getattr(sect, "id")))
    return {
        "id": int(getattr(sect, "id")),
        "name": str(getattr(sect, "name", "") or ""),
        "desc": str(getattr(sect, "desc", "") or ""),
        "alignment": str(getattr(getattr(sect, "alignment", None), "value", getattr(sect, "alignment", "")) or ""),
        "orthodoxy_id": str(getattr(sect, "orthodoxy_id", "") or ""),
        "headquarter_region_id": int(getattr(region, "id", 0) or 0) if region is not None else None,
        "headquarter_name": str(getattr(region, "name", "") or "") if region is not None else "",
    }


def _serialize_technique(item: Any) -> dict[str, Any]:
    return {
        "id": int(getattr(item, "id")),
        "name": str(getattr(item, "name", "") or ""),
        "desc": str(getattr(item, "desc", "") or ""),
        "attribute": str(getattr(getattr(item, "attribute", None), "value", "")),
        "grade": str(getattr(getattr(item, "grade", None), "value", "")),
        "realm": str(getattr(getattr(item, "realm", None), "value", "") or ""),
    }


def _serialize_weapon(item: Any) -> dict[str, Any]:
    return {
        "id": int(getattr(item, "id")),
        "name": str(getattr(item, "name", "") or ""),
        "desc": str(getattr(item, "desc", "") or ""),
        "weapon_type": str(getattr(getattr(item, "weapon_type", None), "value", "")),
        "realm": str(getattr(getattr(item, "realm", None), "value", "")),
    }


def _serialize_auxiliary(item: Any) -> dict[str, Any]:
    return {
        "id": int(getattr(item, "id")),
        "name": str(getattr(item, "name", "") or ""),
        "desc": str(getattr(item, "desc", "") or ""),
        "realm": str(getattr(getattr(item, "realm", None), "value", "")),
    }


def _chunks(items: list[dict[str, Any]], size: int) -> Iterable[list[dict[str, Any]]]:
    for index in range(0, len(items), max(1, size)):
        yield items[index:index + size]


def _extract_keywords(text: str) -> list[str]:
    separators = "，。；、,.!?！？\n\r\t "
    normalized = str(text or "")
    for sep in separators:
        normalized = normalized.replace(sep, " ")
    seen: list[str] = []
    for part in normalized.split(" "):
        part = part.strip()
        if 2 <= len(part) <= 8 and part not in seen:
            seen.append(part)
        if len(seen) >= 8:
            break
    return seen
