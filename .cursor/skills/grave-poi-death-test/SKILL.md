---
name: grave-poi-death-test
description: "通过真实游戏模拟验证角色死亡、墓碑 POI 创建、地图渲染和点击详情。用于需要测试寿元死亡或其他游戏内死亡流程、墓碑 POI，且不得直接调用 handle_death 的任务。"
---

# 墓碑死亡验证

以独立数据目录启动测试局，绝不污染用户当前存档或设置。死亡必须由 `Simulator.step()` 的正常结算路径产生，不能为了测试直接调用 `handle_death()`、手工注册墓碑或伪造死亡事件。

## 流程

1. 阅读 `docs/specs/external-control-api.md`，通过 `/api/v1/command/*` 创建或配置测试角色，不直接改 `game_instance`。
2. 为测试角色设置一个会自然到达的死亡条件。寿元死亡最稳定：创建高龄 avatar，再运行完整月度模拟步骤，直到死亡结算完成。
3. 如果完整模拟依赖 LLM，使用仅限本次测试的本地 OpenAI 兼容 stub；其数据目录、监听端口和进程名必须与正常开发服务隔离。
4. 通过 API 核对完整因果链：
   - 角色 detail 中 `is_dead` 为真，并包含 `death_info`。
   - `world/map` 的 `pois` 含 `kind: "grave"`，位置与死者死亡位置一致。
   - 墓碑摘要含 `deceased_avatar_id`，用作前端进入角色详情的关联。
5. 在实际前端地图中确认图标已加载、尺寸接近头像且可点击。点击墓碑应选中 `avatar` 并打开死者现有的角色详情，不应打开独立墓碑详情面板。

## 最小验证

```powershell
pytest tests/test_death.py
cd web
npm run type-check
npm run test -- src/__tests__/composables/useTextures.test.ts
```

UI 验证优先使用可用的浏览器控制工具；不可用时才以本地 Playwright 打开隔离的前端服务。不要用直接调用死亡处理函数来替代端到端验证。

## 清理

测试结束后先暂停测试局，再停止本次启动的前端、后端和 LLM stub 进程。删除本次专用的数据目录、stub、日志和截图；仅保留仓库内的正式实现与回归测试。清理前核对所有目标都位于仓库 `tmp/` 或 `web/tmp/`，不得触碰用户的常规数据目录或正在使用的服务。
