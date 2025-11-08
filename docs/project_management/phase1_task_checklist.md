# Phase 1 任务清单

## 概览
- **Phase**: Phase 1 - MVP 核心功能
- **时间**: Week 1-10 (8-10周)
- **目标**: 实现完整的 6 人 Agent 团队、基础聊天界面、代码编辑器、预览功能和部署能力

---

## Sprint 1: 基础设施搭建 (Week 1-2)

### 任务 1.1: 项目初始化
- **任务ID**: TASK-1.1
- **负责人**: Alex
- **预计工时**: 3天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: 无
- **交付物**:
  - [ ] 项目目录结构（参考 file_tree.md）
  - [ ] docker-compose.yml（PostgreSQL 15, Redis 7, Qdrant, Backend, Frontend）
  - [ ] .env.example 环境变量模板
  - [ ] Makefile 和启动脚本（setup.sh, dev.sh, build.sh, test.sh）
  - [ ] GitHub Actions CI/CD 基础配置（.github/workflows/ci.yml）
- **验收标准**:
  - [ ] `docker-compose up` 成功启动所有服务
  - [ ] 数据库连接正常
  - [ ] 前后端可以互相访问

### 任务 1.2: 数据库模型和迁移
- **任务ID**: TASK-1.2
- **负责人**: David
- **预计工时**: 4天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-1.1
- **交付物**:
  - [ ] backend/app/models/user.py（用户模型）
  - [ ] backend/app/models/session.py（会话模型）
  - [ ] backend/app/models/message.py（消息模型）
  - [ ] backend/app/models/task.py（任务模型）
  - [ ] backend/app/models/file.py（文件模型）
  - [ ] backend/app/models/deployment.py（部署模型）
  - [ ] backend/app/models/project.py（项目模型）
  - [ ] Alembic 迁移脚本
  - [ ] 数据库初始化脚本（backend/scripts/init_db.py）
- **验收标准**:
  - [ ] `alembic upgrade head` 成功创建所有表
  - [ ] 所有外键约束正确
  - [ ] 可以插入测试数据

### 任务 1.3: 认证系统和中间件
- **任务ID**: TASK-1.3
- **负责人**: Alex
- **预计工时**: 5天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-1.1, TASK-1.2
- **交付物**:
  - [ ] backend/app/utils/security/jwt_handler.py（JWT生成和验证）
  - [ ] backend/app/utils/security/password.py（密码加密）
  - [ ] backend/app/middleware/auth.py（认证中间件）
  - [ ] backend/app/middleware/websocket_auth.py（WebSocket鉴权）
  - [ ] backend/app/middleware/token_refresh.py（Token刷新）
  - [ ] backend/app/api/v1/auth.py（认证API）
- **验收标准**:
  - [ ] 用户可以注册和登录
  - [ ] JWT Token 正确生成和验证
  - [ ] WebSocket 连接需要有效 Token
  - [ ] Token 过期自动刷新

### 任务 1.4: Session Manager 和 Context Store
- **任务ID**: TASK-1.4
- **负责人**: Bob
- **预计工时**: 5天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-1.1, TASK-1.2
- **交付物**:
  - [ ] backend/app/core/session/manager.py（SessionManager）
  - [ ] backend/app/core/session/context.py（Context类）
  - [ ] backend/app/core/session/store.py（ContextStore）
  - [ ] backend/app/core/session/validator.py（会话验证）
  - [ ] backend/app/core/session/lifecycle.py（会话生命周期管理）
- **验收标准**:
  - [ ] 可以创建和获取会话
  - [ ] 上下文正确保存和加载
  - [ ] 会话超时自动清理
  - [ ] 向量检索返回相关历史

---

## Sprint 2: LLM 服务和工具系统 (Week 3-4)

### 任务 2.1: LLM Service 统一接口
- **任务ID**: TASK-2.1
- **负责人**: Bob
- **预计工时**: 6天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-1.4
- **交付物**:
  - [ ] backend/app/core/llm/service.py（LLMService）
  - [ ] backend/app/core/llm/providers/base.py（LLMProvider接口）
  - [ ] backend/app/core/llm/providers/openai.py（OpenAI Provider）
  - [ ] backend/app/core/llm/providers/anthropic.py（Anthropic Provider）
  - [ ] backend/app/core/llm/providers/gemini.py（Gemini Provider）
  - [ ] backend/app/core/llm/config.py（LLM配置）
