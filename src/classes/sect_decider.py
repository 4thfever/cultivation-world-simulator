from __future__ import annotations

import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from src.classes.alignment import Alignment
from src.classes.language import language_manager
from src.classes.event import Event
from src.classes.sect_ranks import get_rank_from_realm
from src.classes.technique import (
    Technique,
    TechniqueAttribute,
    is_attribute_compatible_with_root,
    techniques_by_name,
)
from src.systems.single_choice import (
    SectRecruitmentRequest,
    resolve_sect_recruitment,
)
from src.utils.config import CONFIG
from src.utils.llm import call_llm_with_task_name
from src.utils.llm.exceptions import LLMError, ParseError
from src.utils.strings import to_json_str_with_intent

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.core.sect import Sect
    from src.classes.core.world import World
    from src.systems.sect_decision_context import SectDecisionContext


@dataclass(slots=True)
class SectDecisionResult:
    events: list[Event] = field(default_factory=list)
    recruitment_count: int = 0
    expulsion_count: int = 0
    technique_reward_count: int = 0
    support_count: int = 0
    summary_text: str = ""


@dataclass(slots=True)
class SectDecisionPlan:
    recruit_avatar_ids: list[str] = field(default_factory=list)
    expel_avatar_ids: list[str] = field(default_factory=list)
    reward_avatar_ids: list[str] = field(default_factory=list)
    support_avatar_ids: list[str] = field(default_factory=list)
    thinking: str = ""


