"""
测试 CSV 数据加载的正确性。
验证代码中使用的列名与 CSV 文件中的实际列名匹配。
"""
import pytest
from src.classes.sect import sects_by_id, sects_by_name, Sect
from src.classes.technique import techniques_by_id, techniques_by_name, Technique


class TestSectLoading:
    """测试宗门数据加载"""

    def test_sect_headquarter_name_loaded(self):
        """测试宗门驻地名称正确加载（来自 sect_region.csv 的 name 列）"""
        # 不夜城 (sect_id=12) 的驻地应该是 "大千光极城"
        sect = sects_by_id.get(12)
        assert sect is not None, "宗门 ID=12 应该存在"
        
        # 兼容多语言环境：检查中文或英文名称
        expected_names = {"Sleepless City", "不夜城"}
        assert sect.name in expected_names, f"宗门名称 '{sect.name}' 不在预期列表中: {expected_names}"
        
        expected_hqs = {"Daqian Aurora City", "大千光极城"}
        assert sect.headquarter.name in expected_hqs, (
            f"驻地名称 '{sect.headquarter.name}' 不在预期列表中: {expected_hqs}"
        )

    def test_sect_headquarter_desc_loaded(self):
        """测试宗门驻地描述正确加载（来自 sect_region.csv 的 desc 列）"""
        sect = sects_by_id.get(12)
        assert sect is not None
        # 验证描述不为空且包含关键词 (兼容中英文)
        assert sect.headquarter.desc, "驻地描述不应为空"
        
        desc = sect.headquarter.desc.lower()
        # English keyword: "aurora", Chinese keyword: "极光" or similar unique term
        # 假设中文描述里也会有相关描述。如果不确定中文具体描述，可以只检查英文环境或跳过。
        # 这里简单检查：如果是英文环境包含 aurora，如果是中文环境...
        
        from src.classes.language import language_manager, LanguageType
        if language_manager.current == LanguageType.EN_US:
            assert "aurora" in desc, f"驻地描述 '{desc}' 应该包含 'aurora'"
        else:
            # 中文描述检查
            assert "极光" in desc or "不夜" in desc, f"驻地描述 '{desc}' 应该包含 '极光' 或 '不夜'"

    def test_all_sects_have_headquarters(self):
        """测试所有宗门都有驻地信息"""
        for sect_id, sect in sects_by_id.items():
            assert sect.headquarter is not None, f"宗门 {sect.name} (ID={sect_id}) 应该有驻地"
            assert sect.headquarter.name, f"宗门 {sect.name} 的驻地名称不应为空"

    def test_sect_techniques_loaded(self):
        """测试宗门功法列表正确加载"""
        # 明心剑宗 (sect_id=1) 应该有功法
        sect = sects_by_id.get(1)
        assert sect is not None, "宗门 ID=1 应该存在"
        assert len(sect.technique_names) > 0, (
            f"宗门 '{sect.name}' 应该有独门功法，但 technique_names 为空"
        )

    def test_sect_without_techniques(self):
        """测试没有配置功法的宗门（不夜城 sect_id=12）"""
        sect = sects_by_id.get(12)
        assert sect is not None
        # 不夜城在 technique.csv 中没有配置功法，所以应该是空列表
        assert sect.technique_names == [], (
            f"宗门 '{sect.name}' 不应该有独门功法"
        )


class TestTechniqueLoading:
    """测试功法数据加载"""

    def test_technique_sect_id_loaded(self):
        """测试功法的 sect_id 正确加载（来自 technique.csv 的 sect_id 列）"""
        # 草字剑诀 (id=30) 属于明心剑宗 (sect_id=1)
        technique = techniques_by_id.get(30)
        assert technique is not None, "功法 ID=30 应该存在"
        
        # 兼容多语言环境
        expected_names = {"Grass Word Sword Formula", "草字剑诀"}
        assert technique.name in expected_names, f"功法名称 '{technique.name}' 不在预期列表中: {expected_names}"
        
        assert technique.sect_id == 1, (
            f"功法 '{technique.name}' 的 sect_id 应该是 1，而不是 {technique.sect_id}"
        )

    def test_technique_without_sect(self):
        """测试散修功法（没有宗门限制）的 sect_id 为 None"""
        # 金刚不坏体 (id=1) 是散修功法
        technique = techniques_by_id.get(1)
        assert technique is not None, "功法 ID=1 应该存在"
        assert technique.sect_id is None, (
            f"散修功法 '{technique.name}' 的 sect_id 应该是 None，而不是 {technique.sect_id}"
        )

    def test_sect_techniques_match(self):
        """测试宗门功法和功法的宗门ID相互匹配"""
        for sect_id, sect in sects_by_id.items():
            for tech_name in sect.technique_names:
                technique = techniques_by_name.get(tech_name)
                assert technique is not None, f"功法 '{tech_name}' 应该存在"
                assert technique.sect_id == sect_id, (
                    f"功法 '{tech_name}' 的 sect_id ({technique.sect_id}) "
                    f"应该匹配宗门 '{sect.name}' 的 ID ({sect_id})"
                )


class TestElixirLoading:
    """测试丹药数据加载"""

    def test_elixir_loaded_with_item_id(self):
        """测试丹药使用 item_id 列正确加载"""
        from src.classes.elixir import elixirs_by_id
        
        # 验证丹药已加载且 ID 不为 0（如果用错误的列名会得到默认值 0）
        assert len(elixirs_by_id) > 0, "应该加载到丹药数据"
        
        for elixir_id, elixir in elixirs_by_id.items():
            assert elixir_id > 0, f"丹药 '{elixir.name}' 的 ID 应该大于 0"
            assert elixir.id == elixir_id, f"丹药 ID 不匹配: {elixir.id} != {elixir_id}"


class TestGameDataAPI:
    """测试 /api/meta/game_data API 返回正确的数据结构"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from fastapi.testclient import TestClient
        from src.server.main import app
        return TestClient(app)

    def test_game_data_techniques_have_sect_id(self, client):
        """测试 /api/meta/game_data 返回的功法包含 sect_id 字段（而非 sect）"""
        response = client.get("/api/meta/game_data")
        assert response.status_code == 200
        
        data = response.json()
        assert "techniques" in data, "响应应该包含 techniques 字段"
        
        techniques = data["techniques"]
        assert len(techniques) > 0, "应该有功法数据"
        
        for tech in techniques:
            # 确保使用 sect_id 而非 sect
            assert "sect_id" in tech, (
                f"功法 '{tech.get('name', 'unknown')}' 应该有 sect_id 字段"
            )
            assert "sect" not in tech, (
                f"功法 '{tech.get('name', 'unknown')}' 不应该有 sect 字段（应使用 sect_id）"
            )
            
            # 验证 sect_id 的值类型正确
            sect_id = tech["sect_id"]
            assert sect_id is None or isinstance(sect_id, int), (
                f"功法 '{tech.get('name')}' 的 sect_id 应该是 None 或 int，而不是 {type(sect_id)}"
            )

    def test_game_data_sects_structure(self, client):
        """测试 /api/meta/game_data 返回的宗门数据结构正确"""
        response = client.get("/api/meta/game_data")
        assert response.status_code == 200
        
        data = response.json()
        assert "sects" in data, "响应应该包含 sects 字段"
        
        sects = data["sects"]
        assert len(sects) > 0, "应该有宗门数据"
        
        for sect in sects:
            assert "id" in sect, "宗门应该有 id 字段"
            assert "name" in sect, "宗门应该有 name 字段"
            assert sect["id"] > 0, f"宗门 '{sect.get('name')}' 的 ID 应该大于 0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
