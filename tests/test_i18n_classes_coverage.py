#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 src/classes/ 下的本地化覆盖率和质量

此测试确保：
1. 没有硬编码的中文字符串（除了注释和测试数据）
2. 所有使用的翻译键都在 po 文件中定义
3. 所有类的信息方法返回本地化内容
4. 格式化参数使用一致
"""

import re
import ast
from pathlib import Path
from typing import Set, Dict, List
import pytest

from src.i18n import t
from src.classes.language import language_manager


class TestHardcodedStrings:
    """检查 src/classes/ 下是否有硬编码的中文字符串"""
    
    ALLOWED_HARDCODED_PATTERNS = [
        # 允许的模式（如配置键名、常量等）
        r'^\s*#',  # 行首注释
        r'#.*$',  # 行尾注释
        r'^\s*"""',  # 文档字符串
        r"^\s*'''",  # 文档字符串
        r'.*:\s*"[^"]*".*#',  # 带注释的赋值（如 RIGHTEOUS = "righteous"  # 正）
        r'.*=\s*\{[^}]*\}',  # 字典/集合定义（用于映射和匹配）
        r'.*\.get\(',  # 字典 get 方法的默认值
        r'.*in\s*\{',  # 集合成员检查（用于匹配输入）
    ]
    
    EXCLUDE_FILES = [
        '__pycache__',
        '.pyc',
        '__init__.py',  # 可能只是导入
        'alignment.py',  # 阵营定义文件，包含合理的映射
        'action_runtime.py',  # 运行时常量定义
        'appearance.py',  # 外观描述数据文件，包含大量静态文本
        'animal.py',  # 动物数据文件
        'material_type.py',  # 材料类型数据
        'weapon_type.py',  # 武器类型数据
        'feature.py',  # 特征数据文件
        'cultivation_method.py',  # 修炼方法数据
        'persona.py',  # 性格数据
        'ai.py',  # AI 相关，包含默认值
    ]
    
    @staticmethod
    def contains_chinese(text: str) -> bool:
        """检查字符串是否包含中文字符"""
        return bool(re.search(r'[\u4e00-\u9fff]', text))
    
    @staticmethod
    def is_allowed_line(line: str) -> bool:
        """检查是否是允许包含中文的行（如注释）"""
        for pattern in TestHardcodedStrings.ALLOWED_HARDCODED_PATTERNS:
            if re.match(pattern, line):
                return True
        return False
    
    @pytest.mark.xfail(reason="i18n 迁移进行中，还有约430个硬编码中文字符串待处理")
    def test_no_hardcoded_chinese_in_classes(self):
        """检查 src/classes/ 下的 Python 文件中是否有硬编码的中文字符串"""
        classes_dir = Path("src/classes")
        
        if not classes_dir.exists():
            pytest.skip("src/classes directory not found")
        
        violations = []
        
        for py_file in classes_dir.rglob("*.py"):
            # 跳过排除的文件
            if any(exclude in str(py_file) for exclude in self.EXCLUDE_FILES):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # 跳过允许的行
                    if self.is_allowed_line(line):
                        continue
                    
                    # 检查是否包含中文
                    if self.contains_chinese(line):
                        # 进一步检查是否在字符串中
                        # 排除 f-string 和普通 string 中的中文应该用 t() 包裹
                        # 简单检查：如果有引号且包含中文，就认为可能有问题
                        if '"' in line or "'" in line:
                            violations.append({
                                'file': str(py_file.relative_to('src/classes')),
                                'line': i,
                                'content': line.strip()[:80]  # 只显示前80个字符
                            })
            
            except Exception as e:
                print(f"Warning: Could not read {py_file}: {e}")
        
        if violations:
            msg = "\n发现硬编码的中文字符串（应使用 t() 函数）:\n"
            for v in violations[:10]:  # 只显示前10个
                msg += f"  {v['file']}:{v['line']} - {v['content']}\n"
            if len(violations) > 10:
                msg += f"  ... 还有 {len(violations) - 10} 个\n"
            pytest.fail(msg)


