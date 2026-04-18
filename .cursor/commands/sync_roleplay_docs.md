当用户调用此命令时，请同步整理“角色扮演模式（个人扮演模式）”相关的规则、技能、spec 和测试收尾项。

请严格执行以下流程：

1. **读取锚点文件**：
   - `docs/specs/avatar-roleplay-mode.md`
   - `docs/specs/single-choice-unified-framework.md`
   - `.cursor/rules/roleplay-mode.mdc`
   - `.cursor/skills/roleplay-mode-implementation/SKILL.md`
   - `AGENTS.md`

2. **核对是否需要同步更新**：
   - 若本次改动影响了角色扮演模式的长期约束，更新 `.cursor/rules/roleplay-mode.mdc`
   - 若本次改动影响了后续代理的推荐实现流程，更新 `.cursor/skills/roleplay-mode-implementation/SKILL.md`
   - 若本次改动影响了总体方案、分期边界或关键状态机，更新 `docs/specs/avatar-roleplay-mode.md`
   - 若本次改动影响了二期统一有限决策框架，更新 `docs/specs/single-choice-unified-framework.md`
   - 若 `.cursor` 中的 rule / skill 有变化，更新根目录 `AGENTS.md`

3. **核对实现语义是否仍然一致**：
   - 默认仍是上帝视角，不是独立“个人模式”
   - 同时最多只能扮演一个角色
   - 只在决策边界暂停，不能中断动作链
   - 扮演态、pending request、conversation session、continuation 不进存档
   - 二期优先走统一 choice resolver / continuation
   - 三期对话仍依附 `Conversation` 动作，原始聊天记录不进长期事件流

4. **补测试清单并执行回归**：
   - 后端至少检查：
     - `tests/test_public_api_v1.py`
     - `tests/test_single_choice.py`
     - `tests/test_action_social.py`
     - `tests/test_mutual_actions.py`
   - 前端至少检查：
     - `web/src/__tests__/components/game/RoleplayDock.test.ts`
     - `web/src/__tests__/components/game/roleplay/RoleplayViews.test.ts`
     - `web/src/__tests__/components/game/panels/info/components/RoleplayPanel.test.ts`
   - 运行：
     - `pytest tests/test_public_api_v1.py tests/test_single_choice.py tests/test_action_social.py tests/test_mutual_actions.py -q`
     - `cd web && npm run type-check`
     - `cd web && npm run test`

5. **完成后输出摘要**：
   - 本次是否更新了 rule / skill / spec / AGENTS
   - 本次影响的是一期、二期还是三期
   - 本次跑了哪些测试，哪些没跑

注意：

- 不要因为同步文档而擅自改动无关 spec。
- 如果只是实现细节调整，但没有改变长期约束，不要硬改 `.cursor/rules/roleplay-mode.mdc`。
- 如果改了 `.cursor/rules`、`.cursor/skills`、`.cursor/commands`，应同步更新 `AGENTS.md`。
