# Backend (FastAPI)

MGX 后端服务将提供认证、会话管理、Agent 编排、工具执行与预览相关 API。当前仓库仅包含最小 FastAPI 应用，后续根据 `docs/design` 逐步扩展。

## 本地运行

```bash
cd apps/backend
uv sync            # 或 poetry install
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
