# 贡献指南 (Contributing Guide)

感谢你对 **Cultivation World Simulator** (修仙模拟器) 感兴趣！欢迎任何形式的贡献，包括提出Bug、修复 Bug、改进文档或开发新功能。

> **重要**：任何新功能提交，特别是业务功能提交，请务必提前在 issue 中讨论清楚，得到维护者确认后，再进行贡献。
目前**不接受**重要的业务功能/代码设计模式的改动/重构。

在开始贡献之前，建议先查看 [项目路线图](./ROADMAP.md)，了解项目的发展方向和计划，这有助于你的贡献与项目目标保持一致。

为了保持代码库的健康和风格统一，请在贡献前阅读以下指南。

## 🛠️ 开发环境搭建

具体的安装和启动步骤请参考 [README.md](./README.md) 中的说明。

**项目结构说明：**
- **后端 (Python)**: 位于 `src/` 目录。
- **前端 (Vue 3)**: 位于 `web/` 目录。

## ✅ 测试要求 (必须)

在提交 Pull Request 之前，请务必确保所有测试通过。这是保证代码质量的关键。

**运行后端测试：**

本项目在 CI 环境中使用 Python 3.11。

1. 确保已安装测试依赖（包含在 requirements.txt 中）：
   ```bash
   pip install -r requirements.txt
   ```

2. 运行测试并检查覆盖率（需满足 60% 覆盖率要求）：
   ```bash
   pytest -v --cov=src --cov-report=term --cov-fail-under=60
   ```

**运行前端测试 (Vue/Vitest)：**

前端测试位于 `web/` 目录。

1. 进入前端目录并安装依赖：
   ```bash
   cd web
   npm install
   ```

2. 运行单元测试：
   ```bash
   npm run test:run
   ```

3. 运行测试并查看覆盖率：
   ```bash
   npm run test:coverage
   ```

请确保所有测试用例都能通过（PASS）。如果你添加了新功能，建议同时也添加相应的测试用例。

## 📝 代码规范

我们追求**简洁、优雅、清晰易读**的代码风格。

### Python 后端
- 遵循 PEP 8 风格指南。
- 如果新增了功能，请加入对应的pytest测试。

### Vue 前端
- 使用 **TypeScript** 编写逻辑。
- 遵循 Vue 3 Composition API 的最佳实践。
- 组件命名清晰，保持单一职责。

## 🚀 提交 Pull Request (PR)

1. **Fork** 本仓库到你的 GitHub 账户。
2. **Clone** 你的 Fork 版本到本地。
3. 创建一个新的分支进行开发：
   ```bash
   git checkout -b feature/你的功能名称
   # 或者
   git checkout -b fix/修复的问题
   ```
4. 提交你的更改 (Commit)，请使用清晰的提交信息。
5. 推送 (Push) 到你的远程分支。
6. 在 GitHub 上发起 **Pull Request**。

感谢你的贡献！一起打造更好玩有趣的AI修仙世界。