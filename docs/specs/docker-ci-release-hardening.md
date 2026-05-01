# Docker 与生产前端 CI 防线说明

本文档记录当前已经落地的 Docker 部署与生产前端构建 CI 防线。它不再是待实施计划，而是维护这些检查时的参考。

## 当前状态

Issue #196 暴露过一次 Docker 部署后浏览器黑屏的问题，原因是生产前端产物在真实浏览器中执行时报错。为避免这类问题复发，仓库现在保留两层 CI：

1. `.github/workflows/test.yml`
   - 后端全量 pytest。
   - 前端 `npm run type-check`。
   - 前端 `npm run test:coverage`。
   - 前端 `npm run build`。
   - Playwright 生产前端 smoke：`npm run smoke:production`。
2. `.github/workflows/docker-smoke.yml`
   - `docker compose build`。
   - `pytest -m docker tests/test_docker_runtime_smoke.py -v`。
   - Docker 前端浏览器 smoke：通过 nginx 入口访问 `http://127.0.0.1:8123` 并运行 Playwright。

配套 contract / smoke 测试主要包括：

- `tests/test_docker_build_contract.py`
- `tests/test_data_paths_runtime_contract.py`
- `tests/test_docker_runtime_smoke.py`
- `tests/test_nginx_proxy_contract.py`
- `tests/test_server_binding.py`
- `web/e2e/production-smoke.spec.ts`

## 覆盖目标

当前 CI 需要持续覆盖以下风险：

1. 前端生产构建成功，但真实浏览器执行 JS 后黑屏。
2. Docker 镜像构建成功，但运行镜像缺少 runtime 依赖。
3. 前端容器健康检查只命中静态首页，无法证明 backend 代理链路可用。
4. `CWS_DATA_DIR=/data` 持久化失效，导致 settings / secrets / saves / logs 在容器重建后丢失。
5. Docker 场景中 WebSocket 断开或无人连接导致容器自动退出。
6. nginx、静态资源路径、前端生产 bundle 与 backend API 代理之间出现断链。

## 维护约束

修改 Docker、部署、前端生产构建或持久化语义时，应同步维护：

1. Dockerfile / compose / nginx 配置。
2. 不依赖 Docker daemon 的 contract 测试。
3. 依赖 Docker 的 smoke 测试。
4. `README.md` 与 `docs/readme/*.md` 中的部署说明。

生产镜像只应安装 runtime dependencies；不要把 `pytest` 等测试依赖装入运行镜像。Docker 运行时用户数据统一由 `CWS_DATA_DIR` 决定，不要重新依赖旧的 `/app/assets/saves`、`/app/logs` 等运行目录。

## 失败诊断产物

Docker 相关 workflow 失败时应尽量保留以下 artifact：

1. `docker compose ps`
2. backend / frontend 容器日志
3. Playwright report、trace、screenshot
4. `web/dist` 文件列表

这些信息用于快速判断问题属于 backend 启动、nginx 代理、静态资源、生产 JS 执行，还是首屏渲染。

## 发布前建议

发布前建议至少确认以下命令在 CI 或本地通过：

```bash
pytest
cd web && npm run type-check
cd web && npm run test
cd web && npm run build
cd web && npm run smoke:production
pytest -m docker tests/test_docker_runtime_smoke.py -v
```

如果本地没有 Docker，以 GitHub Actions 的 `Docker Smoke` workflow 作为 Docker 发布前确认入口。
