from pathlib import Path

from src.classes.core.dynasty import Dynasty, Emperor
from src.sim.simulator import Simulator
from src.sim.save.save_game import save_game
from src.sim.load.load_game import load_game


def test_save_and_load_preserves_dynasty(base_world, tmp_path):
    base_world.dynasty = Dynasty(
        id=2,
        name="宋",
        desc="重文轻武，典章繁密，民间书院兴盛。",
        royal_surname="上官",
        effect_desc="",
        effects={},
        current_emperor=Emperor(
            surname="上官",
            given_name="景天",
            birth_month_stamp=int(base_world.month_stamp) - 28 * 12,
            max_age=80,
        ),
    )

    simulator = Simulator(base_world)
    save_path = Path(tmp_path) / "dynasty_save.json"
    success, _ = save_game(base_world, simulator, existed_sects=[], save_path=save_path)

    assert success

    new_world, _new_sim, _new_sects = load_game(save_path)
    assert new_world.dynasty is not None
    assert new_world.dynasty.name == "宋"
    assert new_world.dynasty.royal_surname == "上官"
    assert new_world.dynasty.title == "宋朝"
    assert new_world.dynasty.current_emperor is not None
    assert new_world.dynasty.current_emperor.name == "上官景天"
