from typing import TYPE_CHECKING, Any, Dict, List

from src.classes.effect import format_effects_to_text

if TYPE_CHECKING:
    from src.classes.core.sect import Sect
    from src.classes.core.world import World


def _sect_runtime_source_label(source: str, language_manager: object) -> str:
    """
    根据当前语言返回运行时宗门效果来源的可读标签。
    逻辑与 /api/detail 中 sect 分支保持一致。
    """
    lang = str(language_manager)
    key = (source or "").strip().lower()

    if lang == "zh-CN":
        if key == "base":
            return "基础效果"
        if key == "sect_random_event":
            return "宗门随机事件"
        return source or "临时效果"

    if lang == "zh-TW":
        if key == "base":
            return "基礎效果"
        if key == "sect_random_event":
            return "宗門隨機事件"
        return source or "臨時效果"

    if key == "base":
        return "Base effect"
    if key == "sect_random_event":
        return "Sect random event"
    return source or "Temporary effect"


def build_sect_detail(sect: "Sect", world: "World", language_manager: object) -> Dict[str, Any]:
    """
    组装宗门详情的完整结构化信息。

    - 基础字段来自 sect.get_structured_info()
    - 运行时效果字段与 /api/detail 现有实现保持完全一致
    """
    # 1. 先获取领域层提供的基础信息
    info: Dict[str, Any] = sect.get_structured_info()

    # 2. 拼接运行时效果信息（与原 /api/detail 保持等价）
    current_month = int(getattr(world, "month_stamp", 0))
    runtime_items: List[Dict[str, Any]] = []

    base_runtime_effects = dict(getattr(sect, "sect_effects", {}) or {})
    if base_runtime_effects:
        base_desc = format_effects_to_text(base_runtime_effects).strip()
        if base_desc:
            runtime_items.append(
                {
                    "source": "base",
                    "source_label": _sect_runtime_source_label("base", language_manager),
                    "desc": base_desc,
                    "remaining_months": -1,
                    "is_permanent": True,
                }
            )

    for temp in sect.get_active_temporary_sect_effects(current_month):
        effects = dict(temp.get("effects", {}) or {})
        if not effects:
            continue

        desc = format_effects_to_text(effects).strip()
        if not desc:
            continue

        start_month = int(temp.get("start_month", current_month))
        duration = max(0, int(temp.get("duration", 0)))
        remaining_months = max(0, start_month + duration - current_month)
        source = str(temp.get("source", "temporary") or "temporary")

        runtime_items.append(
            {
                "source": source,
                "source_label": _sect_runtime_source_label(source, language_manager),
                "desc": desc,
                "remaining_months": remaining_months,
                "is_permanent": False,
            }
        )

    active_effects = sect.get_sect_effects(current_month)
    info["runtime_effect_desc"] = (
        format_effects_to_text(active_effects).strip() if active_effects else ""
    )
    info["runtime_extra_income_per_tile"] = float(
        sect.get_extra_income_per_tile(current_month)
    )
    info["runtime_effects_count"] = len(runtime_items)
    info["runtime_effect_items"] = runtime_items

    return info

