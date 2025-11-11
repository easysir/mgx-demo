# MGX Monorepo

## 功能概述

MGX 是一套“对话式研发工作台”，用户只需在 Chat 面板描述需求，Mike 领衔的六人 AI 团队（Emma/Bob/Alex/David/Iris）便会协同完成需求分析、架构设计、编码到沙箱、数据/研究支持等任务：

- **实时流式反馈**：`LLMService` 调用 Deepseek/OpenAI 等模型并将 token/status/error 事件通过 WebSocket 推送到前端，使用户实时看到每个 Agent 的进度。
- **Docker 沙箱 + 预览**：`app/services/container.py` 管理 per-session 沙箱，文件变更会触发 watcher 推送；未来还将串联预览/圈选编辑，形成“对话 → 代码 → 预览”的闭环。

## 目录结构

```
apps/
  backend/
    app/        # FastAPI 网关（API、依赖、模型、服务）
    agents/     # 多 Agent Runtime（编排、LLM、工具、提示）
    shared/     # Python 侧共享模块/类型
  frontend/
    src/app/        # Next.js App Router（workspace page、auth 页面等）
    src/components/ # ChatPanel、EditorPanel、PreviewPanel 等 UI 组件
    src/lib/        # 调用后端 REST/WebSocket 的封装
packages/
  shared/      # 前后端共享的 TypeScript 类型与工具函数
tools/
  scripts/     # bootstrap/dev_backend/sync_backend 等脚本
docs/
  design/      # 系统设计、实施计划
  codex/       # 产品/技术总结
  prd/         # 产品需求文档
  api/         # 接口说明
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
```bash
# 单独启动
pnpm run dev:frontend   # Next.js dev server, http://localhost:3000
pnpm run dev:backend    # 使用 tools/scripts/dev_backend.sh 封装的 uvicorn

