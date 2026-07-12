from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationPhase:
    name: str
    index: int
    reset_check_after: bool = True


SIMULATION_PHASES: tuple[SimulationPhase, ...] = (
    SimulationPhase("update_perception_and_knowledge", 1),
    SimulationPhase("long_term_objective_thinking", 2),
    SimulationPhase("process_gatherings", 3),
    SimulationPhase("decide_actions", 4),
    SimulationPhase("commit_next_plans", 5),
    SimulationPhase("execute_actions", 6),
    SimulationPhase("check_opportunities", 7),
    SimulationPhase("world_secret_discovery", 8),
    SimulationPhase("handle_interactions_first", 9),
    SimulationPhase("evolve_relations", 10),
    SimulationPhase("resolve_death", 11),
    SimulationPhase("update_age_and_birth", 12),
    SimulationPhase("backstory_generation", 13),
    SimulationPhase("passive_effects", 14),
    SimulationPhase("autonomous_custom_creation", 15),
    SimulationPhase("random_minor_events", 16),
    SimulationPhase("sect_random_event", 17),
    SimulationPhase("sect_wars", 18),
    SimulationPhase("nickname_generation", 19),
    SimulationPhase("update_celestial_phenomenon", 20),
    SimulationPhase("update_city_population", 21),
    SimulationPhase("update_dynasty_and_officials", 22),
    SimulationPhase("handle_interactions_second", 23),
    SimulationPhase("update_calculated_relations", 24),
    SimulationPhase("annual_maintenance", 25),
    SimulationPhase("finalize_step", 26, reset_check_after=False),
)


def get_simulation_phases() -> tuple[SimulationPhase, ...]:
    return SIMULATION_PHASES
