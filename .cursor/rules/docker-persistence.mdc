---
description: 约束 Docker 部署下的数据持久化、服务生命周期与回归测试
globs: docker-compose.yml, deploy/Dockerfile.backend, deploy/Dockerfile.frontend, deploy/nginx.conf, src/config/data_paths.py, src/server/main.py, src/utils/config.py, tests/test_docker_build_contract.py, tests/test_data_paths_runtime_contract.py, tests/test_docker_runtime_smoke.py, tests/test_nginx_proxy_contract.py, tests/test_server_binding.py, README.md, docs/readme/*.md
---
# Docker 运行与持久化规则

## 1. 数据真源
- 运行时用户数据（`settings/secrets/saves/logs/cache/incompatible`）必须统一落在 `CWS_DATA_DIR` 对应目录。
- 不要把 `assets/saves`、`/app/logs` 视为运行时持久化真源；它们只能作为历史兼容语义，不能替代 data root。

## 2. 服务生命周期
- Docker / Compose 场景中，容器生命周期必须由进程管理器控制；不要保留“最后一个 WebSocket 客户端断开后自动退出”这类桌面版行为。
- 若桌面版需要保留自动退出能力，必须通过显式环境变量或模式开关区分；Docker 部署默认必须关闭该行为。
- 健康检查应尽量反映真实可用性，不要只检查静态首页或仅证明 Nginx 进程存活。

## 3. Compose 契约
- `docker-compose.yml` 的 `backend` 必须显式设置 `CWS_DATA_DIR`。
- Docker Compose 的 `backend` 必须显式禁用自动空闲关机（当前约定：`CWS_DISABLE_AUTO_SHUTDOWN=1`）。
- `backend.volumes` 必须挂载 `CWS_DATA_DIR` 对应容器路径（当前约定为 `./docker-data:/data`）。
- 禁止仅保留 `./assets/saves:/app/assets/saves` 或 `./logs:/app/logs` 这类历史挂载而缺失 data root 挂载。
- `frontend.depends_on` 若依赖 `backend`，应优先等待 `service_healthy`，不要只依赖启动顺序。
- `frontend.healthcheck` 应通过代理链路验证后端可用性；当前推荐校验 `/api/v1/query/runtime/status`，不要只检查 `/`。

## 4. 镜像构建约束
- 后端生产镜像只安装运行时依赖，不要把 `pytest`、`pytest-cov`、`pytest-asyncio` 等测试依赖装进 runtime image。
- 运行时镜像不要创建或重新依赖 `/app/assets/saves`、`/app/logs` 这类旧目录来承载真实数据。
- 第三方镜像源可作为可覆盖选项，但默认构建路径应尽量使用稳定、通用的官方源，避免 CI 依赖单一地区镜像。

## 5. 配置注入约束
- `src/utils/config.py` 中 `CONFIG.paths.saves` 必须由 `get_data_paths().saves_dir` 注入，禁止改回静态路径。
- 调整 `src/config/data_paths.py` 时，必须保持 `settings/secrets/saves/logs/cache/incompatible` 都在同一 data root 下。

## 6. 测试门禁
- Docker 路径或 compose 相关变更，必须更新并通过：
  - `tests/test_docker_build_contract.py`
  - `tests/test_data_paths_runtime_contract.py`
- 涉及容器生命周期、自动退出或启动绑定逻辑变更时，必须更新并通过：
  - `tests/test_server_binding.py`
- 涉及代理配置变更，必须更新并通过：
  - `tests/test_nginx_proxy_contract.py`
- 涉及持久化语义变更时，优先扩展 `tests/test_docker_runtime_smoke.py`，至少覆盖一个真实运行态数据（如 settings、secrets、save 或 load）跨容器重建仍可用。
- 发布前建议执行：
  - `pytest -m docker tests/test_docker_runtime_smoke.py`

## 7. 文档一致性
- Docker 持久化约定（如 `CWS_DATA_DIR`、挂载目录）发生变化时，必须同步更新：
  - `README.md`
  - `docs/readme/*.md`
- 文档至少要明确四件事：数据真源目录、宿主机挂载目录、容器重建后的数据保留行为、容器不会因无人连接而自动退出。
