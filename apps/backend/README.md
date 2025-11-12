# Backend (FastAPI)

MGX 后端服务将提供认证、会话管理、Agent 编排、工具执行与预览相关 API。当前仓库仅包含最小 FastAPI 应用，后续根据 `docs/design` 逐步扩展。

## 本地运行

```bash
# 在仓库根目录
pnpm setup          # 一次性安装依赖并构建沙箱镜像（见 tools/scripts/bootstrap.sh）

cd apps/backend
uv sync             # 或 poetry install
uv run fastapi dev app.main:app --reload
```

## 目录规划

```
app/               # FastAPI 网关与轻量业务逻辑
  main.py
  api/             # REST / WebSocket 路由
  services/        # 认证、会话、会话存储
  models/          # Pydantic 模型

agents/            # Agent runtime（未来可拆成独立服务）
  config/          # Agent 注册表
  agents/          # 各角色 Agent（LLM/工具逻辑）
  tools/           # Tool executors
  workflows/       # Mike 编排策略
  runtime/         # Orchestrator, workflow 入口

shared/            # app 与 agents 共享的类型定义
```

> TODO: 待 Phase 2 落地真实 LLM/工具接口后，将 `agents/` 抽离为独立微服务，通过 RPC/消息队列与 `app/` 通信。

数据库迁移、任务调度、消息队列等模块将在后续迭代引入。

## 沙箱镜像

Agent 在执行写文件 / 预览任务时会使用独立的 Docker 沙箱。项目提供了一个基础镜像定义：

```
apps/backend/agents/docker/sandbox/Dockerfile
```

镜像特性：

- 基于 `node:20-bookworm`，预装 `pnpm` / `yarn` / `turbo` / `vite` / `next` / `pm2` 等常用前端工具；
- 安装 `build-essential`、`python3`、`git` 以及 `inotify-tools`、`watchman`，确保 HMR 可以在挂载卷下正常工作；
- 默认设置 `CHOKIDAR_USEPOLLING=1` 和 `WATCHPACK_POLLING=true`，适配 Vite/Next；
- 工作目录为 `/workspace`，容器启动后保持常驻，方便通过 `docker exec` 运行 dev server。

本地构建并推送镜像：

```bash
cd apps/backend/agents/docker/sandbox
docker build -t mgx-sandbox:latest .
# 可选：docker push <registry>/mgx-sandbox:latest
```

将 `SANDBOX_IMAGE` 指向构建好的镜像即可在网关中使用（详见 `app/services/container.py`）。
