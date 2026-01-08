# 单元测试指南

本文档旨在指导如何为《修仙模拟器》编写和维护单元测试。

## 目录结构

*   `tests/`: 所有的单元测试文件都应存放在此目录下。
*   `tests/conftest.py`: 包含全局共享的 Fixture 和 Helper 函数。
*   `tests/test_*.py`: 具体模块的测试文件。命名应与 `src` 下的模块对应，例如 `src/classes/action/buy.py` 对应 `tests/test_buy_action.py`。

## 运行测试

在项目根目录下运行：

```bash
pytest
```

或者运行特定文件：

```bash
pytest tests/test_buy_action.py
```

## 编写新测试

我们使用 `pytest` 框架。为了保持代码整洁（DRY），请遵循以下准则：

### 1. 使用共享 Fixture

不要在每个测试文件中重复创建测试用的 Avatar、Map 或 Item。请使用 `tests/conftest.py` 中提供的 Fixture：

*   `base_world`: 提供一个基础的游戏世界环境。
*   `dummy_avatar`: 提供一个标准的测试用角色（位于(0,0)，练气期，男性）。
*   `avatar_in_city`: 基于 `dummy_avatar`，但已将其置于城市中，并给予 1000 灵石，且背包为空。
*   `mock_item_data`: 提供一组标准的 Mock 物品（丹药、材料、兵器、法宝）以及它们对应的 mock 字典结构，方便用于 patch `resolution` 模块。
*   `mock_llm_managers`: 自动 Mock 掉所有 LLM 调用，防止测试跑大模型。

**示例：**

```python
def test_my_feature(avatar_in_city, mock_item_data):
    # 直接使用准备好的角色
    assert avatar_in_city.magic_stone == 1000
    
    # 获取标准测试物品
    test_sword = mock_item_data["obj_weapon"]
    
    # ...
```

### 2. Mock 外部依赖

对于 Action 测试，通常需要 Mock `src.utils.resolution` 中的查找字典。请结合 `mock_item_data` 使用 `unittest.mock.patch`。

**示例：**

```python
from unittest.mock import patch

def test_action_logic(avatar_in_city, mock_item_data):
    materials_mock = mock_item_data["materials"]
    
    with patch("src.utils.resolution.materials_by_name", materials_mock):
        # 此时系统中只有 mock_item_data 里定义的材料是可见的
        action = MyAction(avatar_in_city, avatar_in_city.world)
        action.execute("铁矿石")
```

### 3. Action 测试模板

对于 `src.classes.action` 下的新 Action，建议测试以下三个方面：

1.  **`can_start` (前置条件检查)**:
    *   测试成功情况。
    *   测试各种失败情况（如不在正确地点、资源不足、目标不存在等），并断言返回的错误 `reason`。
2.  **`start` (事件生成)**:
    *   验证返回的 `Event` 对象包含正确的描述文本。
3.  **`_execute` (执行逻辑)**:
    *   验证对 Avatar 状态的修改（扣钱、加物品、扣血、加熟练度等）。
    *   验证对 World 状态的修改。

### 4. Helper 函数

如果需要创建特定的测试对象，优先查看 `conftest.py` 中的 helper 函数：
*   `create_test_material(...)`
*   `create_test_weapon(...)`
*   `create_test_elixir(...)`
*   `create_test_auxiliary(...)`

如果发现新的通用需求，请将其添加到 `conftest.py` 而不是在测试文件中复制粘贴。

## 常见问题

*   **`ModuleNotFoundError`**: 确保你的 IDE 或终端将项目根目录添加到了 `PYTHONPATH`。`pytest` 通常会自动处理这个问题。
*   **LLM 被调用了**: 确保你的测试（如果涉及 sim 循环）使用了 `mock_llm_managers` fixture，或者手动 patch 了相关模块。

