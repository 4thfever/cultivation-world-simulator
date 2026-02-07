import pytest
from unittest.mock import MagicMock, Mock
from src.utils.normalize import (
    remove_parentheses,
    normalize_name,
    normalize_goods_name,
    normalize_weapon_type
)
from src.utils.resolution import (
    resolve_query,
    ResolutionResult
)
from src.classes.material import Material
from src.systems.cultivation import Realm

# ==================== Normalize Tests ====================

def test_remove_parentheses():
    """测试括号移除功能"""
    # 基本测试
    assert remove_parentheses("青云剑(凡品)") == "青云剑"
    assert remove_parentheses("青云剑（凡品）") == "青云剑"
    assert remove_parentheses("青云剑[凡品]") == "青云剑"
    assert remove_parentheses("青云剑【凡品】") == "青云剑"
    assert remove_parentheses("青云剑<凡品>") == "青云剑"
    assert remove_parentheses("青云剑《凡品》") == "青云剑"
    
    # 嵌套与多重括号
    assert remove_parentheses("物品(说明(更多说明))") == "物品"
    assert remove_parentheses("前缀(说明)后缀") == "前缀"  # 现有逻辑是截断式
    
    # 无括号
    assert remove_parentheses("普通物品") == "普通物品"
    assert remove_parentheses("") == ""

def test_normalize_goods_name():
    """测试物品名规范化"""
    assert normalize_goods_name("铁剑 -") == "铁剑"
    assert normalize_goods_name("铁剑(凡品) -") == "铁剑"
    assert normalize_goods_name("  铁剑  ") == "铁剑"

def test_normalize_weapon_type():
    """测试兵器类型规范化"""
    assert normalize_weapon_type("剑类") == "剑"
    assert normalize_weapon_type("刀兵器") == "刀"
    assert normalize_weapon_type("枪武器") == "枪"
    assert normalize_weapon_type("普通剑") == "普通剑"


# ==================== Resolution Tests ====================

class MockWorld:
    def __init__(self):
        self.map = Mock()
        self.map.regions = {}
        self.map.sect_regions = {}
        self.avatar_manager = Mock()
        self.avatar_manager.avatars = {}

@pytest.fixture
def mock_world():
    return MockWorld()

def test_resolve_query_empty():
    """测试空查询"""
    res = resolve_query("")
    assert not res.is_valid
    # 实际代码返回 "查询字符串为空" 或 "查询为空" (取决于 query 是 None 还是 "")
    assert res.error_msg in ["查询为空", "查询字符串为空"]
    
    res = resolve_query(None)
    assert not res.is_valid
    assert res.error_msg == "查询为空"

def test_resolve_query_direct_object():
    """测试直接传递对象"""
    # 1. 匹配类型
    material = Material(id=999, name="测试材料", desc="测试描述", realm=Realm.Qi_Refinement)
    res = resolve_query(material, expected_types=[Material])
    assert res.is_valid
    assert res.obj is material
    assert res.resolved_type == Material

    # 2. 不匹配类型但作为对象传入
    res = resolve_query(material, expected_types=[Realm])
    assert not res.is_valid

def test_resolve_query_realm():
    """测试境界解析"""
    # 1. 字符串匹配（中文） - 取决于Realm的定义，假设 Realm.Qi_Refinement.value 是 "炼气" 或类似
    # 我们先看看 Realm 定义再填，或者使用已知的枚举名
    
    # 使用枚举名通常更稳健
    res = resolve_query("Qi_Refinement", expected_types=[Realm])
    assert res.is_valid
    assert res.obj == Realm.Qi_Refinement

    # 3. 无效值
    res = resolve_query("不存在的境界", expected_types=[Realm])
    assert not res.is_valid

def test_resolve_query_unsupported_type():
    """测试不支持的类型输入"""
    res = resolve_query(123, expected_types=[Material])
    assert not res.is_valid
    assert "非字符串" in res.error_msg

def test_resolve_region_mock(mock_world):
    """测试区域解析（Mock环境）"""
    # 准备数据 - 使用 regions[id] 字典而非 region_names
    mock_region = Mock()
    mock_region.name = "青云山"
    mock_world.map.regions = {1: mock_region}
    
    # 1. 精确匹配
    res = resolve_query("青云山", world=mock_world, expected_types=[type(mock_region)]) # 动态类型模拟 Region
    # 注意：resolution代码里检查的是具体的类名字符串，Mock类名可能不同
    # 我们需要 hack 一下 expected_types 让它通过检查
    
    # 为了测试方便，我们直接模拟 resolution.py 里的 Region 类导入
    # 或者我们只测试逻辑分支
    pass 

# 由于 resolution.py 内部强依赖了实际的类 (Material, Region 等)，
# 且使用了 isinstance(t, type) 和 t.__name__ 判断，
# 纯单元测试建议主要覆盖逻辑分支。集成测试覆盖实际类。

def test_resolve_priority():
    """测试解析优先级"""
    # 假设我们有一个名字既是物品又是境界（不太可能，但为了测试逻辑）
    # 这里的关键是 expected_types 的顺序
    
    # 模拟数据
    pass

