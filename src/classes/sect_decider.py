from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from src.classes.alignment import Alignment
from src.classes.event import Event
from src.classes.sect_ranks import get_rank_from_realm
from src.config import get_settings_service
from src.i18n import t
from src.i18n.template_resolver import resolve_locale_template_path
from src.run.log import get_logger
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
    war_declared_count: int = 0
    peace_made_count: int = 0
    recruitment_count: int = 0
    expulsion_count: int = 0
    technique_reward_count: int = 0
    support_count: int = 0
    summary_text: str = ""


@dataclass(slots=True)
class SectDecisionPlan:
    declare_war_target_ids: list[int] = field(default_factory=list)
    seek_peace_target_ids: list[int] = field(default_factory=list)
    recruit_avatar_ids: list[str] = field(default_factory=list)
    expel_avatar_ids: list[str] = field(default_factory=list)
    reward_avatar_ids: list[str] = field(default_factory=list)
    support_avatar_ids: list[str] = field(default_factory=list)
    thinking: str = ""


class SectDecider:
    """
    按配置周期执行的宗门行政决策执行器。
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

        cls._process_diplomacy(
            sect=sect,
            decision_context=decision_context,
            world=world,
            result=result,
            declare_target_ids=set(plan.declare_war_target_ids) if plan is not None else set(),
            peace_target_ids=set(plan.seek_peace_target_ids) if plan is not None else set(),
        )

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
            cls._warn_plan_skip(sect, "LLM runtime config unavailable")
            return None

        infos = {
            "sect_name": sect.name,
            "world_info": to_json_str_with_intent(cls._serialize_world_info(world)),
            "decision_context_info": to_json_str_with_intent(cls._serialize_context(decision_context)),
            "decision_interval_years": int(getattr(CONFIG.sect, "decision_interval_years", 5)),
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
        except (LLMError, ParseError, Exception) as exc:
            cls._warn_plan_skip(sect, f"LLM plan failed: {exc}")
            return None

    @classmethod
    def _llm_available(cls) -> bool:
        profile, api_key = get_settings_service().get_llm_runtime_config()
        return bool(profile.base_url and api_key and profile.model_name)

    @classmethod
    def _warn_plan_skip(cls, sect: "Sect", reason: str) -> None:
        get_logger().logger.warning(
            "SectDecider using fallback execution for %s(%s): %s",
            getattr(sect, "name", "unknown"),
            getattr(sect, "id", "unknown"),
            reason,
        )

    @classmethod
    def _resolve_template_path(cls) -> Path:
        return resolve_locale_template_path(
            "sect_decider.txt",
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
    def _serialize_context(cls, ctx: "SectDecisionContext") -> dict[str, Any]:
        return {
            "basic_structured": dict(ctx.basic_structured),
            "basic_text": ctx.basic_text,
            "identity": dict(ctx.identity),
            "power": dict(ctx.power),
            "territory": dict(ctx.territory),
            "self_assessment": dict(ctx.self_assessment),
            "economy": dict(ctx.economy),
            "rule": dict(ctx.rule),
            "diplomacy_targets": list(ctx.diplomacy_targets),
            "active_wars": list(ctx.active_wars),
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
        diplomacy_valid = {int(item["other_sect_id"]) for item in decision_context.diplomacy_targets}

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

        def _pick_sect_ids(key: str) -> list[int]:
            raw = payload.get(key, [])
            if not isinstance(raw, list):
                return []
            deduped: list[int] = []
            seen: set[int] = set()
            for item in raw:
                try:
                    value = int(item)
                except (TypeError, ValueError):
                    continue
                if value in diplomacy_valid and value not in seen:
                    seen.add(value)
                    deduped.append(value)
            return deduped

        return SectDecisionPlan(
            declare_war_target_ids=_pick_sect_ids("declare_war_target_ids"),
            seek_peace_target_ids=_pick_sect_ids("seek_peace_target_ids"),
            recruit_avatar_ids=_pick_ids("recruit_avatar_ids", recruit_valid),
            expel_avatar_ids=_pick_ids("expel_avatar_ids", member_valid),
            reward_avatar_ids=_pick_ids("reward_avatar_ids", member_valid),
            support_avatar_ids=_pick_ids("support_avatar_ids", member_valid),
            thinking=str(payload.get("thinking", "") or ""),
        )

    @classmethod
    def _process_diplomacy(
        cls,
        *,
        sect: "Sect",
        decision_context: "SectDecisionContext",
        world: "World",
        result: SectDecisionResult,
        declare_target_ids: set[int],
        peace_target_ids: set[int],
    ) -> None:
        target_by_id = {
            int(item["other_sect_id"]): item
            for item in decision_context.diplomacy_targets
            if item.get("other_sect_id") is not None
        }

        for target_id in declare_target_ids:
            target = target_by_id.get(int(target_id))
            if target is None:
                continue
            if str(target.get("status", "")) == "war":
                continue
            world.declare_sect_war(
                sect_a_id=int(sect.id),
                sect_b_id=int(target_id),
                reason=str(target.get("other_sect_name", "") or ""),
            )
            result.war_declared_count += 1
            result.events.append(
                Event(
                    month_stamp=world.month_stamp,
                    content=t(
                        "{sect_name} declared war on {target_name}; from this point on, the two sects are at war.",
                        sect_name=sect.name,
                        target_name=target["other_sect_name"],
                    ),
                    related_sects=[int(sect.id), int(target_id)],
                    is_major=True,
                )
            )

        for target_id in peace_target_ids:
            target = target_by_id.get(int(target_id))
            if target is None:
                continue
            if str(target.get("status", "")) != "war":
                continue
            world.make_sect_peace(
                sect_a_id=int(sect.id),
                sect_b_id=int(target_id),
                reason=str(target.get("other_sect_name", "") or ""),
            )
            result.peace_made_count += 1
            result.events.append(
                Event(
                    month_stamp=world.month_stamp,
                    content=t(
                        "{sect_name} made peace with {target_name}, and the state of war between them came to an end.",
                        sect_name=sect.name,
                        target_name=target["other_sect_name"],
                    ),
                    related_sects=[int(sect.id), int(target_id)],
                    is_major=True,
                )
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
                    content=t(
                        "{sect_name} spent {cost} spirit stones to recruit {avatar_name}; {avatar_name} officially became a disciple of the sect.",
                        sect_name=sect.name,
                        cost=recruit_cost,
                        avatar_name=avatar.name,
                    ),
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
        sorted_members = sect.get_living_members_sorted_by_status()
        if support_ids is None:
            support_limit = max(1, int(getattr(CONFIG.sect, "support_top_n_per_cycle", 2) or 2))
            support_candidates = [
                avatar
                for avatar in sorted_members
                if int(getattr(getattr(avatar, "magic_stone", None), "value", 0)) < support_amount
            ]
            support_ids = {
                str(getattr(avatar, "id", ""))
                for avatar in support_candidates[:support_limit]
            }

        for avatar in sorted_members:
            if getattr(avatar, "is_dead", False):
                continue

            avatar_id = str(getattr(avatar, "id", ""))

            if sect.is_member_rule_breaker(avatar) and (expel_ids is None or avatar_id in expel_ids):
                avatar.leave_sect()
                result.expulsion_count += 1
                result.events.append(
                    Event(
                        month_stamp=world.month_stamp,
                        content=t(
                            "{sect_name} judged that {avatar_name} had gravely violated the sect rules and expelled them from the sect.",
                            sect_name=sect.name,
                            avatar_name=avatar.name,
                        ),
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
                        content=t(
                            "{sect_name} bestowed the technique \"{technique_name}\" upon {avatar_name}.",
                            sect_name=sect.name,
                            technique_name=reward_technique.name,
                            avatar_name=avatar.name,
                        ),
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
                    content=t(
                        "{sect_name} granted {amount} spirit stones to {avatar_name} in support of their cultivation.",
                        sect_name=sect.name,
                        amount=support_amount,
                        avatar_name=avatar.name,
                    ),
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
            parts.append(t("recruited {count} rogue cultivators", count=result.recruitment_count))
        if result.war_declared_count:
            parts.append(t("declared war {count} times", count=result.war_declared_count))
        if result.peace_made_count:
            parts.append(t("made peace {count} times", count=result.peace_made_count))
        if result.expulsion_count:
            parts.append(t("expelled {count} members", count=result.expulsion_count))
        if result.technique_reward_count:
            parts.append(t("bestowed techniques {count} times", count=result.technique_reward_count))
        if result.support_count:
            parts.append(t("granted spirit-stone support {count} times", count=result.support_count))
        if not parts:
            return t(
                "{sect_name} focused this round of sect decisions on consolidation and observation, with no major adjustments made.",
                sect_name=sect.name,
            )
        return t("{sect_name} this round of sect decisions:", sect_name=sect.name) + " " + "、".join(parts) + "。"
