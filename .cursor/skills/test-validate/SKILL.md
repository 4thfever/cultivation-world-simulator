---
name: test-validate
description: 使用项目虚拟环境运行 Python 测试
---

## 命令

```bash
# 运行所有测试
.venv/bin/pytest

# 运行特定测试文件
.venv/bin/pytest tests/test_<name>.py -v

# 运行并生成覆盖率报告
.venv/bin/pytest --cov=src

# 运行服务器（开发模式）
.venv/bin/python src/server/main.py --dev
```

## 测试覆盖率指南

在进行代码更改后，考虑是否需要测试：

| 更改类型 | 测试建议 |
|-------------|---------------------|
| 修复 Bug | 添加回归测试以防止再次发生 |
| 新功能 | 单元测试 + 如果影响多个模块则添加集成测试 |
| 重构 | 现有测试应通过；如果行为改变则添加测试 |
| 配置/文档 | 通常不需要测试 |

对于 Bug 修复，确保测试在**修复前会失败**并且在**修复后会通过**。
