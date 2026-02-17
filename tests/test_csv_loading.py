"""
测试 CSV 数据加载的正确性。
验证代码中使用的列名与 CSV 文件中的实际列名匹配。
采用动态多语言测试方案，不再硬编码特定语言的预期字符串。
"""
import pytest
import csv
from pathlib import Path
from src.classes.core.sect import sects_by_id, sects_by_name, Sect, reload as reload_sects
from src.classes.technique import techniques_by_id, techniques_by_name, Technique, reload as reload_techniques
from src.classes.items.elixir import elixirs_by_id
from src.utils.config import CONFIG
from src.i18n import t, reload_translations
from src.classes.language import language_manager

# --- Helpers ---

def read_raw_csv_as_dict(file_path):
    """读取原始 CSV 文件，跳过描述行"""
    if not file_path.exists():
        return []
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        lines = list(csv.reader(f))
        
        if len(lines) < 1:
            return []
            
        headers = lines[0]
        data = []
        
        # Start from index 2 if there's a description row
        start_index = 2 if len(lines) > 1 else 1
        
        for row_values in lines[start_index:]:
            if not row_values: continue
            row_dict = {}
            for i, h in enumerate(headers):
                 if i < len(row_values):
                     row_dict[h] = row_values[i]
                 else:
                     row_dict[h] = None
            data.append(row_dict)
            
        return data

@pytest.fixture(params=["zh-CN", "zh-TW", "en-US"])
def game_lang(request):
    """
    参数化 Fixture：切换语言并重载游戏数据。
    测试结束后自动恢复回 zh-CN 环境。
    """
    lang = request.param
    
    # 1. Switch Language
    language_manager.set_language(lang)
    reload_translations()
    
    # 2. Force Reload Game Data
    from src.utils.config import update_paths_for_language
    update_paths_for_language(lang)
    
    from src.utils.df import reload_game_configs
    reload_game_configs()
    
    reload_techniques() 
    reload_sects()
    
    yield lang
    
    # Teardown: Restore to zh-CN for other tests
    language_manager.set_language("zh-CN")
    reload_translations()
    update_paths_for_language("zh-CN")
    reload_game_configs()
    reload_techniques()
    reload_sects()


class TestSectLoading:
    """测试宗门数据加载 (多语言动态验证)"""

    def test_sect_headquarter_name_loaded(self, game_lang):
        """测试宗门驻地名称正确加载"""
        # Read RAW Sect CSV
        sect_csv_path = CONFIG.paths.shared_game_configs / "sect.csv"
        raw_sects = read_raw_csv_as_dict(sect_csv_path)
        
        # Read RAW Sect Region CSV (Source of HQ names)
        region_csv_path = CONFIG.paths.shared_game_configs / "sect_region.csv"
        raw_regions = read_raw_csv_as_dict(region_csv_path)
        sect_region_map = {int(r['sect_id']): r for r in raw_regions if r.get('sect_id')}
        
        # Verify specific Sect (ID=12, 不夜城)
        target_id = 12
        sect = sects_by_id.get(target_id)
        assert sect is not None
        
        # 1. Verify Sect Name
        sect_row = next((r for r in raw_sects if int(r['id']) == target_id), None)
        assert sect_row
        
        expected_sect_name = sect_row.get('name')
        if sect_row.get('name_id'):
            trans = t(sect_row['name_id'])
            if trans and trans != sect_row['name_id']:
                expected_sect_name = trans
        
        assert sect.name == expected_sect_name, f"Sect name mismatch in {game_lang}"
        
        # 2. Verify HQ Name
        region_row = sect_region_map.get(target_id)
        assert region_row
        
        expected_hq_name = region_row.get('name')
        if region_row.get('name_id'):
            trans = t(region_row['name_id'])
            if trans and trans != region_row['name_id']:
                expected_hq_name = trans
                
        assert sect.headquarter.name == expected_hq_name, f"HQ name mismatch in {game_lang}"

    def test_sect_headquarter_desc_loaded(self, game_lang):
        """测试宗门驻地描述正确加载"""
        target_id = 12
        sect = sects_by_id.get(target_id)
        assert sect is not None
        
        # Read RAW Sect Region CSV
        region_csv_path = CONFIG.paths.shared_game_configs / "sect_region.csv"
        raw_regions = read_raw_csv_as_dict(region_csv_path)
        region_row = next((r for r in raw_regions if int(r.get('sect_id', -1)) == target_id), None)
        assert region_row
        
        expected_desc = region_row.get('desc')
        if region_row.get('desc_id'):
            trans = t(region_row['desc_id'])
            if trans and trans != region_row['desc_id']:
                expected_desc = trans
                
        # Normalize newlines/spaces for comparison if needed
        assert sect.headquarter.desc == expected_desc, f"HQ desc mismatch in {game_lang}"

    def test_all_sects_have_headquarters(self, game_lang):
        """测试所有宗门都有驻地信息"""
        for sect_id, sect in sects_by_id.items():
            assert sect.headquarter is not None
            assert sect.headquarter.name, f"宗门 {sect.name} 的驻地名称不应为空"

    def test_sect_techniques_loaded(self, game_lang):
        """测试宗门功法列表正确加载"""
        sect = sects_by_id.get(1) # 明心剑宗
        assert sect is not None
        assert len(sect.technique_names) > 0

    def test_sect_without_techniques(self, game_lang):
        """测试没有配置功法的宗门"""
        sect = sects_by_id.get(10) # 摄魂音宗
        assert sect is not None
        assert sect.technique_names == []


