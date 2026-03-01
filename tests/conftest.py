import pytest
import random
import logging
import sys
from unittest.mock import MagicMock, AsyncMock, patch

from src.classes.environment.map import Map


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging(tmp_path_factory):
    """
    Configure logging to prevent pollution of project root logs.
    1. Redirect src.run.log to temp directory.
    2. Configure root logger to output to stderr for pytest capture.
    """
    # 1. Setup root logger for pytest
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
    
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # 2. Patch src.run.log to use temp directory
    temp_log_dir = tmp_path_factory.mktemp("logs")
    
    # Import here to avoid circular dependencies if any
    import src.run.log
    
    # Reset singleton to ensure it gets re-initialized with patched method
    src.run.log._logger = None
    
    original_setup = src.run.log.Logger._setup_current_logger
    
    def safe_setup(self):
        # Redirect to temp dir
        self.log_dir = temp_log_dir
        # Ensure dir exists
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Call original (will create file in temp dir)
        original_setup(self)
        
        # Allow propagation so pytest can capture logs via root logger
        self.logger.propagate = True
        
    with patch("src.run.log.Logger._setup_current_logger", side_effect=safe_setup, autospec=True):
        yield

@pytest.fixture(autouse=True)
def isolate_save_path(monkeypatch, tmp_path):
    """
    Redirect save path to temp dir for each test to prevent pollution.
    Uses monkeypatch for safe rollback.
    """
    from src.utils.config import CONFIG
    import src.utils.config
    
    # Create temp dir for saves
    # Use a unique name to avoid conflict with tests that create "saves" dir manually
    temp_saves = tmp_path / "test_isolation_saves"
    temp_saves.mkdir(parents=True, exist_ok=True)
    
    # 1. Patch current CONFIG
    # CONFIG.paths is likely an OmegaConf object or dict-like
    monkeypatch.setattr(CONFIG.paths, "saves", temp_saves)
    
    # 2. Patch load_config to ensure any reloads also use temp dir
    original_load_config = src.utils.config.load_config
    
    def safe_load_config():
        config = original_load_config()
        if hasattr(config, "paths"):
            config.paths.saves = temp_saves
        return config
    
    monkeypatch.setattr(src.utils.config, "load_config", safe_load_config)
    
    yield temp_saves


@pytest.fixture(autouse=True)
def fixed_random_seed():
    """
    Ensure all tests have deterministic random behavior.
    This fixture is automatically applied to all tests.
    """
    random.seed(42)
    yield

@pytest.fixture(scope="session", autouse=True)
def force_chinese_language():
    """
    Force language to Chinese for all tests to match expected string outputs.
    """
    from src.classes.language import language_manager
    from src.utils.config import update_paths_for_language
    
    # Force language to Chinese
    language_manager.set_language("zh-CN")
    
    # Ensure game configs are reloaded (in case set_language skipped it due to circular import protection)
    from src.utils.df import reload_game_configs
    reload_game_configs()
    
    yield
from src.classes.environment.tile import TileType, Tile
from src.classes.core.world import World
from src.systems.time import Month, Year, create_month_stamp
from src.classes.core.avatar import Avatar, Gender
from src.classes.age import Age
from src.systems.cultivation import Realm
from src.utils.id_generator import get_avatar_id
from src.utils.name_generator import get_random_name
from src.classes.root import Root
from src.classes.alignment import Alignment

# Action related imports
from src.classes.items.elixir import Elixir, ElixirType
from src.classes.material import Material
from src.classes.items.weapon import Weapon
from src.classes.weapon_type import WeaponType
from src.classes.items.auxiliary import Auxiliary
from src.classes.environment.region import CityRegion

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
    # 强制清空功法，防止随机出的功法带有移动步长加成（如逍遥游）
    av.technique = None
    av.recalc_effects()
    
    return av

