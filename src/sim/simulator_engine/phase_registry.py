from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationPhase:
    name: str
    index: int
    handler_name: str | None = None
    reset_check_after: bool = True


SIMULATION_PHASES: tuple[SimulationPhase, ...] = (
    SimulationPhase("update_perception_and_knowledge", 1, "update_perception_and_knowledge"),
    SimulationPhase("long_term_objective_thinking", 2, "long_term_objective_thinking"),
    SimulationPhase("process_gatherings", 3, "process_gatherings"),
    SimulationPhase("decide_actions", 4, "decide_actions"),
    SimulationPhase("commit_next_plans", 5, "commit_next_plans"),
    SimulationPhase("execute_actions", 6, "execute_actions"),
    SimulationPhase("check_opportunities", 7, "check_opportunities"),
    SimulationPhase("world_secret_discovery", 8, "world_secret_discovery"),
    SimulationPhase("handle_interactions_first", 9, "handle_interactions"),
    SimulationPhase("evolve_relations", 10, "evolve_relations"),
    SimulationPhase("resolve_death", 11, "resolve_death"),
    SimulationPhase("update_age_and_birth", 12, "update_age_and_birth"),
    SimulationPhase("backstory_generation", 13, "backstory_generation"),
    SimulationPhase("passive_effects", 14, "passive_effects"),
    SimulationPhase("autonomous_custom_creation", 15, "autonomous_custom_creation"),
    SimulationPhase("random_minor_events", 16, "random_minor_events"),
    SimulationPhase("sect_random_event", 17, "sect_random_event"),
    SimulationPhase("sect_wars", 18, "sect_wars"),
    SimulationPhase("nickname_generation", 19, "nickname_generation"),
    SimulationPhase("update_celestial_phenomenon", 20, "update_celestial_phenomenon"),
    SimulationPhase("update_city_population", 21, "update_city_population"),
    SimulationPhase("update_dynasty_and_officials", 22, "update_dynasty_and_officials"),
    SimulationPhase("handle_interactions_second", 23, "handle_interactions"),
    SimulationPhase("update_calculated_relations", 24, "update_calculated_relations"),
    SimulationPhase("annual_maintenance", 25, "annual_maintenance"),
    SimulationPhase("finalize_step", 26, "finalize_step", reset_check_after=False),
)


def get_simulation_phases() -> tuple[SimulationPhase, ...]:
    return SIMULATION_PHASES