class TestTranslationKeysUsage:
    """检查翻译键的使用情况"""
    
    @staticmethod
    def extract_t_function_calls(py_file: Path) -> Set[str]:
        """从 Python 文件中提取所有 t() 函数调用的第一个参数"""
        try:
            content = py_file.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            msgids = set()
            
            for node in ast.walk(tree):
                # 查找 t() 函数调用
                if isinstance(node, ast.Call):
                    # 检查函数名是否是 t
                    func_name = None
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr
                    
                    if func_name == 't' and node.args:
                        # 获取第一个参数（msgid）
                        first_arg = node.args[0]
                        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                            msgids.add(first_arg.value)
            
            return msgids
        
        except Exception as e:
            print(f"Warning: Could not parse {py_file}: {e}")
            return set()
    
    @staticmethod
    def extract_msgids_from_po(po_file: Path) -> Set[str]:
        """从 po 文件中提取所有 msgid"""
        msgids = set()
        
        try:
            content = po_file.read_text(encoding='utf-8')
            pattern = r'msgid\s+"([^"]*)"'
            matches = re.findall(pattern, content)
            # 将 po 文件中的转义序列（如 \\n \\t等）转换为实际字符
            # 使用字符串替换而不是 decode，避免中文字符编码问题
            decoded_msgids = set()
            for m in matches:
                if m:  # 排除空字符串
                    # 替换常见的转义序列
                    decoded = m.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r').replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
                    decoded_msgids.add(decoded)
            msgids = decoded_msgids
        except Exception as e:
            print(f"Warning: Could not read {po_file}: {e}")
        
        return msgids
    
    def test_all_used_msgids_are_defined(self):
        """检查所有在代码中使用的 msgid 都在 po 文件中定义"""
        classes_dir = Path("src/classes")
        po_file = Path("src/i18n/locales/zh_CN/LC_MESSAGES/messages.po")
        
        if not classes_dir.exists() or not po_file.exists():
            pytest.skip("Required directories not found")
        
        # 提取 po 文件中的所有 msgid
        defined_msgids = self.extract_msgids_from_po(po_file)
        
        # 提取代码中使用的所有 msgid
        used_msgids = set()
        for py_file in classes_dir.rglob("*.py"):
            used_msgids.update(self.extract_t_function_calls(py_file))
        
        # 找出未定义的 msgid
        undefined_msgids = used_msgids - defined_msgids
        
        if undefined_msgids:
            msg = f"\n发现 {len(undefined_msgids)} 个在代码中使用但未在 po 文件中定义的 msgid:\n"
            for msgid in sorted(undefined_msgids)[:10]:
                msg += f"  - '{msgid}'\n"
            if len(undefined_msgids) > 10:
                msg += f"  ... 还有 {len(undefined_msgids) - 10} 个\n"
            pytest.fail(msg)


class TestClassesI18nIntegration:
    """测试 classes 中的类是否正确集成了国际化"""
    
    def setup_method(self):
        """每个测试前重置语言"""
        language_manager.set_language("zh-CN")
    
    def test_realm_translation(self):
        """测试境界相关的翻译"""
        from src.classes.cultivation import Realm
        
        language_manager.set_language("zh-CN")
        # 测试境界名称翻译
        assert t("qi_refinement") == "练气"
        assert t("foundation_establishment") == "筑基"
        
        language_manager.set_language("en-US")
        assert t("qi_refinement") == "Qi Refinement"
        assert t("foundation_establishment") == "Foundation Establishment"
    
    def test_gender_translation(self):
        """测试性别翻译"""
        language_manager.set_language("zh-CN")
        assert t("male") == "男"
        assert t("female") == "女"
        
        language_manager.set_language("en-US")
        assert t("male") == "Male"
        assert t("female") == "Female"
    
    def test_alignment_translation(self):
        """测试阵营翻译"""
        language_manager.set_language("zh-CN")
        assert t("righteous") == "正"
        assert t("neutral") == "中立"
        assert t("evil") == "邪"
        
        language_manager.set_language("en-US")
        assert t("righteous") == "Righteous"
        assert t("neutral") == "Neutral"
        assert t("evil") == "Evil"
    
    def test_weapon_type_translation(self):
        """测试武器类型翻译"""
        language_manager.set_language("zh-CN")
        assert t("sword") == "剑"
        assert t("saber") == "刀"
        assert t("spear") == "枪"
        
        language_manager.set_language("en-US")
        assert t("sword") == "Sword"
        assert t("saber") == "Saber"
        assert t("spear") == "Spear"
    
    def test_action_names_translation(self):
        """测试动作名称翻译"""
        language_manager.set_language("zh-CN")
        assert t("cultivate_action_name") == "修炼"
        assert t("breakthrough_action_name") == "突破"
        assert t("attack_action_name") == "发起战斗"
        
        language_manager.set_language("en-US")
        assert t("cultivate_action_name") == "Cultivate"
        assert t("breakthrough_action_name") == "Breakthrough"
        assert t("attack_action_name") == "Initiate Battle"
    
    def test_effect_names_translation(self):
        """测试效果名称翻译"""
        language_manager.set_language("zh-CN")
        assert t("effect_extra_max_hp") == "最大生命值"
        assert t("effect_extra_max_lifespan") == "最大寿元"
        
        language_manager.set_language("en-US")
        assert t("effect_extra_max_hp") == "Max HP"
        assert t("effect_extra_max_lifespan") == "Max Lifespan"
    
    def test_parameterized_translation_chinese(self):
        """测试带参数的中文翻译"""
        language_manager.set_language("zh-CN")
        
        result = t("{name} obtained {amount} spirit stones", 
                  name="张三", amount=100)
        assert "张三" in result
        assert "获得灵石" in result
        assert "100" in result
    
    def test_parameterized_translation_english(self):
        """测试带参数的英文翻译"""
        language_manager.set_language("en-US")
        
        result = t("{name} obtained {amount} spirit stones",
                  name="Zhang San", amount=100)
        assert "Zhang San" in result
        assert "obtained" in result
        assert "spirit stones" in result
        assert "100" in result


