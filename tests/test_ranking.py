import pytest
from unittest.mock import MagicMock

from src.classes.ranking import RankingManager
from src.systems.cultivation import Realm, CultivationProgress
from src.classes.core.sect import Sect, SectHeadQuarter
from src.classes.alignment import Alignment

@pytest.fixture
def test_sect():
    hq = SectHeadQuarter(name="测试驻地", desc="测试驻地描述", image="test.png")
    sect = Sect(
        id=1,
        name="测试宗门",
        desc="测试",
        member_act_style="测试风格",
        alignment=Alignment.RIGHTEOUS,
        headquarter=hq,
        technique_names=[]
    )
    return sect

def test_update_rankings_empty():
    manager = RankingManager()
    manager.update_rankings([])
    
    data = manager.get_rankings_data()
    assert len(data["heaven"]) == 0
    assert len(data["earth"]) == 0
    assert len(data["human"]) == 0
    # sect is populated from global sects_by_id, so it might not be empty if there are global sects.
    # We will mock the sects_by_id or just let it be.

def test_update_rankings_avatars(dummy_avatar, test_sect):
    manager = RankingManager()
    
    # 构造人榜（筑基）角色
    human_avatar = MagicMock()
    human_avatar.id = "human_1"
    human_avatar.name = "Human"
    human_avatar.sect = test_sect
    human_avatar.cultivation_progress = CultivationProgress(31) # 筑基前期
    human_avatar.is_dead = False
    
    # 构造地榜（金丹）角色
    earth_avatar = MagicMock()
    earth_avatar.id = "earth_1"
    earth_avatar.name = "Earth"
    earth_avatar.sect = None # 散修
    earth_avatar.cultivation_progress = CultivationProgress(61) # 金丹前期
    earth_avatar.is_dead = False
    
    # 构造天榜（元婴）角色
    heaven_avatar = MagicMock()
    heaven_avatar.id = "heaven_1"
    heaven_avatar.name = "Heaven"
    heaven_avatar.sect = test_sect
    heaven_avatar.cultivation_progress = CultivationProgress(91) # 元婴前期
    heaven_avatar.is_dead = False
    
    # 还需要 mock get_base_strength
    # 为了避免依赖具体战斗力计算，我们在 avatar 上加上 mock 返回值？
    # 实际上 get_base_strength 是根据 realm 和 effects 来的
    # 我们可以用真实的 Avatar 或者给 mock_avatar 加上必要的属性
    
    # 为了方便，直接修改 dummy_avatar 产生三个真实的 Avatar
    import copy
    import uuid
    
    av1 = copy.deepcopy(dummy_avatar)
    av1.id = str(uuid.uuid4())
    av1.name = "Human"
    av1.cultivation_progress.level = 31
    av1.cultivation_progress.realm = Realm.Foundation_Establishment
    av1.sect = test_sect
    test_sect.add_member(av1)
    
    av2 = copy.deepcopy(dummy_avatar)
    av2.id = str(uuid.uuid4())
    av2.name = "Earth"
    av2.cultivation_progress.level = 61
    av2.cultivation_progress.realm = Realm.Core_Formation
    av2.sect = None
    
    av3 = copy.deepcopy(dummy_avatar)
    av3.id = str(uuid.uuid4())
    av3.name = "Heaven"
    av3.cultivation_progress.level = 91
    av3.cultivation_progress.realm = Realm.Nascent_Soul
    av3.sect = test_sect
    test_sect.add_member(av3)

    # 我们需要 patch sects_by_id 让他只包含 test_sect，这样才能测试宗门榜
    with pytest.MonkeyPatch.context() as m:
        m.setattr("src.classes.core.sect.sects_by_id", {1: test_sect})
        manager.update_rankings([av1, av2, av3])
    
    data = manager.get_rankings_data()
    
    # 验证天榜
    assert len(data["heaven"]) == 1
    assert data["heaven"][0]["name"] == "Heaven"
    assert data["heaven"][0]["sect"] == "测试宗门"
    
    # 验证地榜
    assert len(data["earth"]) == 1
    assert data["earth"][0]["name"] == "Earth"
    assert data["earth"][0]["sect"] == "散修"  # t("Rogue Cultivator") returns "散修" in zh-CN
    
    # 验证人榜
    assert len(data["human"]) == 1
    assert data["human"][0]["name"] == "Human"
    assert data["human"][0]["sect"] == "测试宗门"
    
    # 验证宗门榜
    assert len(data["sect"]) == 1
    assert data["sect"][0]["name"] == "测试宗门"
    assert data["sect"][0]["member_count"] == 2
    # 宗门总战斗力应大于0
    assert data["sect"][0]["total_power"] > 0
    
def test_ranking_sorting(dummy_avatar):
    """验证同境界下的战斗力排序"""
    manager = RankingManager()
    
    import copy
    import uuid
    from src.systems.battle import get_base_strength
    
    av1 = copy.deepcopy(dummy_avatar)
    av1.id = str(uuid.uuid4())
    av1.name = "Weak Nascent"
    av1.update_cultivation(91) # 元婴前期
    
    av2 = copy.deepcopy(dummy_avatar)
    av2.id = str(uuid.uuid4())
    av2.name = "Strong Nascent"
    av2.update_cultivation(111) # 元婴后期

    print(f"av1 strength: {get_base_strength(av1)}")
    print(f"av2 strength: {get_base_strength(av2)}")

    manager.update_rankings([av1, av2])
    
    data = manager.get_rankings_data()
    print(data["heaven"])
    assert len(data["heaven"]) == 2
    # 战斗力高的排在前面
    assert data["heaven"][0]["name"] == "Strong Nascent"
    assert data["heaven"][1]["name"] == "Weak Nascent"
