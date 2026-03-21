from src.classes.core.dynasty import Dynasty, Emperor
from src.sim.simulator_engine.phases import world as world_phases
from src.systems.time import MonthStamp


def test_phase_update_dynasty_replaces_dead_emperor(base_world):
    base_world.dynasty = Dynasty(
        id=1,
        name="晋",
        desc="",
        royal_surname="司马",
        current_emperor=Emperor(
            surname="司马",
            given_name="承安",
            birth_month_stamp=int(base_world.month_stamp) - 80 * 12,
            max_age=80,
        ),
    )

    events = world_phases.phase_update_dynasty(base_world)

    assert len(events) == 2
    assert "驾崩" in events[0].content
    assert "新帝即位" in events[1].content
    assert base_world.dynasty.current_emperor is not None
    assert base_world.dynasty.current_emperor.name != "司马承安"
    assert base_world.dynasty.current_emperor.surname == "司马"
    assert 25 <= base_world.dynasty.current_emperor.max_age <= 90
    assert base_world.dynasty.current_emperor.get_age(int(base_world.month_stamp)) < base_world.dynasty.current_emperor.max_age


def test_phase_update_dynasty_generates_emperor_if_missing(base_world):
    base_world.dynasty = Dynasty(
        id=1,
        name="秦",
        desc="",
        royal_surname="上官",
    )

    events = world_phases.phase_update_dynasty(base_world)

    assert len(events) == 1
    assert "新君" in events[0].content
    assert base_world.dynasty.current_emperor is not None
    assert base_world.dynasty.current_emperor.surname == "上官"