# 同时启动
pnpm dev                # Turbo run dev --parallel, 前后端并行
```
> 后端脚本会自动 source `~/venvs/mgx/bin/activate` 并执行 `uvicorn app.main:app --reload --factory`；如需修改端口或日志，可在 `tools/scripts/dev_backend.sh` 中扩展。

## 系统架构概览

> 详细背景参见 `docs/design/system_design.md` 与 `docs/codex/mgx_mvp_summary.md`。

- **前端工作区（Next.js 14 + shadcn/Tailwind）**：单页 Workspace， ChatPanel、文件树、Monaco 预留区与预览面板，并通过 REST + WebSocket 与后端同步会话/文件状态。
- **FastAPI 网关层**：`apps/backend/app` 暴露认证、会话、聊天、文件与沙箱接口，所有 HTTP/WebSocket 都经过 JWT 认证（`app/dependencies/auth.py`）；`stream.py` 负责房间广播流式 token/status/file_change 事件。
- **多 Agent 编排层**：`agents/workflows/orchestrator.py` 让 Mike 以状态机方式调度 Emma/Bob/Alex/David/Iris，`agents/llm/service.py` 提供统一 LLMService（默认 Deepseek（API 考量，演示用），可切换 provider），`agents/tools` 封装 ToolExecutor + file_write 等工具（后续待扩展）。
- **上下文管理与记忆**：`app/services/agent_runtime.py` 在每轮对话前为 WorkflowContext 组装三类 metadata —— 最近对话摘要、沙箱文件概览、最近写入的文档（PRD/调研/技术方案），并由各 Agent 的 `_compose_user_message` 注入 prompt，使多轮对话能够记住“刚才发生了什么”“沙箱里有哪些文件”，同时不会把原始文档全文塞入 prompt。
- **沙箱与工具能力**：`app/services/container.py` 管理 Docker 容器，`filesystem.py`/`capabilities.py` 负责文件读写与 `file_change` 推送，`agents/tools/file_write.py` 则把这些能力暴露给 Alex 等角色，实现“对话→代码文件”的闭环。
- **状态管理与持久化演进**：当前 SessionRepository 在内存基础上扩展了文件存储，接口已经抽象（`app/services/session_repository.py`），方便 Phase 2 接入 PostgreSQL/Redis 与向量存储，实现 docs 中规划的短期/长期记忆。

## Agent Runtime 亮点

- **配置化角色 + 动态决策**：`agents/config/registry.py` 定义 Mike/Emma/Bob/Alex/David/Iris 的职责与默认工具，`workflows/orchestrator.py` 让 Mike 按 JSON 决策下一位 Agent/是否结束，真实需求分析和编码链路都在此统一描述。
- **流式 + 回放双通道**：`LLMService` 默认 Deepseek（`DEEPSEEK_API_KEY` / `AGENT_LLM_DEEPSEEK_MODEL`），若未配置则返回占位响应；所有 token/status/error 事件通过 `/api/ws/sessions/{id}` 推送，最终消息还会写入 SessionStore，保证历史可追踪。
- **沙箱工具体系**：`agents/tools` 内只有“工具”概念，具体能力（文件写入、未来的终端/Git/Search 等）在 `app/services/capabilities.py` 实现并通过适配器注入，使得后端可以独立演进，而 Agent 代码只依赖稳定接口。
- **多层上下文注入**：Gateway 会为每个 WorkflowContext 自动附带 `history`（最近对话）+ `files_overview`（沙箱目录摘要）+ `artifacts`（最近写入文件列表）三类 metadata；BaseAgent 统一拼装 prompt，Bob/Emma 等 Agent 再结合 `{{read_file:path}}`、`file_read`/`file_write` 工具，既能引用历史文档，又避免复制 PRD 原文，真正实现“看过上下文再动手”。
- **Monorepo 与共享类型**：借助 pnpm workspace + Turborepo 管理 Next.js、FastAPI 与 `packages/shared` TypeScript 类型，配合统一 lint/test 脚本，降低多语言协作的维护成本。

## 下一步规划

1. **状态持久化与配额治理**：将 SessionRepository 落地 PostgreSQL/Redis，引入 Alembic 迁移与 Redis 缓存，实现 docs 中的短期/长期记忆，并结合 `users.subscription_tier` 建立 LLM/沙箱配额策略。
2. **工具矩阵扩展**：在 `agents/tools` 中新增终端、Git、搜索、预览等工具，并在 Alex/Bob/Iris 等角色的 `act` 生命周期中调用，使 Code Sandbox、Preview Server、GitHub 集成真正贯通。
3. **在线预览与可视化编辑**：实现 docs 规划的 Preview Server（nginx 反代 + session 隔离端口），在前端 PreviewPanel 内联展示实时页面，同时探索可圈选元素/可视化编辑能力，让用户在浏览器中直接调整 UI。
4. **前端可编辑体验**：除了预览，还需接入 Monaco + 文件树 + 工具链，实现多文件编辑、差异查看与保存；后续可结合 Alex 输出的 file block，联动“点选文件→查看→编辑→回写沙箱”。
5. **鉴权与多用户体验**：补齐刷新 Token、登出、WebSocket 鉴权续期；为前端增加登录态守卫、错误提示与权限文案，铺垫企业多租户/审计能力。
6. **Observability & Cost**：为 `LLMService`、ToolExecutor、sandbox 操作打通 metrics/logging/tracing，并基于 `docs/prd` 中的风险项，建立 LLM 成本与资源使用的监控告警。

## 项目约定

- **包管理**：采用 `pnpm`，所有 Node 包需声明在对应子包中。
- **任务调度**：`turbo.json` 维护 dev/build/lint/publish 流程，可在子项目内扩展。
- **Python 环境**：推荐 `uv` 或 `poetry` 管理虚拟环境，默认配置位于 `apps/backend/pyproject.toml`。
- **共享资源**：跨项目逻辑优先沉淀到 `packages/`，通过相对依赖引用，保持实现一致。
