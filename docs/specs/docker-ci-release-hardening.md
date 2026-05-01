# Docker 与生产前端 CI 防线方案

本文档记录 Docker 部署与生产前端构建的 CI 防线设计。目标是：维护者本地即使没有 Docker，也能在 push、PR、release 前通过 GitHub Actions 尽早发现“构建能过但浏览器黑屏”“镜像能起但代理/持久化不可用”等问题。

## 1. 背景

Issue #196 暴露的问题是：Docker 部署后浏览器黑屏，控制台报：

```text
Cannot access lexical declaration before initialization
```

该问题本质是前端生产构建产物的 chunk 初始化顺序问题。开发模式和普通单元测试不一定会暴露，必须用“生产构建 + 真实浏览器执行 JS”才能稳定发现。

因此 CI 不能只覆盖后端 pytest 和前端 vitest，还需要补齐以下层级：

1. 前端生产构建。
2. 非 Docker 的生产页面浏览器 smoke。
3. Docker compose 运行时 smoke。
4. Docker 下的前端浏览器 smoke。
5. 发布前手动完整验证入口。

## 2. 总体原则

1. 本地无 Docker 不阻塞开发，Docker 相关验证放到 GitHub Actions。
2. PR 阶段优先跑快速、稳定、能抓高频问题的检查。
3. main / release 阶段再跑耗时更长的 Docker compose smoke。
4. 所有 smoke 都应检查“真实可用性”，不要只检查静态首页返回 200。
5. 前端黑屏类问题必须通过真实浏览器捕获 `pageerror` 和 console error。
6. Docker 健康检查继续以 backend 代理链路为准，避免 frontend 只返回 nginx 静态页就算健康。

## 3. 建议 CI 列表

### 3.1 `backend-tests`

触发：

- pull_request
- push to main

命令：

```bash
pytest -n auto --dist loadfile -v --cov=src --cov-report=xml --cov-report=term --cov-fail-under=60
```

目的：

- 保持现有 Python 单元测试与集成测试覆盖。
- 覆盖 Docker contract 测试中不依赖 Docker daemon 的部分。

注意：

- `tests/test_docker_build_contract.py` 应继续纳入普通 pytest。
- 不依赖本地 Docker 的部署契约，例如 Dockerfile COPY、runtime requirements、compose healthcheck、frontend chunk 策略，应放在普通测试里。

### 3.2 `frontend-tests`

触发：

- pull_request
- push to main

命令：

```bash
cd web
npm ci
npm run type-check
npm run test:coverage
npm run build
```

目的：

- `type-check` 抓类型错误。
- `vitest` 抓前端单元行为。
- `npm run build` 抓生产构建失败、跨目录静态资源导入失败、Vite/Rollup 基础错误。

注意：

- `npm run build` 是必须项。只跑 `type-check` 和 `vitest` 不足以防生产产物问题。

### 3.3 `frontend-production-smoke`

触发：

- pull_request
- push to main

建议工具：

- Playwright Chromium

步骤：

```bash
cd web
npm ci
npm run build
npm run preview -- --host 127.0.0.1 --port 4173
```

浏览器检查：

1. 打开 `http://127.0.0.1:4173/`。
2. 监听 `pageerror`，出现任何未捕获异常则失败。
3. 监听 console error，出现非白名单错误则失败。
4. 检查 `#app` 存在且文本或子节点非空。
5. 检查至少一个稳定启动界面元素可见，例如系统菜单、开始入口、loading overlay 或主场景容器。

目的：

- 在不使用 Docker 的情况下，执行真实生产 JS。
- 直接覆盖 Issue #196 这类“build 成功但浏览器执行崩溃”的问题。

建议测试文件：

- `web/src/__tests__/e2e/productionSmoke.spec.ts`，或
- `web/e2e/production-smoke.spec.ts`

### 3.4 `docker-build`

触发：

- pull_request 中当 Docker 相关文件、前端构建配置、静态资源路径、requirements 改动时运行。
- push to main 必跑。

建议路径过滤：

- `docker-compose.yml`
- `deploy/**`
- `requirements*.txt`
- `src/config/**`
- `src/server/**`
- `web/**`
- `static/locales/registry.json`
- `static/game_configs/world_info.csv`

命令：

```bash
docker compose build
```

目的：

- 确认 backend/frontend 镜像都能构建。
- 抓 Dockerfile COPY 漏文件、生产依赖漏装、前端构建上下文缺失等问题。

注意：

- 该 job 不要求本地可运行，放 GitHub Actions 即可。

### 3.5 `docker-runtime-smoke`

触发：

- push to main
- release tag
- workflow_dispatch

命令：

```bash
pytest -m docker tests/test_docker_runtime_smoke.py
```

已有覆盖：

- `docker compose up -d --build`
- backend runtime status
- settings 持久化
- LLM secrets 状态
- 开局
- 存档
- recreate 后 settings/secrets/saves 保留
- 读档

建议增强：

1. 失败时同时收集 frontend logs：

```bash
docker compose logs --no-color frontend
```

