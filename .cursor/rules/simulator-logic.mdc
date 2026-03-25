---
description: 模拟器 (Simulator) 相位逻辑管理规范
globs: src/sim/simulator.py, src/sim/**/*.py
---

# 模拟器逻辑规范 (Simulator Logic)

本规范定义了模拟器步进 (Step) 过程中各个相位 (Phase) 的组织和执行方式。

## 1. 相位独立性 (Phase Independence)

- **每个相位必须是一个独立的函数或明确职责的调用单元**。
- 推荐将相位实现放在 `src/sim/simulator_engine/phases/*.py` 中，由模块函数承载具体业务逻辑。
- `Simulator.step()` 应保持为薄编排器，只负责按顺序调度 phase，不在其中展开业务细节。
- 如需共享单次 step 的运行时状态，优先通过 `SimulationStepContext` 传递，而不是继续给 `Simulator` 增加同名转发 wrapper。

## 2. 索引与顺序 (Indexing & Order)

- 每个相位在 `step()` 中必须关联一个 **整数索引 (Int Index)**。
- **全局索引刷新**: 当插入新的相位时，必须重新对所有相位进行编号（在注释中明确标注），确保顺序逻辑清晰且无跳号。
- 示例：
  ```python
  # 1. 感知更新
  ctx.add_events(world_phases.phase_update_perception_and_knowledge(self.world, ctx.living_avatars))
  # 2. 长期目标思考
  ctx.add_events(await lifecycle.phase_long_term_objective_thinking(ctx.living_avatars))
  # … 每年 1 月：先 update_sects，再按配置周期执行 phase_sect_periodic_thinking（宗门周期思考）
  ```
- **每年 1 月专属相位**：宗门周期思考必须在 `SectManager.update_sects()` 之后执行，并按 `thinking_interval_years` 决定是否在当年触发；生成结果写入 `periodic_thinking` 并写入事件流；详见 `sect-system.mdc` 第 8 节。

## 3. 异步执行规范 (Async Guidelines)

- 涉及 LLM 调用、复杂决策或大量并发计算的相位应标记为 `async`。
- 在 `step()` 中使用 `await` 调用异步相位。
- 内部实现优先使用 `asyncio.gather` 并行处理多个角色的逻辑，提高运行效率。

## 4. 生命周期与角色管理 (Lifecycle & Avatar Management)

- **存活缓存**: 在 `step()` 开始时获取 `living_avatars` 列表。
- **死亡结算**: 必须包含独立的死亡结算 phase，并在该阶段从 `living_avatars` 列表中移除已死亡的角色，防止后续相位继续处理。
- **状态流转**: 相位间优先通过 `SimulationStepContext` 中的 `living_avatars`、`events`、`processed_event_ids` 等字段同步状态。

## 5. 事件与交互处理 (Events & Interactions)

- **交互去重**: 使用 `processed_event_ids` 集合记录已处理过交互的事件，防止在后续交互处理相位中重复计算。
- **集中归档**: 每个相位返回产生的 `Event` 列表，由 `finalizer.finalize_step()` 统一进行去重、日志记录和入库。

## 6. Vibe Coding 检查清单

1. [ ] 新相位是否已提取为独立函数，并放在合适的 `phases` 模块中？
2. [ ] `step()` 方法中的相位注释索引是否已更新且连续？
3. [ ] 是否在死亡结算相位后正确维护了 `living_avatars` 列表？
4. [ ] 耗时逻辑是否已异步化并考虑了并发执行？