class SectDecider:
    """
    五年一次的宗门行政决策执行器。
    """

    @classmethod
    async def decide(
        cls,
        sect: "Sect",
        decision_context: "SectDecisionContext",
        world: "World",
    ) -> SectDecisionResult:
        result = SectDecisionResult()

        recruit_cost = int(getattr(CONFIG.sect, "recruit_cost", 500))
        support_amount = int(getattr(CONFIG.sect, "support_amount", 300))
        plan = await cls._plan(sect, decision_context, world, recruit_cost=recruit_cost, support_amount=support_amount)

        await cls._process_recruitment(
            sect=sect,
            decision_context=decision_context,
            world=world,
            recruit_cost=recruit_cost,
            result=result,
            selected_ids=set(plan.recruit_avatar_ids) if plan is not None else None,
        )

        cls._process_members(
            sect=sect,
            world=world,
            support_amount=support_amount,
            result=result,
            expel_ids=set(plan.expel_avatar_ids) if plan is not None else None,
            reward_ids=set(plan.reward_avatar_ids) if plan is not None else None,
            support_ids=set(plan.support_avatar_ids) if plan is not None else None,
        )

        result.summary_text = cls._build_summary(sect, result)
        return result

    @classmethod
    async def _plan(
        cls,
        sect: "Sect",
        decision_context: "SectDecisionContext",
        world: "World",
        *,
        recruit_cost: int,
        support_amount: int,
    ) -> SectDecisionPlan | None:
        if not cls._llm_available():
            return None

        infos = {
            "sect_name": sect.name,
            "world_info": to_json_str_with_intent(cls._serialize_world_info(world)),
            "decision_context_info": to_json_str_with_intent(cls._serialize_context(decision_context)),
            "recruit_cost": recruit_cost,
            "support_amount": support_amount,
        }

        try:
            result = await call_llm_with_task_name(
                task_name="sect_decider",
                template_path=cls._resolve_template_path(),
                infos=infos,
            )
            return cls._parse_plan(result, decision_context)
        except (LLMError, ParseError, Exception):
            return None

    @classmethod
    def _llm_available(cls) -> bool:
        llm_conf = getattr(CONFIG, "llm", None)
        if llm_conf is None:
            return False
        return bool(
            getattr(llm_conf, "base_url", "")
            and getattr(llm_conf, "key", "")
            and getattr(llm_conf, "model_name", "")
        )

    @classmethod
    def _resolve_template_path(cls) -> Path:
        lang = str(language_manager)
        path = Path(f"static/locales/{lang}/templates/sect_decider.txt")
        if path.exists():
            return path
        return Path("static/locales/zh-CN/templates/sect_decider.txt")

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
    def _serialize_context(cls, ctx: "SectDecisionContext") -> dict[str, Any]:
        return {
            "basic_structured": dict(ctx.basic_structured),
            "basic_text": ctx.basic_text,
            "power": dict(ctx.power),
            "territory": dict(ctx.territory),
            "economy": dict(ctx.economy),
            "rule": dict(ctx.rule),
            "recruitment_candidates": list(ctx.recruitment_candidates),
            "member_candidates": list(ctx.member_candidates),
            "relations": list(ctx.relations),
            "relations_summary": ctx.relations_summary,
            "history": {
                "summary_text": str(ctx.history.get("summary_text", "")),
            },
        }

    @classmethod
    def _parse_plan(
        cls,
        payload: dict[str, Any] | Any,
        decision_context: "SectDecisionContext",
    ) -> SectDecisionPlan | None:
        if not isinstance(payload, dict):
            return None

        recruit_valid = {str(item["avatar_id"]) for item in decision_context.recruitment_candidates}
        member_valid = {str(item["avatar_id"]) for item in decision_context.member_candidates}

        def _pick_ids(key: str, valid_ids: set[str]) -> list[str]:
            raw = payload.get(key, [])
            if not isinstance(raw, list):
                return []
            deduped: list[str] = []
            seen: set[str] = set()
            for item in raw:
                value = str(item)
                if value in valid_ids and value not in seen:
                    seen.add(value)
                    deduped.append(value)
            return deduped

        return SectDecisionPlan(
            recruit_avatar_ids=_pick_ids("recruit_avatar_ids", recruit_valid),
            expel_avatar_ids=_pick_ids("expel_avatar_ids", member_valid),
            reward_avatar_ids=_pick_ids("reward_avatar_ids", member_valid),
            support_avatar_ids=_pick_ids("support_avatar_ids", member_valid),
            thinking=str(payload.get("thinking", "") or ""),
        )

    @classmethod
    async def _process_recruitment(
        cls,
        *,
        sect: "Sect",
        decision_context: "SectDecisionContext",
        world: "World",
        recruit_cost: int,
        result: SectDecisionResult,
        selected_ids: set[str] | None,
    ) -> None:
        avatars = getattr(getattr(world, "avatar_manager", None), "avatars", {}) or {}
        for candidate in decision_context.recruitment_candidates:
            if selected_ids is not None and candidate["avatar_id"] not in selected_ids:
                continue
            if int(getattr(sect, "magic_stone", 0)) < recruit_cost:
                break
            if not candidate.get("alignment_recruitable", False):
                continue

            avatar = avatars.get(candidate["avatar_id"])
            if avatar is None or getattr(avatar, "is_dead", False):
                continue
            if getattr(avatar, "sect", None) is not None:
                continue

            outcome = await resolve_sect_recruitment(
                SectRecruitmentRequest(
                    sect=sect,
                    avatar=avatar,
                    cost=recruit_cost,
                )
            )
            result.events.append(
                Event(
                    month_stamp=world.month_stamp,
                    content=outcome.result_text,
                    related_avatars=[avatar.id],
                    related_sects=[int(sect.id)],
                    is_major=False,
                )
            )

            if not outcome.accepted:
                continue
            if int(getattr(sect, "magic_stone", 0)) < recruit_cost:
                continue

            sect.magic_stone -= recruit_cost
            avatar.join_sect(sect, get_rank_from_realm(avatar.cultivation_progress.realm))
            result.recruitment_count += 1
            result.events.append(
                Event(
                    month_stamp=world.month_stamp,
                    content=f"{sect.name} 花费 {recruit_cost} 灵石招徕 {avatar.name} 入门，{avatar.name} 正式成为本宗弟子。",
                    related_avatars=[avatar.id],
                    related_sects=[int(sect.id)],
                    is_major=True,
                )
            )

    @classmethod
    def _process_members(
        cls,
        *,
        sect: "Sect",
        world: "World",
        support_amount: int,
        result: SectDecisionResult,
        expel_ids: set[str] | None,
        reward_ids: set[str] | None,
        support_ids: set[str] | None,
    ) -> None:
        for avatar in list(getattr(sect, "members", {}).values()):
            if getattr(avatar, "is_dead", False):
                continue

            avatar_id = str(getattr(avatar, "id", ""))

            if sect.is_member_rule_breaker(avatar) and (expel_ids is None or avatar_id in expel_ids):
                avatar.leave_sect()
                result.expulsion_count += 1
                result.events.append(
                    Event(
                        month_stamp=world.month_stamp,
                        content=f"{sect.name} 认定 {avatar.name} 严重违背门规，将其逐出宗门。",
                        related_avatars=[avatar.id],
                        related_sects=[int(sect.id)],
                        is_major=True,
                    )
                )
                continue

            reward_technique = cls._pick_reward_technique(sect, avatar)
            if (
                reward_ids is None or avatar_id in reward_ids
            ) and reward_technique is not None and cls._can_replace_technique(avatar, reward_technique):
                avatar.technique = reward_technique
                result.technique_reward_count += 1
                result.events.append(
                    Event(
                        month_stamp=world.month_stamp,
                        content=f"{sect.name} 赐予 {avatar.name} 功法《{reward_technique.name}》。",
                        related_avatars=[avatar.id],
                        related_sects=[int(sect.id)],
                        is_major=True,
                    )
                )

            if support_ids is not None and avatar_id not in support_ids:
                continue
            if int(getattr(sect, "magic_stone", 0)) < support_amount:
                continue
            current_stones = int(getattr(getattr(avatar, "magic_stone", None), "value", 0))
            if current_stones >= support_amount:
                continue

            sect.magic_stone -= support_amount
            avatar.magic_stone += support_amount
            result.support_count += 1
            result.events.append(
                Event(
                    month_stamp=world.month_stamp,
                    content=f"{sect.name} 资助 {avatar.name} {support_amount} 灵石，以助其修行。",
                    related_avatars=[avatar.id],
                    related_sects=[int(sect.id)],
                    is_major=False,
                )
            )

    @classmethod
    def _pick_reward_technique(cls, sect: "Sect", avatar: "Avatar") -> Technique | None:
        candidates: list[Technique] = []
        for technique_name in getattr(sect, "technique_names", []) or []:
            technique = techniques_by_name.get(technique_name)
            if technique is None:
                continue
            if not technique.is_allowed_for(avatar):
                continue
            if technique.attribute == TechniqueAttribute.EVIL and getattr(avatar, "alignment", None) != Alignment.EVIL:
                continue
            if not is_attribute_compatible_with_root(technique.attribute, avatar.root):
                continue
            candidates.append(technique)

        if not candidates:
            return None
        return random.choice(candidates)

    @classmethod
    def _grade_rank(cls, technique: Technique | None) -> int:
        grade = getattr(getattr(technique, "grade", None), "value", "")
        order = {"LOWER": 1, "MIDDLE": 2, "UPPER": 3}
        return order.get(str(grade), 0)

    @classmethod
    def _can_replace_technique(cls, avatar: "Avatar", new_technique: Technique) -> bool:
        current_technique = getattr(avatar, "technique", None)
        return cls._grade_rank(current_technique) <= cls._grade_rank(new_technique)

    @classmethod
    def _build_summary(cls, sect: "Sect", result: SectDecisionResult) -> str:
        parts = []
        if result.recruitment_count:
            parts.append(f"招徕散修 {result.recruitment_count} 人")
        if result.expulsion_count:
            parts.append(f"驱逐门人 {result.expulsion_count} 人")
        if result.technique_reward_count:
            parts.append(f"赐下功法 {result.technique_reward_count} 次")
        if result.support_count:
            parts.append(f"资助灵石 {result.support_count} 次")
        if not parts:
            return f"{sect.name} 本轮五年决策以观望整固为主，未作实质处分。"
        return f"{sect.name} 本轮五年决策：" + "，".join(parts) + "。"