- **验收标准**:
  - [ ] 可以调用 OpenAI GPT-4
  - [ ] 可以调用 Anthropic Claude
  - [ ] 流式输出正常工作
  - [ ] Fallback 机制正确触发

### 任务 2.2: Tool Executor 和基础工具
- **任务ID**: TASK-2.2
- **负责人**: Alex
- **预计工时**: 7天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-1.4
- **交付物**:
  - [ ] backend/app/core/tools/base.py（Tool接口）
  - [ ] backend/app/core/tools/executor.py（ToolExecutor）
  - [ ] backend/app/core/tools/editor.py（EditorTool）
  - [ ] backend/app/core/tools/terminal.py（TerminalTool）
  - [ ] backend/app/core/tools/search.py（SearchTool）
  - [ ] backend/app/core/tools/git.py（GitTool）
- **验收标准**:
  - [ ] 可以读写文件
  - [ ] 可以执行终端命令
  - [ ] 可以搜索网络
  - [ ] 可以提交代码到 GitHub

### 任务 2.3: Code Sandbox (Docker 容器沙箱)
- **任务ID**: TASK-2.3
- **负责人**: Alex
- **预计工时**: 6天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-1.1
- **交付物**:
  - [ ] backend/app/core/sandbox/docker.py（Docker容器管理）
  - [ ] backend/app/core/sandbox/executor.py（代码执行器）
  - [ ] backend/app/core/sandbox/limits.py（资源限制配置）
  - [ ] infrastructure/docker/sandbox.Dockerfile（沙箱镜像）
- **验收标准**:
  - [ ] 可以创建和销毁容器
  - [ ] 可以执行 Node.js 代码
  - [ ] 资源限制生效
  - [ ] 超时自动清理

---

## Sprint 3: Agent 系统核心 (Week 5-6)

### 任务 3.1: BaseAgent 和 Mike Agent
- **任务ID**: TASK-3.1
- **负责人**: Bob
- **预计工时**: 8天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-2.1, TASK-2.2
- **交付物**:
  - [ ] backend/app/agents/base.py（BaseAgent抽象类）
  - [ ] backend/app/agents/mike.py（MikeAgent）
  - [ ] backend/app/agents/memory.py（Agent记忆系统）
  - [ ] backend/app/agents/prompts/mike_prompts.py（Mike提示词）
- **验收标准**:
  - [ ] Mike 可以分析用户需求
  - [ ] Mike 可以创建任务计划
  - [ ] Mike 可以分配任务
  - [ ] Mike 可以审查交付物

### 任务 3.2: Execution Team (Emma, Bob, Alex, David, Iris)
- **任务ID**: TASK-3.2
- **负责人**: Alex + Bob
- **预计工时**: 10天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-3.1
- **交付物**:
  - [ ] backend/app/agents/emma.py（EmmaAgent）
  - [ ] backend/app/agents/bob.py（BobAgent）
  - [ ] backend/app/agents/alex.py（AlexAgent）
  - [ ] backend/app/agents/david.py（DavidAgent）
  - [ ] backend/app/agents/iris.py（IrisAgent）
  - [ ] 所有 Agent 的提示词文件
- **验收标准**:
  - [ ] 每个 Agent 可以独立执行任务
  - [ ] 每个 Agent 可以向 Mike 汇报
  - [ ] 所有 Agent 的提示词清晰有效

### 任务 3.3: Task Scheduler 和 Message Router
- **任务ID**: TASK-3.3
- **负责人**: Bob
- **预计工时**: 6天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-3.1
- **交付物**:
  - [ ] backend/app/tasks/scheduler.py（TaskScheduler）
  - [ ] backend/app/tasks/models.py（Task模型）
  - [ ] backend/app/tasks/dependencies.py（依赖解析）
  - [ ] backend/app/core/messaging/router.py（MessageRouter）
  - [ ] backend/app/core/messaging/models.py（Message模型）
- **验收标准**:
  - [ ] 可以调度任务到 Agent
  - [ ] Agent 完成后通知 Mike
  - [ ] 消息正确路由
  - [ ] 任务依赖正确解析

### 任务 3.4: Agent Manager (技术支撑层)
- **任务ID**: TASK-3.4
- **负责人**: Bob
- **预计工时**: 3天
- **优先级**: P1
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-3.2, TASK-3.3
- **交付物**:
  - [ ] backend/app/agents/manager.py（AgentManager）
