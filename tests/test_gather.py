import pytest
from unittest.mock import MagicMock, patch
from src.utils.gather import execute_gather, check_can_start_gather
from src.systems.cultivation import Realm
from src.classes.environment.region import NormalRegion

@pytest.fixture
def mock_region(dummy_avatar):
    """设置一个 Mock 的 NormalRegion 到 avatar 所在 tile"""
    real_region = NormalRegion(id=999, name="TestRegion", desc="Testing")
    # Bypass post_init loading from global dicts by manually setting fields
    real_region.lodes = []
    real_region.animals = []
    real_region.plants = []
    
    dummy_avatar.tile.region = real_region
    return real_region

@pytest.fixture
def mock_resource_material():
    material = MagicMock()
    material.name = "TestMaterial"
    material.realm = Realm.Qi_Refinement
    return material

@pytest.fixture
def mock_resource(mock_resource_material):
    """创建一个通用的资源对象 (Lode/Animal/Plant)"""
    res = MagicMock()
    res.realm = Realm.Qi_Refinement
    res.materials = [mock_resource_material]
    return res

def test_check_can_start_gather_success(dummy_avatar, mock_region, mock_resource):
    """测试采集检查通过的情况"""
    mock_region.lodes = [mock_resource]
    
    can, msg = check_can_start_gather(dummy_avatar, "lodes", "矿脉")
    assert can is True
    assert msg == ""

def test_check_can_start_gather_not_normal_region(dummy_avatar):
    """测试不在普通区域的情况"""
    dummy_avatar.tile.region = "NotARegion" 
    
    can, msg = check_can_start_gather(dummy_avatar, "lodes", "矿脉")
    assert can is False
    assert "当前不在普通区域" in msg

def test_check_can_start_gather_no_resources(dummy_avatar, mock_region):
    """测试区域没有资源的情况"""
    mock_region.lodes = []
    
    can, msg = check_can_start_gather(dummy_avatar, "lodes", "矿脉")
    assert can is False
    assert "当前区域没有矿脉" in msg

def test_check_can_start_gather_realm_too_low(dummy_avatar, mock_region, mock_resource):
    """测试境界不足的情况"""
    # 提升资源境界到筑基
    mock_resource.realm = Realm.Foundation_Establishment
    mock_region.lodes = [mock_resource]
    # avatar 默认为练气
    
    can, msg = check_can_start_gather(dummy_avatar, "lodes", "矿脉")
    assert can is False
    assert "当前区域的矿脉境界过高" in msg

def test_execute_gather_success(dummy_avatar, mock_region, mock_resource, mock_resource_material):
    """测试执行采集逻辑成功"""
    mock_region.lodes = [mock_resource]
    
    # 模拟 add_material
    dummy_avatar.add_material = MagicMock()
    
    result = execute_gather(dummy_avatar, "lodes", "extra_mine_materials")
    
    assert "TestMaterial" in result
    assert result["TestMaterial"] >= 1
    dummy_avatar.add_material.assert_called_once()
    
    # 验证获得的材料是正确的
    args, _ = dummy_avatar.add_material.call_args
    assert args[0] == mock_resource_material
    assert args[1] >= 1

def test_execute_gather_with_extra_effect(dummy_avatar, mock_region, mock_resource):
    """测试带有加成效果的采集"""
    mock_region.lodes = [mock_resource]
    
    # effects 是只读属性，它通过合并各个组件的 effects 来计算。
    # 为了测试，我们 Mock 掉 effects 属性。
    with patch.object(type(dummy_avatar), 'effects', new_callable=lambda: {"extra_mine_materials": 2}):
        dummy_avatar.add_material = MagicMock()
        
        result = execute_gather(dummy_avatar, "lodes", "extra_mine_materials")
        
        # 基础1 + 加成2 = 3
        assert result["TestMaterial"] == 3
    
def test_execute_gather_random_selection(dummy_avatar, mock_region):
    """测试从多个资源中随机选择"""
    res1 = MagicMock()
    res1.realm = Realm.Qi_Refinement
    res1.materials = [MagicMock(name="Material1")]
    res1.materials[0].name = "Material1"
    
    res2 = MagicMock()
    res2.realm = Realm.Qi_Refinement
    res2.materials = [MagicMock(name="Material2")]
    res2.materials[0].name = "Material2"
    
    mock_region.lodes = [res1, res2]
    dummy_avatar.add_material = MagicMock()
    
    execute_gather(dummy_avatar, "lodes", "extra_mine_materials")
    dummy_avatar.add_material.assert_called_once()
