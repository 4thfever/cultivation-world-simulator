from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.config import get_settings_service
from src.i18n import t
from src.i18n.template_resolver import resolve_locale_template_path
from src.run.log import get_logger
from src.utils.config import CONFIG
from src.utils.llm import call_llm_with_task_name
from src.utils.llm.exceptions import LLMError, ParseError
from src.utils.strings import to_json_str_with_intent

if TYPE_CHECKING:
    from src.classes.core.sect import Sect
    from src.classes.core.world import World
    from src.systems.sect_decision_context import SectDecisionContext


class SectThinker:
    """
    宗门周期思考生成器。

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
            "world_lore": world.world_lore.text,
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
    def get_thinking_interval_years(cls) -> int:
        interval = int(
            getattr(
                CONFIG.sect,
                "thinking_interval_years",
                getattr(CONFIG.sect, "decision_interval_years", 5),
            )
        )
        return interval if interval > 0 else 5

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
        return t(
            "Our sect has settled its priorities for the coming years; next we should guard our rules and foundations, recruit talent with care, reward and punish fairly, and expand our momentum through steady progress."
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
        return resolve_locale_template_path(
            "sect_thinker.txt",
            preferred_dir=CONFIG.paths.templates,
        )

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
            return t("There is currently no celestial phenomenon.")
        name = str(getattr(phenomenon, "name", "") or "")
        desc = str(getattr(phenomenon, "desc", "") or "")
        if name and desc:
            return t("{name}: {desc}", name=name, desc=desc)
        return name or desc or t("A celestial phenomenon is present, but its description is missing.")