class TestI18nConsistency:
    """测试国际化的一致性"""
    
    def test_all_enum_translations_exist(self):
        """测试所有枚举类型的翻译都存在"""
        language_manager.set_language("zh-CN")
        
        # 测试主要枚举类型
        enum_keys = [
            # 境界
            "qi_refinement", "foundation_establishment", "core_formation", "nascent_soul",
            # 阶段
            "early_stage", "middle_stage", "late_stage",
            # 性别
            "male", "female",
            # 阵营
            "righteous", "neutral", "evil",
            # 武器类型
            "sword", "saber", "spear", "staff", "fan", "whip", "zither", "flute", "hidden_weapon",
            # 关系
            "parent", "child", "sibling", "kin", "master", "apprentice", "lovers", "friend", "enemy",
        ]
        
        missing = []
        for key in enum_keys:
            result = t(key)
            # 如果翻译失败，会返回原始键
            if result == key:
                missing.append(key)
        
        if missing:
            pytest.fail(f"以下枚举键缺少中文翻译: {', '.join(missing)}")
    
    def test_format_string_consistency(self):
        """测试格式化字符串在中英文中的参数一致性"""
        from pathlib import Path
        import re
        
        zh_po = Path("src/i18n/locales/zh_CN/LC_MESSAGES/messages.po")
        en_po = Path("src/i18n/locales/en_US/LC_MESSAGES/messages.po")
        
        if not zh_po.exists() or not en_po.exists():
            pytest.skip("PO files not found")
        
        def extract_msgid_msgstr_pairs(po_file):
            """提取 msgid 和 msgstr 对"""
            content = po_file.read_text(encoding='utf-8')
            pairs = {}
            
            lines = content.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if line.startswith('msgid "') and line != 'msgid ""':
                    msgid = line[7:-1]  # 提取引号内的内容
                    
                    # 查找对应的 msgstr
                    i += 1
                    while i < len(lines) and not lines[i].strip().startswith('msgstr '):
                        i += 1
                    
                    if i < len(lines):
                        msgstr = lines[i].strip()[8:-1]  # 提取引号内的内容
                        pairs[msgid] = msgstr
                i += 1
            
            return pairs
        
        zh_pairs = extract_msgid_msgstr_pairs(zh_po)
        en_pairs = extract_msgid_msgstr_pairs(en_po)
        
        # 检查格式化参数
        inconsistent = []
        for msgid in zh_pairs:
            if msgid in en_pairs:
                # 提取格式化参数 {param}
                zh_params = set(re.findall(r'\{(\w+)\}', zh_pairs[msgid]))
                en_params = set(re.findall(r'\{(\w+)\}', en_pairs[msgid]))
                msgid_params = set(re.findall(r'\{(\w+)\}', msgid))
                
                # 检查中英文翻译的参数是否与原始 msgid 一致
                if zh_params != msgid_params or en_params != msgid_params:
                    inconsistent.append({
                        'msgid': msgid,
                        'msgid_params': msgid_params,
                        'zh_params': zh_params,
                        'en_params': en_params
                    })
        
        if inconsistent:
            msg = "\n发现格式化参数不一致的翻译:\n"
            for item in inconsistent[:5]:
                msg += f"  msgid: {item['msgid'][:50]}...\n"
                msg += f"    原始参数: {item['msgid_params']}\n"
                msg += f"    中文参数: {item['zh_params']}\n"
                msg += f"    英文参数: {item['en_params']}\n"
            if len(inconsistent) > 5:
                msg += f"  ... 还有 {len(inconsistent) - 5} 个\n"
            pytest.fail(msg)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
