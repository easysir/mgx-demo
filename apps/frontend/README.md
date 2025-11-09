# Frontend (Next.js)

MGX Web 客户端基于 Next.js 14 + React 18 + shadcn/Tailwind，负责 Chat Workspace、编辑器与预览体验。当前提供最小骨架，后续按系统设计文档逐步完善。

## 本地运行

```bash
cd apps/frontend
pnpm install        # 若尚未在仓库根目录执行
pnpm dev
```

## 目录规划

```
src/app/            # App Router 页面
src/components/     # UI 组件 + ChatUI
src/lib/            # API / WebSocket 封装
src/store/          # Zustand 状态
```

Tailwind、shadcn/ui、Monaco Editor 等依赖将在功能开发阶段加入。