- **验收标准**:
  - [ ] 可以创建和销毁 Agent 实例
  - [ ] 可以执行 Mike 的指令
  - [ ] 可以通知 Mike 完成情况

---

## Sprint 4: API 和 WebSocket (Week 7)

### 任务 4.1: RESTful API 实现
- **任务ID**: TASK-4.1
- **负责人**: Alex
- **预计工时**: 5天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-3.1, TASK-3.2
- **交付物**:
  - [ ] backend/app/api/v1/auth.py（认证API）
  - [ ] backend/app/api/v1/sessions.py（会话管理API）
  - [ ] backend/app/api/v1/chat.py（聊天交互API）
  - [ ] backend/app/api/v1/files.py（文件操作API）
  - [ ] backend/app/api/v1/deploy.py（部署相关API）
  - [ ] backend/app/api/v1/projects.py（项目管理API）
- **验收标准**:
  - [ ] 所有 API 端点正常工作
  - [ ] OpenAPI 文档完整
  - [ ] 错误处理正确
  - [ ] 限流机制生效

### 任务 4.2: WebSocket 服务器
- **任务ID**: TASK-4.2
- **负责人**: Alex
- **预计工时**: 5天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-1.3, TASK-3.3
- **交付物**:
  - [ ] backend/app/api/v1/websocket.py（WebSocket连接）
  - [ ] backend/app/services/websocket.py（WebSocket服务）
- **验收标准**:
  - [ ] WebSocket 连接稳定
  - [ ] 流式输出正常
  - [ ] 状态广播及时
  - [ ] 断线自动重连

---

## Sprint 5: 预览服务器 (Week 8)

### 任务 5.1: Preview Server 实现
- **任务ID**: TASK-5.1
- **负责人**: Alex
- **预计工时**: 7天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-2.3
- **交付物**:
  - [ ] backend/app/core/preview/server.py（PreviewServer主类）
  - [ ] backend/app/core/preview/proxy.py（nginx反向代理配置）
  - [ ] backend/app/core/preview/port_manager.py（端口管理）
  - [ ] backend/app/core/preview/url_generator.py（预览URL生成）
  - [ ] infrastructure/nginx/preview.conf.template（nginx配置模板）
- **验收标准**:
  - [ ] 可以启动预览服务
  - [ ] nginx 反向代理正确配置
  - [ ] 预览 URL 可以访问
  - [ ] 多个会话互不干扰

---

## Sprint 6: 前端核心功能 (Week 9-10)

### 任务 6.1: Next.js 项目初始化和布局
- **任务ID**: TASK-6.1
- **负责人**: Alex
- **预计工时**: 4天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-1.1
- **交付物**:
  - [ ] Next.js 14 项目初始化
  - [ ] shadcn/ui 组件库集成
  - [ ] Tailwind CSS 配置
  - [ ] 主布局组件（frontend/src/components/layout/）
  - [ ] 路由配置（frontend/src/app/）
- **验收标准**:
  - [ ] 项目可以启动
  - [ ] 布局正常显示
  - [ ] 路由跳转正常
  - [ ] 深色模式切换正常

### 任务 6.2: ChatUI (整合版)
- **任务ID**: TASK-6.2
- **负责人**: Alex
- **预计工时**: 6天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-6.1
- **交付物**:
  - [ ] frontend/src/components/chat/ChatInterface.tsx
  - [ ] frontend/src/components/chat/MessageList.tsx
  - [ ] frontend/src/components/chat/MessageItem.tsx
  - [ ] frontend/src/components/chat/InputBox.tsx
  - [ ] frontend/src/components/chat/AgentIndicator.tsx
- **验收标准**:
  - [ ] ChatUI 正常显示
  - [ ] 消息流式输出正常
  - [ ] Agent 状态实时更新
  - [ ] 任务进度正确显示

### 任务 6.3: 代码编辑器和文件管理
- **任务ID**: TASK-6.3
- **负责人**: Alex
- **预计工时**: 6天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-6.1
- **交付物**:
  - [ ] frontend/src/components/editor/CodeEditor.tsx
  - [ ] frontend/src/components/editor/FileTree.tsx
  - [ ] frontend/src/components/editor/Terminal.tsx
  - [ ] frontend/src/components/editor/EditorTabs.tsx
