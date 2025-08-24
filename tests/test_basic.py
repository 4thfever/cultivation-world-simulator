import uuid
from src.classes.avatar import Avatar, Gender
from src.classes.calendar import Month, Year
from src.classes.world import World 
from src.classes.tile import Map, TileType
from src.classes.age import Age

def test_basic():
    """
    测试整个基础代码能不能run起来
    """
    map = Map(width=2, height=2)
    for x in range(2):
        for y in range(2):
            map.create_tile(x, y, TileType.PLAIN)

    world = World(map=map)

    avatar = Avatar(
        world=world,
        name="John Doe",
        id=str(uuid.uuid4()),
        birth_month=Month.JANUARY,
        birth_year=Year(2000),
        age=Age(20),
        gender=Gender.MALE
    )



