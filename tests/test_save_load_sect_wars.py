from pathlib import Path

from src.run.data_loader import reload_all_static_data
from src.classes.core.sect import sects_by_id
from src.sim.simulator import Simulator
from src.sim.save.save_game import save_game
from src.sim.load.load_game import load_game


def test_save_and_load_preserves_sect_wars(base_world, tmp_path):
    existed_sects = list(sects_by_id.values())[:2]
    assert len(existed_sects) == 2

    base_world.existed_sects = existed_sects
    base_world.sect_context.from_existed_sects(existed_sects)
    base_world.declare_sect_war(sect_a_id=existed_sects[0].id, sect_b_id=existed_sects[1].id, reason="test")
    existed_sects[0].set_war_weariness(34)
    existed_sects[1].set_war_weariness(7)

    simulator = Simulator(base_world)
    save_path = Path(tmp_path) / "sect_war_save.json"
    success, _ = save_game(base_world, simulator, existed_sects, save_path=save_path)

    assert success

    new_world, _new_sim, _new_sects = load_game(save_path)
    assert new_world.are_sects_at_war(existed_sects[0].id, existed_sects[1].id)
    assert _new_sects[0].war_weariness == 34
    assert _new_sects[1].war_weariness == 7


def test_save_and_load_preserves_sect_runtime_state_after_static_reload(base_world, tmp_path):
    existed_sects = list(sects_by_id.values())[:1]
    assert len(existed_sects) == 1

    base_world.existed_sects = existed_sects
    base_world.sect_context.from_existed_sects(existed_sects)

    sect = existed_sects[0]
    sect.magic_stone = 1234
    sect.periodic_thinking = "我宗当先固守山门，再图远交近攻。"
    sect.last_decision_summary = "本轮招徕散修 1 人。"
    sect.is_active = False
    sect.set_war_weariness(19)

    simulator = Simulator(base_world)
    save_path = Path(tmp_path) / "sect_runtime_state_save.json"
    success, _ = save_game(base_world, simulator, existed_sects, save_path=save_path)

    assert success

    reload_all_static_data()

    new_world, _new_sim, _new_sects = load_game(save_path)
    assert len(_new_sects) == 1
    loaded_sect = _new_sects[0]
    assert loaded_sect.magic_stone == 1234
    assert loaded_sect.periodic_thinking == "我宗当先固守山门，再图远交近攻。"
    assert loaded_sect.last_decision_summary == "本轮招徕散修 1 人。"
    assert loaded_sect.is_active is False
    assert loaded_sect.war_weariness == 19
    assert int(new_world.existed_sects[0].id) == int(loaded_sect.id)
