# MGX MVP Summary

## Product Definition
- **Positioning**: Conversational研发工作台，用户以自然语言描述目标，由 Mike 领衔的六人 AI 团队接力完成需求分析、设计、开发、数据处理与研究，直到产出可预览、可部署的项目。
- **Core UX**: 整合式 ChatUI（30% 宽度）同步展示对话、Agent 状态与任务进度，Editor+Preview 区域（70%）承载 Monaco 编辑器、文件树、终端和实时预览；导航深度 <=2 层，Dashboard→Workspace→Preview/Deploy 不超两次点击。
- **Tech Stack**: FastAPI + 自研多-Agent 框架 + Redis/Celery + Docker 沙箱构建后端执行环境；Next.js 14、shadcn/Tailwind、Zustand、Monaco 和 Socket.IO 构建前端；统一 LLMService 抽象支持 GPT-4、Claude、Gemini 及 Ollama，自带模型切换与 fallback 机制。
- **MVP Scope (Phase 1)**: 完整 6 Agent 团队（Mike/Emma/Bob/Alex/David/Iris）、认证和会话、流式聊天、文件/代码操作、Docker 预览（nginx 反代）、GitHub 集成、JWT+刷新 Token 的 WebSocket 鉴权；Phase 2/3 规划 Supabase、多模型切换、模板库、企业特性等扩展。

## Architectural Overview
- **Frontend Layer**: Web UI、整合 Chat Interface、Monaco Code Editor、文件管理与预览面板；通过 REST/WebSocket 与后端交互，保持聊天/开发/预览三模块在同一工作区。
- **API Gateway Layer**: FastAPI Gateway 统一入口，Auth Middleware 负责 HTTP+WebSocket JWT 校验与刷新，WebSocket Server 推送 Agent 状态和流式输出。
- **Agent Orchestration Layer**: Mike 作为唯一入口与决策者，通过 Task Scheduler（DAG 依赖管理）和 Message Router（Agent 间通信 + 状态广播）协调 Emma/Bob/Alex/David/Iris，遵循消息流“用户→Mike→团队→Mike→用户”。
- **Core Services & Tooling**: LLMService、ToolExecutor、Session Manager、Context Store、Code Sandbox、Preview Server 构成共享基座；工具层封装 Editor/Terminal/Search/Git/Supabase 等能力，全部 Agent 通过 ToolExecutor 访问，Session Manager/Context Store 统一维护上下文。
- **Data & Infrastructure Layer**: PostgreSQL（主数据）、Redis（缓存/队列/短期记忆）、向量库（长期记忆）、文件存储（S3/本地）及外部服务（OpenAI/Anthropic/Gemini/GitHub/Supabase）；Docker 沙箱通过资源配额、命令白名单和超时机制保证代码执行安全。

## Data Model & Workflow
- **ER 模型**: users-sessions-messages/tasks/files/deployments/agent_executions/tool_executions/llm_requests/context_embeddings/projects，支持从用户行为到 Agent/工具执行的全链路追踪。
- **上下文策略**: 滑动窗口保存最近对话，关键信息写入向量库，Redis 承担短期记忆，Session Manager + Context Store 保证 Agent 与工具取用一致。
- **端到端流程**: 用户登录→创建会话→Mike 分析需求并广播任务总览→Task Scheduler 指派 Bob/Alex 等→Agent 通过 ToolExecutor 操作文件/终端/沙箱→Message Router+WebSocket 实时回传→Preview Server 启动沙箱 + nginx 映射→用户预览/部署→Session/上下文持久化。

## Delivery Plan & Risks
- **实施节奏**: Phase 1（8-10 周）完成基础设施、数据库、认证、Agent 基座、前端工作区与预览部署；Phase 2（4-6 周）扩展 Supabase、多模型、Vercel/Netlify、数据科学与高级搜索；Phase 3（6-8 周）上线协作、模板库、企业功能和性能优化，配套 CI/CD、Docker Compose、K8s 和监控。
- **开放问题**: LLM 成本控制策略、沙箱资源配额及分级、协同编辑与权限模型、数据隐私/私有部署、各 Agent 能力边界、ChatUI 折叠与响应式规范、Mike 决策透明度。需在后续产品/工程迭代中逐项落地。

## Suggested Next Steps
1. 明确 LLM 计费与沙箱资源策略，结合 `users.subscription_tier` 与配额字段落实到产品方案。
2. 将实施规划拆解为里程碑与负责人，确保 Phase 1 关键组件（Session Manager、Task Scheduler、Preview Server、整合 ChatUI）按周交付。
3. 基于 UI/架构文档输出中高保真原型，验证 30/70 布局与整合式 ChatUI 的交互细节，为前端开发定稿。

