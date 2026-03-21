from src.classes.core.dynasty import dynasties_by_id
from src.systems.dynasty_generator import generate_dynasty


def test_generate_dynasty_returns_runtime_dynasty():
    dynasty = generate_dynasty()
    template = dynasties_by_id[dynasty.id]

    assert dynasty.id in dynasties_by_id
    assert dynasty.name == template.name
    assert dynasty.royal_surname
    assert dynasty.title == f"{dynasty.name}朝"
    assert dynasty.royal_house_name.endswith("氏")
    assert dynasty.is_low_magic is True
    assert dynasty.effects == template.effects
    assert dynasty.effects is not template.effects
