import pytest

from src.classes.action.devour_people import DevourPeople
from src.classes.action.help_people import HelpPeople
from src.classes.action.plunder_people import PlunderPeople
from src.classes.alignment import Alignment
from src.classes.environment.region import CityRegion
from src.classes.items.auxiliary import Auxiliary, get_ten_thousand_souls_banner_bonus
from src.classes.environment.tile import Tile, TileType
from src.sim.simulator import Simulator
from src.sim.simulator_engine.phases.world import phase_update_city_population


class TestCityPopulation:
    def test_region_initial_population(self):
        region = CityRegion(id=1, name="TestCity", desc="Test")
        assert region.population == 80.0
        assert region.population_capacity == 120.0

    def test_change_population_bounds(self):
        region = CityRegion(
            id=1,
            name="TestCity",
            desc="Test",
            population=40.0,
            population_capacity=100.0,
        )

        region.change_population(10.0)
        assert region.population == 50.0

        region.change_population(100.0)
        assert region.population == 100.0

        region.change_population(-40.0)
        assert region.population == 60.0

        region.change_population(-100.0)
        assert region.population == 0.0

    def test_help_people_increases_population(self, avatar_in_city):
        region = avatar_in_city.tile.region
        initial_population = region.population
        avatar_in_city.magic_stone = 100
        initial_stone = avatar_in_city.magic_stone

        action = HelpPeople(avatar_in_city, avatar_in_city.world)
        action.start()
        import asyncio
        asyncio.run(action.finish())

        assert region.population == pytest.approx(initial_population + 1.8)
        assert avatar_in_city.magic_stone == initial_stone - 45
        assert avatar_in_city.luck == pytest.approx(0.3)

    def test_plunder_people_decreases_population(self, avatar_in_city):
        region = avatar_in_city.tile.region
        initial_population = region.population
        initial_stone = avatar_in_city.magic_stone
        avatar_in_city.alignment = Alignment.EVIL

        action = PlunderPeople(avatar_in_city, avatar_in_city.world)
        import asyncio
        asyncio.run(action.finish())

        assert region.population == pytest.approx(initial_population - 3.0)
        assert avatar_in_city.magic_stone == initial_stone + 90
        assert avatar_in_city.luck == pytest.approx(-0.3)

    def test_devour_people_decreases_population(self, avatar_in_city):
        region = avatar_in_city.tile.region
        initial_population = region.population

        aux = Auxiliary(id=999, name="万魂幡", realm=None, desc="Test")
        aux.special_data = {"devoured_souls": 0}
        avatar_in_city.auxiliary = aux

        action = DevourPeople(avatar_in_city, avatar_in_city.world)
        import asyncio
        asyncio.run(action.finish())

        assert region.population == pytest.approx(initial_population * 0.99)
        assert avatar_in_city.auxiliary.special_data["devoured_souls"] == 8000
        assert avatar_in_city.luck == pytest.approx(-1.0)

    def test_ten_thousand_souls_banner_bonus_curve(self):
        assert get_ten_thousand_souls_banner_bonus(0) == 0
        assert get_ten_thousand_souls_banner_bonus(1000) == 1
        assert get_ten_thousand_souls_banner_bonus(3000) == 2
        assert get_ten_thousand_souls_banner_bonus(7000) == 3
        assert get_ten_thousand_souls_banner_bonus(15000) == 4
        assert get_ten_thousand_souls_banner_bonus(30000) == 5
        assert get_ten_thousand_souls_banner_bonus(50000) == 6
        assert get_ten_thousand_souls_banner_bonus(70000) == 7
        assert get_ten_thousand_souls_banner_bonus(90000) == 8

    def test_simulator_population_growth_uses_logistic_curve(self, base_world):
        city = CityRegion(
            id=1,
            name="TestCity",
            desc="Test",
            population=40.0,
            population_capacity=100.0,
        )

        tile = Tile(0, 0, TileType.CITY)
        tile.region = city
        base_world.map.tiles[(0, 0)] = tile
        base_world.map.regions[1] = city

        phase_update_city_population(base_world)

        expected = 40.0 + 0.03 * 40.0 * (1 - 40.0 / 100.0)
        assert city.population == pytest.approx(expected)

    def test_simulator_population_growth_stops_at_capacity(self, base_world):
        city = CityRegion(
            id=1,
            name="TestCity",
            desc="Test",
            population=100.0,
            population_capacity=100.0,
        )

        tile = Tile(0, 0, TileType.CITY)
        tile.region = city
        base_world.map.tiles[(0, 0)] = tile
        base_world.map.regions[1] = city

        phase_update_city_population(base_world)
        assert city.population == 100.0

    def test_save_load_population(self, base_world, tmp_path):
        from src.sim.load.load_game import load_game
        from src.sim.save.save_game import save_game

        sim = Simulator(base_world)

        city = CityRegion(
            id=999,
            name="SaveLoadCity",
            desc="Test",
            population=88.8,
            population_capacity=120.0,
        )

        tile = Tile(0, 0, TileType.CITY)
        tile.region = city
        base_world.map.tiles[(0, 0)] = tile
        base_world.map.regions[999] = city

        save_path = tmp_path / "test_city_population_save.json"
        success, _ = save_game(base_world, sim, [], save_path=save_path)
        assert success

        with pytest.MonkeyPatch.context() as m:
            from src.classes.environment.map import Map

            empty_map = Map(10, 10)
            new_city = CityRegion(id=999, name="SaveLoadCity", desc="Test")
            new_tile = Tile(0, 0, TileType.CITY)
            new_tile.region = new_city
            empty_map.tiles[(0, 0)] = new_tile
            empty_map.regions[999] = new_city

            m.setattr("src.run.load_map.load_cultivation_world_map", lambda: empty_map)

            loaded_world, _, _ = load_game(save_path)

            loaded_city = loaded_world.map.regions[999]
            assert loaded_city.population == pytest.approx(88.8)
