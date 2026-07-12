from __future__ import annotations

import inspect
from typing import Any, Callable

from .context import SimulationStepContext
from .finalizer import finalize_step
from .phase_registry import SimulationPhase, get_simulation_phases
from .phases import actions, annual, lifecycle, sect_war, social, world as world_phases


class SimulationStepAborted(Exception):
    """Raised internally when a lifecycle command supersedes the current step."""


class SimulationPhaseRunner:
    def __init__(self, simulator: Any, phases: tuple[SimulationPhase, ...] | None = None):
        self.simulator = simulator
        self.world = simulator.world
        self.phases = phases or get_simulation_phases()
        self.handlers: dict[str, Callable[[SimulationStepContext], Any]] = {
            "update_perception_and_knowledge": self.update_perception_and_knowledge,
            "long_term_objective_thinking": self.long_term_objective_thinking,
            "process_gatherings": self.process_gatherings,
            "decide_actions": self.decide_actions,
            "commit_next_plans": self.commit_next_plans,
            "execute_actions": self.execute_actions,
            "check_opportunities": self.check_opportunities,
            "world_secret_discovery": self.world_secret_discovery,
            "handle_interactions": self.handle_interactions,
            "evolve_relations": self.evolve_relations,
            "resolve_death": self.resolve_death,
            "update_age_and_birth": self.update_age_and_birth,
            "backstory_generation": self.backstory_generation,
            "passive_effects": self.passive_effects,
            "autonomous_custom_creation": self.autonomous_custom_creation,
            "random_minor_events": self.random_minor_events,
            "sect_random_event": self.sect_random_event,
            "sect_wars": self.sect_wars,
            "nickname_generation": self.nickname_generation,
            "update_celestial_phenomenon": self.update_celestial_phenomenon,
            "update_city_population": self.update_city_population,
            "update_dynasty_and_officials": self.update_dynasty_and_officials,
            "update_calculated_relations": self.update_calculated_relations,
            "annual_maintenance": self.annual_maintenance,
            "finalize_step": self.finalize_step,
        }

    def raise_if_reset_requested(self) -> None:
        runtime = getattr(self.world, "runtime", None)
        if runtime is not None and getattr(runtime, "is_reset_requested", lambda: False)():
            raise SimulationStepAborted()

    async def run(self) -> list[Any]:
        ctx = SimulationStepContext.create(self.world)
        try:
            self.raise_if_reset_requested()
            for phase in self.phases:
                handler_name = phase.handler_name or phase.name
                handler = self.handlers[handler_name]
                result = handler(ctx)
                if inspect.isawaitable(result):
                    result = await result
                if phase.reset_check_after:
                    self.raise_if_reset_requested()
                if phase.name == "finalize_step":
                    return result or []
            return []
        except SimulationStepAborted:
            return []

    def update_perception_and_knowledge(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(world_phases.phase_update_perception_and_knowledge(self.world, ctx.living_avatars))

    async def long_term_objective_thinking(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(await lifecycle.phase_long_term_objective_thinking(ctx.living_avatars))

    async def process_gatherings(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(await world_phases.phase_process_gatherings(self.world))

    async def decide_actions(self, ctx: SimulationStepContext) -> None:
        await actions.phase_decide_actions(self.world, ctx.living_avatars)

    def commit_next_plans(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(actions.phase_commit_next_plans(ctx.living_avatars))

    async def execute_actions(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(await actions.phase_execute_actions(ctx.living_avatars))

    async def check_opportunities(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(await world_phases.phase_check_opportunities(self.world, ctx.living_avatars))

    async def world_secret_discovery(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(await world_phases.phase_world_secret_discovery(self.world, ctx.living_avatars))

    def handle_interactions(self, ctx: SimulationStepContext) -> None:
        social.phase_handle_interactions(self.world.avatar_manager, ctx.events, ctx.processed_event_ids)

    async def evolve_relations(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(await social.phase_evolve_relations(self.world.avatar_manager, ctx.living_avatars))

    def resolve_death(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(lifecycle.phase_resolve_death(self.world, ctx.living_avatars))

    def update_age_and_birth(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(lifecycle.phase_update_age_and_birth(self.world, ctx.living_avatars))

    async def backstory_generation(self, ctx: SimulationStepContext) -> None:
        await lifecycle.phase_backstory_generation(ctx.living_avatars)

    async def passive_effects(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(await world_phases.phase_passive_effects(self.world, ctx.living_avatars))

    async def autonomous_custom_creation(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(await world_phases.phase_autonomous_custom_creation(self.world, ctx.living_avatars))

    async def random_minor_events(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(await world_phases.phase_random_minor_events(self.world, ctx.living_avatars))

    async def sect_random_event(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(await world_phases.phase_sect_random_event(self.world))

    async def sect_wars(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(await sect_war.phase_handle_sect_wars(self.simulator, ctx.living_avatars))

    async def nickname_generation(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(await lifecycle.phase_nickname_generation(ctx.living_avatars))

    def update_celestial_phenomenon(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(world_phases.phase_update_celestial_phenomenon(self.world))

    def update_city_population(self, _ctx: SimulationStepContext) -> None:
        world_phases.phase_update_city_population(self.world)

    def update_dynasty_and_officials(self, ctx: SimulationStepContext) -> None:
        ctx.add_events(world_phases.phase_update_dynasty(self.world))
        ctx.add_events(world_phases.phase_update_official_system(self.world, ctx.living_avatars))

    def update_calculated_relations(self, ctx: SimulationStepContext) -> None:
        social.phase_update_calculated_relations(self.world, ctx.living_avatars)

    async def annual_maintenance(self, ctx: SimulationStepContext) -> None:
        await annual.run_annual_maintenance(self.simulator, ctx)

    def finalize_step(self, ctx: SimulationStepContext) -> list[Any]:
        return finalize_step(ctx)
