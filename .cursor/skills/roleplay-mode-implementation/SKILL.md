---
name: roleplay-mode-implementation
description: 规划、实现或重构角色扮演模式（默认上帝视角下的单角色接管）时使用。适用于一期文本决策、二期统一有限选择框架、三期依附 Conversation 动作的自由对话，以及对应的 runtime/API/frontend/test 收口。
---

## 适用场景

当任务涉及以下任一方向时使用本技能：

- 实现或重构角色扮演模式
- 调整 `RoleplaySession`、`pending_request`、`conversation_session`
- 给一期文本决策补能力或修回归
- 给二期 `single_choice` / mutual action choice 接玩家接管
- 给三期 `Conversation` 对话链、summary、dock chat UI 做改动

## 先确认什么

1. 这次改动属于一期、二期还是三期？
2. 这次改动是在补主链，还是在做收尾/UI/测试？
3. 是否会影响 runtime 暂停语义、存档语义、continuation 语义？
4. 是否正在无意中把“上帝视角下的单角色接管”做回成独立个人模式？

## 必守心智

### 1. 默认始终是上帝视角

- 不把个人扮演做成与上帝模式并列的全局模式。
- 玩家扮演时仍可观察全世界，不做信息收窄。

### 2. 只在决策边界暂停

- 不能打断执行到一半的动作链。
- 只能在“当前动作已空 + planned actions 已空，需要新决策”时等待玩家。

### 3. 扮演态不进存档

- `RoleplaySession`
- `pending_request`
- `conversation_session`
- choice continuation

以上都属于 runtime，必须在 `load / reinit / reset / start` 后清空。

### 4. 二期优先走统一有限决策框架

- 不在每个业务点散落 `if roleplay ... else ...`
- 优先让业务层只保留：
  - `build_request()`
  - `apply_decision(...)`
- 决策来源交给统一 resolver / continuation

### 5. 三期对话必须依附 `Conversation`

- 不新增脱离动作语义的自由聊天入口
- 玩家只控制一侧发言，对方仍由 LLM 回复
- 原始聊天记录不进长期事件流，只以 summary 落地

## 推荐工作流

### 1. 先看锚点文档

优先查看：

- `docs/specs/avatar-roleplay-mode.md`
- `docs/specs/single-choice-unified-framework.md`
- `.cursor/rules/roleplay-mode.mdc`

如果改动涉及外接 API，再补看：

- `docs/specs/external-control-api.md`
- `.cursor/rules/external-control-api.mdc`

### 2. 再看当前落点

后端常见入口：

- `src/server/runtime/session.py`
- `src/server/services/roleplay_service.py`
- `src/server/api/public_v1/command.py`
- `src/server/api/public_v1/query.py`
- `src/systems/single_choice/**/*.py`
- `src/classes/mutual_action/conversation.py`

前端常见入口：

- `web/src/stores/roleplay.ts`
- `web/src/components/game/RoleplayDock.vue`
- `web/src/components/game/roleplay/*.vue`
- `web/src/api/modules/avatar.ts`
- `web/src/types/api.ts`

### 3. 判断改动层级

- 改运行时语义：优先改 runtime/service，不要先改 UI
- 改 API：先定 query/command 边界和 DTO
- 改二期选择：先看能否接入统一 choice resolver
- 改三期对话：先看是否仍依附 `Conversation`

## 实现检查清单

### 一期

1. 是否仍是 `decision` 型 request？
2. 是否保持“无效输入不恢复世界运行”？
3. 是否在动作链结束才创建 pending request？

### 二期

1. 是否复用统一 `choice` 请求？
2. 是否通过统一 continuation 恢复流程？
3. 是否避免在业务场景里硬编码 roleplay 分支？

### 三期

1. 是否由 `Conversation` 动作触发？
2. 是否保持“玩家一句、LLM 一句”？
3. 是否只有玩家能结束？
4. 是否只把 summary 落到长期事件流？

## 前端约束

- `RoleplayDock` 应维持统一骨架：
  - Header
  - Active Request
  - Activity Stream
- `decision / choice / conversation` 只切 request body，不重新发明整页布局
- 事件流优先复用统一高密度 event list 组件

## 文档与测试

改动 roleplay 主链时，优先同步：

- `docs/specs/avatar-roleplay-mode.md`
- `docs/specs/single-choice-unified-framework.md`
- `.cursor/rules/roleplay-mode.mdc`
- `AGENTS.md`

建议至少运行：

```bash
pytest tests/test_public_api_v1.py tests/test_single_choice.py tests/test_action_social.py tests/test_mutual_actions.py -q
cd web && npm run type-check
cd web && npm run test
```
