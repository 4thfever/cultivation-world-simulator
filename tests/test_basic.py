from src.utils.id_generator import get_avatar_id
from src.classes.avatar import Avatar, Gender
from src.classes.calendar import Month, Year, MonthStamp, create_month_stamp
from src.classes.world import World 
from src.classes.tile import Map, TileType
from src.classes.age import Age
from src.classes.cultivation import Realm
from src.utils.names import get_random_name

def test_basic():
    """
    测试整个基础代码能不能run起来
    """
    map = Map(width=2, height=2)
    for x in range(2):
        for y in range(2):
            map.create_tile(x, y, TileType.PLAIN)

    world = World(map=map, month_stamp=create_month_stamp(Year(1), Month.JANUARY))

    avatar = Avatar(
        world=world,
        name=get_random_name(Gender.MALE),
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.MALE
    )



