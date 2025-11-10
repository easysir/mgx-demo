# MGX Monorepo

这一仓库采用 monorepo 结构，集中管理 MGX MVP 的后端、前端以及共享模块。顶层通过 pnpm workspace + Turborepo 协调多语言项目，便于统一脚本、缓存和依赖治理。

## 目录结构

```
apps/
  backend/     # FastAPI 服务
  frontend/    # Next.js Web 客户端
packages/
  shared/      # 前后端共享的 TypeScript 包
tools/
  scripts/     # 辅助脚本 (bootstrap、lint、release 等)
docs/          # 设计与规范文档
```

## 快速开始

### 初始化
```bash
corepack enable
COREPACK_ENABLE_STRICT=0 corepack prepare pnpm@9.12.2 --activate
pnpm run setup   # 自动安装 Node 依赖 + 创建 ~/venvs/mgx 并安装后端依赖
```

### Docker 前置
- 本地需安装并启动 Docker Desktop 或兼容的 Docker Engine（>= 24.x）。
- 确保当前用户具备 `docker` 命令权限，执行 `docker ps` 能正常返回结果。
- 默认沙箱数据会挂载到 `/tmp/mgx/sandboxes/<session_id>`，如需更改可在后端设置 `SANDBOX_BASE_PATH` / `SANDBOX_PROJECT_ROOT` 环境变量。
- 若需限制沙箱资源，可设置 `SANDBOX_CPU` / `SANDBOX_MEMORY` 等变量后再启动后端。

### 启动
- 前端：`pnpm run dev:frontend`（Next.js dev server，默认 http://localhost:3000）
- 后端：`pnpm run dev:backend`（uvicorn + FastAPI，健康检查 http://127.0.0.1:8000/healthz）
- Agents Runtime：无需单独启动，随 FastAPI 服务一起初始化；当后续拆为独立微服务时再更新启动命令。
- 前后端并行：`pnpm dev`（Turbo 并行拉起各 dev 命令）

## Agent Runtime 亮点

- **配置化角色 + 动态编排**：`agents/config/registry.py` 注册所有角色及默认工具，`workflows/orchestrator.py` 由 Mike 驱动的状态机根据 LLM 决策实时指派下一位 Agent 并收尾，便于扩编或替换流程。
- **流式执行链路**：`LLMService` 现已默认走 Deepseek（`DEEPSEEK_API_KEY` / `AGENT_LLM_DEEPSEEK_MODEL`），未配置时自动回退到占位响应；仍可按需自定义其它 provider。异常统一抛出，token/status/error 通过 `/api/ws/sessions/{id}` WebSocket 推送，让 ChatUI 实时刷新。
- **统一会话接口**：`SessionStore`（MVP 阶段为内存实现）负责记录当前会话，REST 历史接口与流式事件共享 message_id，方便刷新或追踪；后续会替换为 PostgreSQL/Redis 持久化。

## 项目约定

- **包管理**：采用 `pnpm`，所有 Node 包需声明在对应子包中。
- **任务调度**：`turbo.json` 维护 dev/build/lint/publish 流程，可在子项目内扩展。
- **Python 环境**：推荐 `uv` 或 `poetry` 管理虚拟环境，默认配置位于 `apps/backend/pyproject.toml`。
- **共享资源**：跨项目逻辑优先沉淀到 `packages/`，通过相对依赖引用，保持实现一致。

更多细节请参考 `docs/design` 与 `docs/codex`。