- **验收标准**:
  - [ ] 编辑器正常工作
  - [ ] 文件树可以展开折叠
  - [ ] 终端可以执行命令
  - [ ] 多标签页切换正常

### 任务 6.4: 预览面板
- **任务ID**: TASK-6.4
- **负责人**: Alex
- **预计工时**: 4天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-6.1, TASK-5.1
- **交付物**:
  - [ ] frontend/src/components/preview/PreviewPanel.tsx
  - [ ] frontend/src/components/preview/DeviceSelector.tsx
  - [ ] frontend/src/components/preview/Console.tsx
  - [ ] frontend/src/components/preview/NetworkPanel.tsx
- **验收标准**:
  - [ ] 预览正常显示
  - [ ] 设备视图切换正常
  - [ ] 控制台显示日志
  - [ ] 实时刷新正常

### 任务 6.5: WebSocket 客户端和状态管理
- **任务ID**: TASK-6.5
- **负责人**: Alex
- **预计工时**: 4天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: TASK-4.2, TASK-6.1
- **交付物**:
  - [ ] frontend/src/lib/websocket/client.ts
  - [ ] frontend/src/lib/websocket/handlers.ts
  - [ ] frontend/src/lib/websocket/auth.ts
  - [ ] frontend/src/store/chatStore.ts
  - [ ] frontend/src/store/taskStore.ts
- **验收标准**:
  - [ ] WebSocket 连接稳定
  - [ ] 消息正确接收和处理
  - [ ] 断线自动重连
  - [ ] 状态正确更新

---

## Sprint 7: 集成测试和优化 (Week 10)

### 任务 7.1: 端到端测试
- **任务ID**: TASK-7.1
- **负责人**: Alex + Emma
- **预计工时**: 5天
- **优先级**: P0
- **状态**: ⬜ TODO
- **开始日期**: -
- **完成日期**: -
- **依赖**: 所有前面的任务
- **交付物**:
  - [ ] E2E 测试用例
  - [ ] 测试报告
  - [ ] Bug 修复
- **验收标准**:
  - [ ] 所有测试用例通过
  - [ ] 无严重 Bug
  - [ ] 性能符合预期

---

## 总体进度统计

### 按 Sprint 统计
| Sprint | 任务数 | 已完成 | 进行中 | 待开始 | 完成率 |
|--------|--------|--------|--------|--------|--------|
| Sprint 1 | 4 | 0 | 0 | 4 | 0% |
| Sprint 2 | 3 | 0 | 0 | 3 | 0% |
| Sprint 3 | 4 | 0 | 0 | 4 | 0% |
| Sprint 4 | 2 | 0 | 0 | 2 | 0% |
| Sprint 5 | 1 | 0 | 0 | 1 | 0% |
| Sprint 6 | 5 | 0 | 0 | 5 | 0% |
| Sprint 7 | 1 | 0 | 0 | 1 | 0% |
| **总计** | **20** | **0** | **0** | **20** | **0%** |

### 按负责人统计
| 负责人 | 任务数 | 已完成 | 进行中 | 待开始 | 完成率 |
|--------|--------|--------|--------|--------|--------|
| Alex | 11 | 0 | 0 | 11 | 0% |
| Bob | 5 | 0 | 0 | 5 | 0% |
| David | 1 | 0 | 0 | 1 | 0% |
| Alex + Bob | 1 | 0 | 0 | 1 | 0% |
| Alex + Emma | 1 | 0 | 0 | 1 | 0% |
| **总计** | **20** | **0** | **0** | **20** | **0%** |

### 按优先级统计
| 优先级 | 任务数 | 已完成 | 进行中 | 待开始 | 完成率 |
|--------|--------|--------|--------|--------|--------|
| P0 | 19 | 0 | 0 | 19 | 0% |
| P1 | 1 | 0 | 0 | 1 | 0% |
| **总计** | **20** | **0** | **0** | **20** | **0%** |

---

## 状态图例
- ⬜ TODO: 待开始
- 🟦 IN_PROGRESS: 进行中
- 🟨 REVIEW: 代码审查中
- 🟥 BLOCKED: 被阻塞
- ✅ DONE: 已完成

---

## 更新日志
| 日期 | 更新内容 | 更新人 |
|------|---------|--------|
| 2024-11-08 | 创建 Phase 1 任务清单 | Emma |