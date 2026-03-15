from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.classes.language import language_manager
from src.config import get_settings_service
from src.run.log import get_logger
from src.utils.llm import call_llm_with_task_name
from src.utils.llm.exceptions import LLMError, ParseError
from src.utils.strings import to_json_str_with_intent

if TYPE_CHECKING:
    from src.classes.core.sect import Sect
    from src.classes.core.world import World
    from src.systems.sect_decision_context import SectDecisionContext


class SectThinker:
    """
    宗门思考生成器。

    输入：SectDecisionContext + 本轮决策摘要
    输出：宗门意志口吻的短文本（30~100字）
    """

    MIN_LEN = 30
    MAX_LEN = 100

    @classmethod
    async def think(
        cls,
        sect: "Sect",
        decision_context: "SectDecisionContext",
        world: "World",
        *,
        decision_summary: str = "",
    ) -> str:
        if not cls._llm_available():
            cls._warn_fallback(sect, "LLM runtime config unavailable")
            return cls._fallback(sect)

        infos = {
            "sect_name": sect.name,
            "world_info": to_json_str_with_intent(cls._serialize_world_info(world)),
            "current_phenomenon_info": cls._current_phenomenon_info(world),
            "decision_context_info": to_json_str_with_intent(
                cls._serialize_context(decision_context)
            ),
            "decision_summary": str(decision_summary or ""),
        }

        try:
            result = await call_llm_with_task_name(
                task_name="sect_thinker",
                template_path=cls._resolve_template_path(),
                infos=infos,
            )
            raw = ""
            if isinstance(result, dict):
                raw = str(result.get("sect_thinking", "")).strip()
            return cls._normalize(raw, sect)
        except (LLMError, ParseError, Exception) as exc:
            cls._warn_fallback(sect, f"LLM think failed: {exc}")
            return cls._fallback(sect)

    @classmethod
    def _llm_available(cls) -> bool:
        profile, api_key = get_settings_service().get_llm_runtime_config()
        return bool(profile.base_url and api_key and profile.model_name)

    @classmethod
    def _normalize(cls, text: str, sect: "Sect") -> str:
        clean = " ".join((text or "").split())
        if len(clean) < cls.MIN_LEN:
            cls._warn_fallback(sect, f"LLM response too short ({len(clean)} chars)")
            return cls._fallback(sect)
        if len(clean) > cls.MAX_LEN:
            return clean[: cls.MAX_LEN]
        return clean

    @classmethod
    def _fallback(cls, sect: "Sect") -> str:
        return (
            f"我宗已定近年取舍，接下来当守住门规与根基，"
            f"择才而纳、赏罚分明，以稳中求进扩张宗门气象。"
        )

    @classmethod
    def _warn_fallback(cls, sect: "Sect", reason: str) -> None:
        get_logger().logger.warning(
            "SectThinker fallback for %s(%s): %s",
            getattr(sect, "name", "unknown"),
            getattr(sect, "id", "unknown"),
            reason,
        )

    @classmethod
    def _serialize_context(cls, ctx: "SectDecisionContext") -> dict[str, Any]:
        recent = []
        for ev in ctx.history.get("recent_events", []):
            recent.append(
                {
                    "month_stamp": int(getattr(ev, "month_stamp", 0)),
                    "content": str(getattr(ev, "content", "")),
                }
            )

        return {
            "basic_structured": dict(ctx.basic_structured),
            "basic_text": ctx.basic_text,
            "identity": dict(ctx.identity),
            "power": dict(ctx.power),
            "territory": dict(ctx.territory),
            "self_assessment": dict(ctx.self_assessment),
            "economy": dict(ctx.economy),
            "rule": dict(ctx.rule),
            "recruitment_candidates": list(ctx.recruitment_candidates),
            "member_candidates": list(ctx.member_candidates),
            "relations": list(ctx.relations),
            "relations_summary": ctx.relations_summary,
            "history": {
                "summary_text": str(ctx.history.get("summary_text", "")),
                "recent_events": recent,
            },
        }

    @classmethod
    def _resolve_template_path(cls) -> Path:
        lang = str(language_manager)
        path = Path(f"static/locales/{lang}/templates/sect_thinker.txt")
        if path.exists():
            return path
        return Path("static/locales/zh-CN/templates/sect_thinker.txt")

    @classmethod
    def _serialize_world_info(cls, world: "World") -> dict[str, Any]:
        try:
            info = world.get_info(detailed=True)
            if isinstance(info, dict):
                return info
        except Exception:
            pass
        return {}

    @classmethod
    def _current_phenomenon_info(cls, world: "World") -> str:
        phenomenon = getattr(world, "current_phenomenon", None)
        if phenomenon is None:
            return "当前无天地异象。"
        name = str(getattr(phenomenon, "name", "") or "")
        desc = str(getattr(phenomenon, "desc", "") or "")
        if name and desc:
            return f"{name}：{desc}"
        return name or desc or "当前有天地异象，但描述缺失。"
