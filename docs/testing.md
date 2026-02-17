# 测试指南 (Testing Guide)

本文档旨在介绍本项目的测试架构、功能设计以及如何新增测试用例。

## 1. 测试文件结构

测试代码位于 `tests/` 目录下，主要结构如下：

*   `tests/conftest.py`: Pytest 的全局配置文件，包含了所有的全局 Fixture、Hook 和配置。这是理解测试环境构建的关键。
*   `tests/test_*.py`: 针对各个模块的单元测试和集成测试。
    *   `test_action_*.py`: 针对玩家行为（如修炼、战斗、移动等）的测试。
    *   `test_*.py`: 针对核心系统（如寿命、突破、经济系统等）的测试。
*   `tests/tools/`: 针对工具脚本的测试（如 i18n 构建检查）。
*   `tests/manual/`: 手动测试脚本（如有）。

## 2. 测试环境与功能设计

为了保证测试的稳定、快速和不污染开发环境，我们在 `tests/conftest.py` 中实现了以下机制：

### 2.1 环境隔离

*   **日志隔离 (`configure_test_logging`)**: 
    *   测试运行时的日志会被重定向到临时目录，防止污染项目根目录下的 `logs/` 文件夹。
    *   同时将日志输出到 `stderr`，以便 Pytest 捕获和显示（在测试失败时）。
*   **存档隔离 (`isolate_save_path`)**:
    *   测试期间产生的所有存档文件会被重定向到临时目录。
    *   通过 Monkeypatch 动态修改 `CONFIG.paths.saves`，确保测试互不干扰，且不影响本地真实存档。

### 2.2 确定性与稳定性

*   **固定随机种子 (`fixed_random_seed`)**:
    *   自动将 `random` 模块的种子固定为 `42`，确保每次运行测试时的随机行为一致。
*   **强制中文环境 (`force_chinese_language`)**:
    *   强制将游戏语言设置为简体中文 (`zh-CN`)，确保测试中断言的字符串匹配（如物品名称、提示信息）是稳定的。

### 2.3 核心 Mock 与 Fixture

为了避免测试依赖外部服务（如 LLM API）并简化测试编写，我们提供了以下核心 Fixture：

*   **`mock_llm_managers` (Autouse)**:
    *   **关键**: 自动 Mock 了所有涉及 LLM 调用的核心组件，包括 `llm_ai`, `StoryTeller`, `HistoryManager` 等。
    *   防止测试消耗 Token。
    *   防止测试因网络波动或 LLM 输出不稳定而失败。
    *   **使用**: 如果需要自定义 LLM 的返回值，可以在测试函数中接受 `mock_llm_managers` 参数并修改其 Mock 对象的 `return_value`。

*   **基础世界构建**:
    *   `base_map`: 创建一个 10x10 的全平原地图。
    *   `base_world`: 基于 `base_map` 创建的游戏世界实例。

*   **测试角色 (`dummy_avatar`)**:
    *   创建一个标准的测试角色：
        *   境界：练气期
        *   灵根：金灵根
        *   阵营：正道
        *   位置：(0, 0)
    *   **特点**: 清空了特质 (`personas`) 和功法，避免随机生成的属性干扰测试结果。

*   **城市角色 (`avatar_in_city`)**:
    *   基于 `dummy_avatar`，但位于城市中，且拥有初始资金，背包为空。适合测试购买、拍卖等城市内行为。

*   **测试物品 (`mock_item_data`)**:
    *   提供了一组标准的测试物品（丹药、材料、武器、法宝），方便在测试中直接分发给角色。

## 3. 如何新增测试

### 3.1 创建测试文件

在 `tests/` 目录下创建一个新的 `test_<模块名>.py` 文件。

### 3.2 编写测试用例

引入 `pytest` 和需要的模块。通常你只需要请求 `dummy_avatar` 或 `avatar_in_city` 即可开始测试。

#### 示例：测试一个新的动作

```python
import pytest
from src.classes.action import ActionStatus

# 如果是异步方法，使用 pytest.mark.asyncio
@pytest.mark.asyncio
async def test_my_new_action(dummy_avatar):
    # 1. 准备环境
    # 例如：给角色添加特定物品
    dummy_avatar.magic_stone = 100
    
    # 2. 执行动作
    # 假设有一个名为 do_something 的动作函数
    # result = await do_something(dummy_avatar)
    
    # 3. 断言结果
    # assert result.status == ActionStatus.SUCCESS
    # assert dummy_avatar.magic_stone == 0
```

### 3.3 处理 LLM 调用

虽然 `mock_llm_managers` 会自动拦截 LLM 调用，但有时你需要模拟特定的 LLM 回复。

```python
@pytest.mark.asyncio
async def test_action_with_llm(dummy_avatar, mock_llm_managers):
    # 获取 mock 对象
    mock_ai = mock_llm_managers["ai"]
    
    # 设定预期返回值
    mock_ai.decide.return_value = {"decision": "attack"}
    
    # 执行依赖 LLM 的代码...
    
    # 验证是否调用了 LLM
    mock_ai.decide.assert_called_once()
```

### 3.4 常用技巧

1.  **参数化测试**: 使用 `@pytest.mark.parametrize` 可以用不同的输入运行同一个测试逻辑，非常适合测试数值边界或不同的状态组合。
2.  **Mock 时间**: 如果测试涉及时间流逝，可以直接修改 `dummy_avatar.world.month_stamp` 或相关的时间属性。
3.  **检查日志**: 如果测试失败且原因不明，可以查看控制台输出的日志（已被重定向到 stderr）。

## 4. 运行测试

*   运行所有测试：
    ```bash
    pytest
    ```
*   运行指定文件的测试：
    ```bash
    pytest tests/test_my_feature.py
    ```
*   运行包含特定关键词的测试：
    ```bash
    pytest -k "cultivate"
    ```
