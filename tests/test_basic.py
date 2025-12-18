from src.classes.avatar import Avatar
# test_basic is now simplified using fixtures
def test_basic(base_world, dummy_avatar):
    """
    测试整个基础代码能不能run起来
    使用 conftest.py 中的 fixtures 简化设置
    """
    # fixtures 已经创建了 map, world, avatar
    assert base_world.map.width == 10
    assert base_world.map.height == 10
    
    assert dummy_avatar.world == base_world
    assert dummy_avatar.age.age == 20
