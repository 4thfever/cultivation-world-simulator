import pytest
from unittest.mock import MagicMock

from src.classes.map import Map
from src.classes.tile import TileType
from src.classes.world import World
from src.classes.calendar import Month, Year, create_month_stamp
from src.classes.avatar import Avatar, Gender
from src.classes.age import Age
from src.classes.cultivation import Realm
from src.utils.id_generator import get_avatar_id
from src.classes.name import get_random_name

@pytest.fixture
def base_map():
    """创建一个 10x10 的全平原地图"""
    width, height = 10, 10
    game_map = Map(width=width, height=height)
    for x in range(width):
        for y in range(height):
            game_map.create_tile(x, y, TileType.PLAIN)
    return game_map

@pytest.fixture
def base_world(base_map):
    """创建一个基于 base_map 的世界，时间为 Year 1, Jan"""
    return World(map=base_map, month_stamp=create_month_stamp(Year(1), Month.JANUARY))

from src.classes.root import Root
from src.classes.alignment import Alignment

@pytest.fixture
def dummy_avatar(base_world):
    """创建一个位于 (0,0) 的标准男性练气期角色"""
    # 确保ID生成器重置或不冲突 (get_avatar_id 是随机UUID通常没问题)
    av = Avatar(
        world=base_world,
        name="TestDummy",
        id=get_avatar_id(),
        birth_month_stamp=create_month_stamp(Year(2000), Month.JANUARY),
        age=Age(20, Realm.Qi_Refinement),
        gender=Gender.MALE,
        pos_x=0,
        pos_y=0,
        root=Root.GOLD, # 固定灵根
        personas=[],    # 清空特质，避免随机效果
        alignment=Alignment.RIGHTEOUS # 固定阵营
    )
    
    # 赋予一个 Mock 武器，防止 get_avatar_info 报错
    av.weapon = MagicMock()
    av.weapon.get_detailed_info.return_value = "测试木剑（练气）"
    av.weapon_proficiency = 0.0

    # 强制清空特质（因为 __post_init__ 会在 personas 为空时自动随机生成）
    av.personas = []
    av.recalc_effects()
    
    return av

@pytest.fixture
def mock_llm_managers():
    """
    Mock 所有涉及 LLM 调用的管理器和函数，防止测试中意外调用 LLM。
    包括：
    - llm_ai (decision making)
    - process_avatar_long_term_objective (long term goal)
    - process_avatar_nickname (nickname generation)
    - RelationResolver.run_batch (relationship evolution)
    """
    from unittest.mock import patch, MagicMock, AsyncMock

    with patch("src.sim.simulator.llm_ai") as mock_ai, \
         patch("src.sim.simulator.process_avatar_long_term_objective", new_callable=AsyncMock) as mock_lto, \
         patch("src.classes.nickname.process_avatar_nickname", new_callable=AsyncMock) as mock_nick, \
         patch("src.classes.relation_resolver.RelationResolver.run_batch", new_callable=AsyncMock) as mock_rr:
        
        # 1. Mock AI Decision
        # ai.decide is an async method
        mock_ai.decide = AsyncMock(return_value={})

        # 2. Mock Long Term Objective
        # AsyncMock returns a coroutine when called
        mock_lto.return_value = None

        # 3. Mock Nickname
        mock_nick.return_value = None

        # 4. Mock Relation Resolver
        mock_rr.return_value = []

        yield {
            "ai": mock_ai,
            "lto": mock_lto,
            "nick": mock_nick,
            "rr": mock_rr
        }