@pytest.fixture(autouse=True)
def mock_llm_managers():
    """
    Mock 所有涉及 LLM 调用的管理器和函数，防止测试中意外调用 LLM。
    """
    # 创建 mock LLM 配置
    mock_llm_config = MagicMock()
    mock_llm_config.api_key = "test_key"
    mock_llm_config.base_url = "http://test.api/v1"
    mock_llm_config.model_name = "test-model"
    
    with patch("src.sim.simulator.llm_ai") as mock_ai, \
         patch("src.sim.simulator.process_avatar_long_term_objective", new_callable=AsyncMock) as mock_lto, \
         patch("src.sim.simulator.process_avatar_backstory", new_callable=AsyncMock) as mock_backstory, \
         patch("src.classes.nickname.process_avatar_nickname", new_callable=AsyncMock) as mock_nick, \
         patch("src.classes.relation.relation_resolver.RelationResolver.run_batch", new_callable=AsyncMock) as mock_rr, \
         patch("src.classes.history.HistoryManager.apply_history_influence", new_callable=AsyncMock) as mock_hist, \
         patch("src.classes.story_teller.call_llm_with_task_name", new_callable=AsyncMock) as mock_call_llm_story, \
         patch("src.utils.llm.config.LLMConfig.from_mode", return_value=mock_llm_config) as mock_config:
        
        mock_ai.decide = AsyncMock(return_value={})
        mock_lto.return_value = None
        mock_backstory.return_value = None
        mock_nick.return_value = None
        mock_rr.return_value = []
        mock_hist.return_value = None
        mock_call_llm_story.return_value = {"story": "测试故事"}

        yield {
            "ai": mock_ai,
            "lto": mock_lto,
            "backstory": mock_backstory,
            "nick": mock_nick,
            "rr": mock_rr,
            "hist": mock_hist,
            "story": mock_call_llm_story,
            "gathering_story": mock_call_llm_story,
            "config": mock_config
        }

# --- Shared Helpers for Item Creation ---

def create_test_elixir(name, realm, price=100, elixir_id=1, effects=None):
    if effects is None:
        effects = {"max_hp": 10}
    return Elixir(
        id=elixir_id,
        name=name,
        realm=realm,
        type=ElixirType.Breakthrough,
        desc="测试丹药",
        price=price,
        effects=effects
    )

def create_test_material(name, realm, material_id=101):
    return Material(
        id=material_id,
        name=name,
        desc="测试物品",
        realm=realm
    )

def create_test_weapon(name, realm, weapon_id=201):
    return Weapon(
        id=weapon_id,
        name=name,
        weapon_type=WeaponType.SWORD,
        realm=realm,
        desc="测试兵器",
        effects={},
        effect_desc=""
    )

def create_test_auxiliary(name, realm, aux_id=301):
    return Auxiliary(
        id=aux_id,
        name=name,
        realm=realm,
        desc="测试法宝",
        effects={},
        effect_desc=""
    )

@pytest.fixture
def avatar_in_city(dummy_avatar):
    """
    修改 dummy_avatar，使其位于城市中，并给予初始资金
    """
    city_region = CityRegion(id=1, name="TestCity", desc="测试城市")
    tile = Tile(0, 0, TileType.CITY)
    tile.region = city_region
    
    dummy_avatar.tile = tile
    dummy_avatar.magic_stone = 1000
    dummy_avatar.cultivation_progress.realm = Realm.Qi_Refinement
    dummy_avatar.elixirs = []
    dummy_avatar.materials = {} # 确保背包为空
    dummy_avatar.weapon = None
    dummy_avatar.auxiliary = None
    
    return dummy_avatar

@pytest.fixture
def mock_item_data():
    """
    提供标准的一组测试物品，包括材料、丹药、兵器、法宝。
    返回一个包含这些对象的字典，方便后续 mock 使用。
    """
    test_elixir = create_test_elixir("聚气丹", Realm.Qi_Refinement, price=100)
    high_level_elixir = create_test_elixir("筑基丹", Realm.Foundation_Establishment, price=1000, elixir_id=2)
    test_material = create_test_material("铁矿石", Realm.Qi_Refinement)
    test_weapon = create_test_weapon("青云剑", Realm.Qi_Refinement)
    test_auxiliary = create_test_auxiliary("聚灵珠", Realm.Qi_Refinement)

    return {
        "elixirs": {
            "聚气丹": [test_elixir],
            "筑基丹": [high_level_elixir]
        },
        "materials": {
            "铁矿石": test_material
        },
        "weapons": {
            "青云剑": test_weapon
        },
        "auxiliaries": {
            "聚灵珠": test_auxiliary
        },
        # Direct access
        "obj_elixir": test_elixir,
        "obj_high_elixir": high_level_elixir,
        "obj_material": test_material,
        "obj_weapon": test_weapon,
        "obj_auxiliary": test_auxiliary
    }
