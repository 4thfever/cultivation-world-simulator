import pytest

from src.classes.action.eat_mortals import EatMortals
from src.classes.action.rest import Rest
from src.classes.alignment import Alignment
from src.classes.race import get_race


@pytest.mark.asyncio
async def test_turtle_rest_recovers_hp_and_gains_exp(avatar_in_city):
    avatar_in_city.race = get_race("turtle")
    avatar_in_city.personas = []
    avatar_in_city.technique = None
    avatar_in_city.hp.cur = max(1, avatar_in_city.hp.cur - 50)
    old_hp = avatar_in_city.hp.cur
    old_exp = avatar_in_city.cultivation_progress.exp
    avatar_in_city.recalc_effects()

    action = Rest(avatar_in_city, avatar_in_city.world)
    ok, reason = action.can_start()
    assert ok, reason

    events = await action.finish()

    assert avatar_in_city.hp.cur > old_hp
    assert avatar_in_city.cultivation_progress.exp > old_exp
    assert "修为经验" in events[0].content


@pytest.mark.asyncio
async def test_human_rest_does_not_gain_exp(avatar_in_city):
    avatar_in_city.race = get_race("human")
    avatar_in_city.personas = []
    avatar_in_city.technique = None
    avatar_in_city.recalc_effects()
    old_exp = avatar_in_city.cultivation_progress.exp

    await Rest(avatar_in_city, avatar_in_city.world).finish()

    assert avatar_in_city.cultivation_progress.exp == old_exp


@pytest.mark.asyncio
async def test_wolf_eat_mortals_reduces_population_and_gains_exp(avatar_in_city):
    avatar_in_city.race = get_race("wolf")
    avatar_in_city.alignment = Alignment.EVIL
    avatar_in_city.personas = []
    avatar_in_city.technique = None
    avatar_in_city.recalc_effects()
    region = avatar_in_city.tile.region
    old_population = region.population
    old_exp = avatar_in_city.cultivation_progress.exp

    action = EatMortals(avatar_in_city, avatar_in_city.world)
    ok, reason = action.can_start()
    assert ok, reason
    events = await action.finish()

    assert region.population < old_population
    assert avatar_in_city.cultivation_progress.exp > old_exp
    assert "吃掉" in events[0].content


def test_eat_mortals_blocks_human_and_righteous_yao(avatar_in_city):
    avatar_in_city.race = get_race("human")
    avatar_in_city.alignment = Alignment.EVIL
    ok, _reason = EatMortals(avatar_in_city, avatar_in_city.world).can_start()
    assert ok is False

    avatar_in_city.race = get_race("snake")
    avatar_in_city.alignment = Alignment.RIGHTEOUS
    ok, _reason = EatMortals(avatar_in_city, avatar_in_city.world).can_start()
    assert ok is False
