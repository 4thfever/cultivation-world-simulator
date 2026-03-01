---
description: Guide for module registration when creating new actions, mutual actions or gatherings
globs: src/classes/**/*.py
---

# 模块注册规范 (Module Registration)

当你在本项目中创建一个新的类（Class）并使用了某种注册装饰器（如 `@register_action`, `@register_mutual_action`, `@register_gathering`, `@register_item` 等）时，由于 Python 模块导入机制的限制，你必须遵循以下规范，以防止你的注册无效。

## 1. 核心要求：修改 `__init__.py`

**必须**在同级目录（或上级目录管理导出的地方）的 `__init__.py` 中导入该模块。因为 Python 的装饰器在模块未被 import 的情况下不会执行，否则游戏在运行时将找不到你新写的类。

例如，如果你新建了 `src/classes/action/new_action.py`，你必须在 `src/classes/action/__init__.py` 中添加：
```python
from .new_action import NewAction
```

如果你新建了 `src/classes/gathering/new_gathering.py`，你必须在 `src/classes/gathering/__init__.py` 中添加：
```python
from .new_gathering import NewGathering
```

如果你新建了 `src/classes/mutual_action/new_mutual_action.py`，你必须在 `src/classes/mutual_action/__init__.py` 中添加：
```python
from .new_mutual_action import NewMutualAction
```

## 2. 测试要求：新增注册验证测试

为了确保模块注册成功并且不会在未来被不小心移除，**必须**在 `tests/` 下为你的新模块编写的测试文件中，加入一个验证是否注册成功的测试用例：

```python
def test_new_action_registered():
    # 示例：如果是 action
    from src.classes.action.registry import ACTION_REGISTRY
    assert "NewAction" in ACTION_REGISTRY
    
    # 示例：如果是 gathering
    # from src.classes.gathering.gathering import GatheringManager
    # manager = GatheringManager()
    # assert any(isinstance(g, NewGathering) for g in manager.gatherings)
```

## 3. Vibe Coding 检查清单

在完成新特性的核心代码编写后，请核对以下列表：
1. [ ] 新文件是否包含 `@register_xxx` 装饰器？
2. [ ] 是否已经在对应的 `__init__.py` 里加入了 `from .module import Class`？
3. [ ] 是否跑过了相关测试或者自己手动测试过确认该事件/行为能在系统里被读取？