2. 等待 frontend 代理健康接口：

```text
http://localhost:8123/api/v1/query/runtime/status
```

3. 检查 nginx 入口返回 `index.html`：

```text
http://localhost:8123/
```

目的：

- 覆盖容器生命周期、backend runtime、数据持久化、代理链路。

### 3.6 `docker-frontend-browser-smoke`

触发：

- push to main
- release tag
- workflow_dispatch

依赖：

- `docker compose up -d --build`
- Playwright Chromium

浏览器检查：

1. 打开 `http://localhost:8123/`。
2. 监听 `pageerror`。
3. 监听 console error。
4. 检查 `#app` 非空。
5. 检查页面不是纯黑空白：可以读取 body 文本、关键节点、或截图像素非单色。
6. 检查 `/api/v1/query/runtime/status` 通过 frontend nginx 代理返回 ok。

目的：

- 覆盖 Docker frontend image、nginx、静态资源路径、生产 JS 执行。
- 这是最直接防止 Docker 部署黑屏复发的检查。

注意：

- 该 job 可以和 `docker-runtime-smoke` 合并，减少重复启动 compose。
- 如果合并，应在同一个 job 中先做 API/runtime 检查，再做浏览器 smoke，最后 `docker compose down`。

### 3.7 `release-gate`

触发：

- workflow_dispatch
- tag push，例如 `v*`

应包含：

1. `backend-tests`
2. `frontend-tests`
3. `frontend-production-smoke`
4. `docker-build`
5. `docker-runtime-smoke`
6. `docker-frontend-browser-smoke`

目的：

- 发 GitHub release / Docker 包之前，提供一个完整绿灯入口。
- 维护者本地没有 Docker 时，以此作为发布前最终确认。

## 4. 优先落地顺序

### P0：立即补齐

1. 在现有 `.github/workflows/test.yml` 中加入 `npm run build`。
2. 新增 `frontend-production-smoke`，用 Playwright 打开 `vite preview`。
3. 保留并扩展普通 Docker contract 测试，继续防止危险构建配置回归。

原因：

- 不需要 Docker。
- PR 阶段即可发现生产前端黑屏。
- 成本低，收益高。

### P1：GitHub 上跑 Docker

1. 新增单独 workflow 或 job：`docker-build`。
2. 新增或启用 `pytest -m docker tests/test_docker_runtime_smoke.py`。
3. 失败时上传 compose logs 作为 artifact。

原因：

- 本地无 Docker 不影响。
- GitHub runner 自带 Docker 环境，适合做真实部署验证。

### P2：Docker 浏览器端到端

1. 在 Docker smoke 中加入 Playwright。
2. 打开 `http://localhost:8123/`。
3. 捕获 console/pageerror。
4. 保存失败截图、浏览器 console 日志、frontend/backend 容器日志。

原因：

- 这是对“用户打开浏览器黑屏”的直接模拟。
- 比只 curl 健康接口更接近真实用户。

## 5. 失败诊断产物

Docker 相关 job 失败时应上传以下 artifact：

1. `docker compose ps`
2. `docker compose logs --no-color backend`
3. `docker compose logs --no-color frontend`
4. Playwright screenshot
5. Playwright trace 或 console log
6. `web/dist/index.html`
7. `web/dist/web_static` 文件列表

这些产物能快速判断：

- 是 backend 未启动。
- 是 nginx 代理失败。
- 是静态资源 404。
- 是生产 JS 执行错误。
- 是页面渲染了但首屏不可见。

## 6. 对 Issue #196 的专项预防

为防止 `vendor-vue` / `vendor-ui` 一类强制拆包再次导致生产黑屏：

1. 普通 contract 测试应禁止重新引入已知危险 chunk 名。
2. `frontend-production-smoke` 必须监听 `pageerror`。
3. Docker 浏览器 smoke 必须打开真实 `localhost:8123` 页面。
4. 前端构建配置中如需新增 `manualChunks`，应优先保持同一库生态的强依赖在同一依赖图内，不要把 Vue runtime 与依赖 Vue 的 UI 框架强行拆到互相独立的 vendor chunk。

## 7. 推荐最终 workflow 结构

建议拆成两个 workflow：

### `.github/workflows/test.yml`

用于 PR 和 main：

- `backend-tests`
- `frontend-tests`
- `frontend-production-smoke`

### `.github/workflows/docker-smoke.yml`

用于 main、tag、手动触发：

- `docker-build`
- `docker-runtime-and-browser-smoke`

这样普通 PR 反馈速度较快，发布前又有真实 Docker 兜底。

## 8. 验收标准

完成后，维护者不需要本地 Docker，也能通过 GitHub Actions 确认：

1. 前端生产构建成功。
2. 生产构建页面能被真实浏览器打开。
3. Docker 镜像能构建。
4. Docker compose 能启动 backend/frontend。
5. frontend nginx 能代理 backend API。
6. Docker 页面不是黑屏，且无未捕获 JS 异常。
7. settings/secrets/saves 在容器重建后仍持久化。

