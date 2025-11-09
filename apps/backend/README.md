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
app/
  main.py          # 入口
  api/             # REST / WebSocket 路由
  agents/          # Agent 实现
  core/            # LLM、工具、会话、沙箱
  services/        # 业务服务
```

数据库迁移、任务调度、消息队列等模块将在后续迭代引入。

