from __future__ import annotations

from .base import LoadContext


class SimulatorLoadSection:
    key = "simulator"

    def load(self, context: LoadContext) -> None:
        from src.sim.simulator import Simulator

        world = context.world
        run_config_snapshot = context.run_config_snapshot or {}

        world.run_config_snapshot = run_config_snapshot

        simulator_data = context.save_data.get("simulator", {})
        simulator = Simulator(world)
        simulator.awakening_rate = simulator_data.get(
            "awakening_rate",
            simulator_data.get(
                "birth_rate",
                run_config_snapshot.get("npc_awakening_rate_per_month", 0.01),
            ),
        )
        context.simulator = simulator
