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

### 启动
- 前端：`pnpm run dev:frontend`（Next.js dev server，默认 http://localhost:3000）
- 后端：`pnpm run dev:backend`（uvicorn + FastAPI，健康检查 http://127.0.0.1:8000/healthz）
- 前后端并行：`pnpm dev`（Turbo 并行拉起各 dev 命令）

## 项目约定

- **包管理**：采用 `pnpm`，所有 Node 包需声明在对应子包中。
- **任务调度**：`turbo.json` 维护 dev/build/lint/publish 流程，可在子项目内扩展。
- **Python 环境**：推荐 `uv` 或 `poetry` 管理虚拟环境，默认配置位于 `apps/backend/pyproject.toml`。
- **共享资源**：跨项目逻辑优先沉淀到 `packages/`，通过相对依赖引用，保持实现一致。

更多细节请参考 `docs/design` 与 `docs/codex`。
