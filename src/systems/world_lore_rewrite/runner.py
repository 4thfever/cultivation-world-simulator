from __future__ import annotations

import asyncio
import time
from dataclasses import replace
from typing import Any

from src.config import get_settings_service
from src.run.log import get_logger
from src.utils.llm.client import call_llm_with_task_name
from src.utils.llm.exceptions import LLMError

from .fallback import build_fallback_style_guide, fallback_job
from .models import RewriteJob, WorldLoreRewriteContext, WorldLoreRewriteDraft
from .planner import build_world_lore_jobs
from .prompts import build_rewrite_infos, build_style_guide_infos, resolve_world_lore_template
from .validation import (
    WorldLoreValidationError,
    draft_from_validated_job,
    validate_job_result,
)


class WorldLoreRewriteRunner:
    def __init__(self, context: WorldLoreRewriteContext):
        self.context = context
        self.logger = get_logger().logger
        self._completed_job_ids: set[str] = set()
        self._fallback_job_ids: set[str] = set()

    async def run(self) -> WorldLoreRewriteDraft:
        started_at = time.monotonic()
        total_deadline = started_at + self.context.config.total_timeout_seconds
        style_guide = await self._generate_style_guide(total_deadline)
        context = replace(self.context, style_guide=style_guide)
        jobs = build_world_lore_jobs(context)
        self.logger.info(
            "[WorldLore] planned jobs: %s",
            self._format_job_counts(jobs),
        )

        draft = WorldLoreRewriteDraft()
        pending_window = self._get_pending_window()

        for batch_start in range(0, len(jobs), pending_window):
            if time.monotonic() >= total_deadline:
                break
            batch = jobs[batch_start:batch_start + pending_window]
            results = await asyncio.gather(
                *[self._run_job(job, total_deadline) for job in batch],
                return_exceptions=False,
            )
            for partial in results:
                draft.merge(partial)

        for job in jobs:
            if job.id in self._completed_job_ids:
                continue
            partial = fallback_job(job)
            self._fallback_job_ids.add(job.id)
            draft.merge(partial)

        draft.elapsed_seconds = round(time.monotonic() - started_at, 2)
        self.logger.info(
            "[WorldLore] rewrite complete: llm=%s fallback=%s elapsed=%ss",
            draft.llm_count,
            draft.fallback_count,
            draft.elapsed_seconds,
        )
        return draft

    async def _generate_style_guide(self, total_deadline: float) -> dict[str, Any]:
        remaining = total_deadline - time.monotonic()
        if remaining <= 1:
            return build_fallback_style_guide(self.context.lore_text)

        timeout = min(20.0, remaining, self.context.config.task_timeout_seconds)
        try:
            result = await asyncio.wait_for(
                call_llm_with_task_name(
                    task_name="world_lore_style_guide",
                    template_path=resolve_world_lore_template("world_lore_style_guide.txt"),
                    infos=build_style_guide_infos(self.context.lore_text),
                    max_retries=0,
                ),
                timeout=timeout,
            )
            if isinstance(result, dict) and result:
                self.logger.info("[WorldLore] style guide done")
                return result
        except Exception as exc:
            self.logger.warning("[WorldLore] style guide failed, fallback applied: %s", exc)
        return build_fallback_style_guide(self.context.lore_text)

    async def _run_job(self, job: RewriteJob, total_deadline: float) -> WorldLoreRewriteDraft:
        job_started_at = time.monotonic()
        job_deadline = min(
            job_started_at + self.context.config.task_timeout_seconds,
            total_deadline,
        )
        previous_error = ""

        for attempt in range(self.context.config.max_parse_retries + 1):
            remaining = job_deadline - time.monotonic()
            if remaining <= 0:
                break
            if attempt > 0 and remaining < self.context.config.min_retry_budget_seconds:
                break
            try:
                result = await asyncio.wait_for(
                    call_llm_with_task_name(
                        task_name=job.task_name,
                        template_path=resolve_world_lore_template("world_lore_rewrite_entities.txt"),
                        infos=build_rewrite_infos(job, previous_error=previous_error),
                        max_retries=0,
                    ),
                    timeout=remaining,
                )
                validated = validate_job_result(job, result, source="llm")
                partial = draft_from_validated_job(job, validated)
                self._completed_job_ids.add(job.id)
                self.logger.info("[WorldLore] job %s done in %.1fs", job.id, time.monotonic() - job_started_at)
                return partial
            except (LLMError, WorldLoreValidationError) as exc:
                previous_error = str(exc)
                if attempt < self.context.config.max_parse_retries:
                    self.logger.warning("[WorldLore] job %s parse/validation failed, retrying: %s", job.id, exc)
                    continue
                break
            except asyncio.TimeoutError:
                previous_error = "timeout"
                break
            except Exception as exc:
                previous_error = str(exc)
                break

        self.logger.warning("[WorldLore] job %s failed, fallback applied: %s", job.id, previous_error)
        self._completed_job_ids.add(job.id)
        self._fallback_job_ids.add(job.id)
        return fallback_job(job)

    def _get_pending_window(self) -> int:
        try:
            profile, _ = get_settings_service().get_llm_runtime_config()
            max_concurrent = int(getattr(profile, "max_concurrent_requests", 10) or 10)
        except Exception:
            max_concurrent = 10
        return max(8, max_concurrent * 2)

    @staticmethod
    def _format_job_counts(jobs: list[RewriteJob]) -> str:
        counts: dict[str, int] = {}
        for job in jobs:
            counts[job.kind] = counts.get(job.kind, 0) + 1
        return " ".join(f"{key}={value}" for key, value in sorted(counts.items()))
