# i18n 测试说明

## 概述

针对 `src/classes/` 的本地化工作，本项目添加了以下测试逻辑来确保国际化的质量和完整性。

## 测试文件

### 1. ✅ `test_i18n_duplicates.py` - PO 文件重复项检查

**状态**: 已创建并通过测试

**功能**:
- 检查中英文 PO 文件中是否有重复的 msgid
- 检查中英文 msgid 数量是否一致
- 检查中英文 msgid 键是否完全匹配

**特点**:
- 独立运行，不依赖 conftest.py
- 快速执行（< 5秒）
- 适合 pre-commit hook

**运行方式**:
```bash
python tests/test_i18n_duplicates.py
```

---

### 2. ⚠️ `test_i18n_po_quality.py` - PO 文件质量和代码检查

**状态**: 已创建，发现需要修复的问题

**功能**:
- 🔍 检测硬编码的中文字符串（应使用 `t()` 函数）
- 🔍 检测代码中使用但 PO 文件中未定义的翻译键
- 🔍 检测格式化参数不一致问题

**特点**:
- 使用 AST 解析器静态分析代码
- 不依赖项目导入，避免循环依赖
- 提供详细的问题定位信息

**运行方式**:
```bash
python tests/test_i18n_po_quality.py
```

**当前发现的问题**:

#### 1. 硬编码中文字符串
主要在以下文件:
- `classes/appearance.py` - 外貌描述数据
- `classes/alignment.py` - 枚举注释
- `classes/animal.py` - 动物信息

**分析**:
- 大部分是**数据文件**中的内容（如 appearance.py 中的外貌描述）
- 一些是**枚举常量的注释**（可接受）

#### 2. 缺失的翻译键
代码中使用但 PO 文件中未定义，需要在两个 PO 文件中添加这些 msgid 及其翻译。

---

### 3. 📝 `test_i18n_classes_coverage.py` - Classes 模块深度测试

**状态**: (已移除，原版本依赖过时 API)

建议使用 `test_i18n_po_quality.py` 进行静态分析。

---

### 4. 🌍 `test_csv_i18n.py` - CSV 配置国际化测试

**状态**: 已创建并通过测试

**功能**:
- 测试 CSV 配置的单源加载机制（Single Source of Truth）
- 验证 `load_game_configs` 时自动注入翻译
- 测试中英文切换时配置值的正确变化
- 验证随机姓名生成器的国际化支持

**特点**:
- 包含 Mock 单元测试（无需真实文件）
- 包含集成测试（使用真实 `static/game_configs`）
- 覆盖了重构后的配置加载核心逻辑

**运行方式**:
```bash
python -m pytest tests/test_csv_i18n.py
```

---

## 推荐的工作流程

### 日常开发

```bash
# 1. 编写代码，使用 t() 函数
code = t("{name} obtained {amount} spirit stones", name=name, amount=100)

# 2. 运行快速检查（提交前）
python tests/test_i18n_duplicates.py
python tests/test_i18n_po_quality.py

# 3. 如果发现缺失的翻译，添加到 PO 文件

# 4. 重新运行测试确认
python tests/test_i18n_duplicates.py
```

### 大规模修改后

```bash
# 运行完整测试套件
python -m pytest tests/test_i18n_*.py -v
```

---

## 相关文件

- ✅ `tests/test_i18n_duplicates.py` - 重复项检查
- ✅ `tests/test_i18n_po_quality.py` - 质量检查
- ✅ `tests/README_i18n_tests.md` - 本文档
- ✅ `tools/i18n/check_po_duplicates.py` - 独立工具