class TestTechniqueLoading:
    """测试功法数据加载"""

    def test_technique_sect_id_loaded(self, game_lang):
        """测试功法的 sect_id 正确加载"""
        tech_id = 30 # 草字剑诀
        technique = techniques_by_id.get(tech_id)
        assert technique is not None
        
        # Verify Name using Dynamic Logic
        tech_csv_path = CONFIG.paths.shared_game_configs / "technique.csv"
        raw_techs = read_raw_csv_as_dict(tech_csv_path)
        row = next((r for r in raw_techs if int(r['id']) == tech_id), None)
        
        expected_name = row.get('name')
        if row.get('name_id'):
            trans = t(row['name_id'])
            if trans and trans != row['name_id']:
                expected_name = trans
                
        assert technique.name == expected_name, f"Technique name mismatch in {game_lang}"
        assert technique.sect_id == 1

    def test_technique_without_sect(self, game_lang):
        """测试散修功法"""
        technique = techniques_by_id.get(1)
        assert technique is not None
        assert technique.sect_id is None

    def test_sect_techniques_match(self, game_lang):
        """测试宗门功法和功法的宗门ID相互匹配"""
        for sect_id, sect in sects_by_id.items():
            for tech_name in sect.technique_names:
                technique = techniques_by_name.get(tech_name)
                # 注意：technique_names 是 string list，如果 names 不匹配（翻译问题）这里会取不到
                # 但我们的系统设计是：sect.technique_names 是直接从 technique.csv 加载的
                # 所以只要 reload 顺序正确（先 technique 后 sect），名字应该是一致的
                assert technique is not None, f"功法 '{tech_name}' 应该存在 (Lang: {game_lang})"
                assert technique.sect_id == sect_id


class TestElixirLoading:
    """丹药加载测试 (ID check, less dependent on lang but good to verify integrity)"""

    def test_elixir_loaded_with_item_id(self):
        # 丹药目前没有专门的 reload 和 translation key 绑定逻辑验证需求
        # 保持原样即可，不需要 parametrizing unless needed
        assert len(elixirs_by_id) > 0
        for elixir_id, elixir in elixirs_by_id.items():
            assert elixir_id > 0
            assert elixir.id == elixir_id


class TestGameDataAPI:
    """测试 API (API 测试通常在固定环境下运行，这里不使用多语言参数化以免影响 Server 状态)"""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from src.server.main import app
        return TestClient(app)

    def test_game_data_techniques_have_sect_id(self, client):
        response = client.get("/api/meta/game_data")
        assert response.status_code == 200
        data = response.json()
        assert len(data["techniques"]) > 0
        assert "sect_id" in data["techniques"][0]

    def test_game_data_sects_structure(self, client):
        response = client.get("/api/meta/game_data")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sects"]) > 0
        assert "id" in data["sects"][0]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
