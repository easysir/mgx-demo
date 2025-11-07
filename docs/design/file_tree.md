# MGX MVP 项目文件结构

## 整体目录结构

```
mgx-mvp/
├── backend/                          # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI应用入口
│   │   ├── config.py                 # 配置管理
│   │   ├── dependencies.py           # 依赖注入
│   │   │
│   │   ├── api/                      # API路由
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py           # 认证相关API
│   │   │   │   ├── sessions.py       # 会话管理API
│   │   │   │   ├── chat.py           # 聊天交互API
│   │   │   │   ├── files.py          # 文件操作API
│   │   │   │   ├── deploy.py         # 部署相关API
│   │   │   │   ├── projects.py       # 项目管理API
│   │   │   │   └── websocket.py      # WebSocket连接
│   │   │
│   │   ├── agents/                   # Agent系统
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # BaseAgent抽象类
│   │   │   ├── mike.py               # Mike Agent (团队负责人)
│   │   │   ├── emma.py               # Emma Agent (产品经理)
│   │   │   ├── bob.py                # Bob Agent (架构师)
│   │   │   ├── alex.py               # Alex Agent (工程师)
│   │   │   ├── david.py              # David Agent (数据分析师)
│   │   │   ├── iris.py               # Iris Agent (研究员)
│   │   │   ├── manager.py            # Agent Manager
│   │   │   ├── memory.py             # Agent记忆系统
│   │   │   └── prompts/              # Agent提示词模板
│   │   │       ├── mike_prompts.py
│   │   │       ├── emma_prompts.py
│   │   │       ├── bob_prompts.py
│   │   │       ├── alex_prompts.py
│   │   │       ├── david_prompts.py
│   │   │       └── iris_prompts.py
│   │   │
│   │   ├── core/                     # 核心服务
│   │   │   ├── __init__.py
│   │   │   ├── llm/                  # LLM服务
│   │   │   │   ├── __init__.py
│   │   │   │   ├── service.py        # LLMService
│   │   │   │   ├── providers/        # LLM提供商
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── base.py       # LLMProvider接口
│   │   │   │   │   ├── openai.py     # OpenAI Provider
│   │   │   │   │   ├── anthropic.py  # Anthropic Provider
│   │   │   │   │   ├── gemini.py     # Gemini Provider
│   │   │   │   │   └── ollama.py     # Ollama Provider
│   │   │   │   └── config.py         # LLM配置
│   │   │   │
│   │   │   ├── tools/                # 工具系统
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py           # Tool接口
│   │   │   │   ├── executor.py       # ToolExecutor
│   │   │   │   ├── editor.py         # EditorTool
│   │   │   │   ├── terminal.py       # TerminalTool
│   │   │   │   ├── search.py         # SearchTool
│   │   │   │   ├── git.py            # GitTool
│   │   │   │   └── supabase.py       # SupabaseTool
│   │   │   │
│   │   │   ├── sandbox/              # 代码沙箱
│   │   │   │   ├── __init__.py
│   │   │   │   ├── docker.py         # Docker容器管理
│   │   │   │   ├── executor.py       # 代码执行器
│   │   │   │   └── limits.py         # 资源限制配置
│   │   │   │
│   │   │   ├── session/              # 会话管理
│   │   │   │   ├── __init__.py
│   │   │   │   ├── manager.py        # SessionManager
│   │   │   │   ├── context.py        # Context
│   │   │   │   └── store.py          # ContextStore
│   │   │   │
│   │   │   └── messaging/            # 消息系统
│   │   │       ├── __init__.py
│   │   │       ├── router.py         # MessageRouter
│   │   │       ├── queue.py          # 消息队列
│   │   │       └── models.py         # Message模型
│   │   │
│   │   ├── tasks/                    # 任务管理
│   │   │   ├── __init__.py
│   │   │   ├── scheduler.py          # TaskScheduler
│   │   │   ├── models.py             # Task模型
│   │   │   ├── executor.py           # 任务执行器
│   │   │   └── dependencies.py       # 依赖解析
│   │   │
│   │   ├── models/                   # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── user.py               # User模型
│   │   │   ├── session.py            # Session模型
│   │   │   ├── message.py            # Message模型
│   │   │   ├── task.py               # Task模型
│   │   │   ├── file.py               # File模型
│   │   │   ├── deployment.py         # Deployment模型
│   │   │   └── project.py            # Project模型
│   │   │
│   │   ├── schemas/                  # Pydantic模式
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # 认证相关schema
│   │   │   ├── session.py            # 会话相关schema
│   │   │   ├── chat.py               # 聊天相关schema
│   │   │   ├── file.py               # 文件相关schema
│   │   │   └── deploy.py             # 部署相关schema
│   │   │
│   │   ├── db/                       # 数据库
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # 数据库基类
│   │   │   ├── session.py            # 数据库会话
│   │   │   ├── migrations/           # Alembic迁移
│   │   │   │   ├── env.py
│   │   │   │   └── versions/
│   │   │   └── repositories/         # 数据仓库
│   │   │       ├── __init__.py
│   │   │       ├── user.py
│   │   │       ├── session.py
│   │   │       ├── message.py
│   │   │       ├── task.py
│   │   │       └── file.py
│   │   │
│   │   ├── services/                 # 业务服务
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # 认证服务
│   │   │   ├── session.py            # 会话服务
│   │   │   ├── chat.py               # 聊天服务
│   │   │   ├── file.py               # 文件服务
│   │   │   └── deploy.py             # 部署服务
│   │   │
│   │   ├── middleware/               # 中间件
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # 认证中间件
│   │   │   ├── cors.py               # CORS中间件
│   │   │   ├── logging.py            # 日志中间件
│   │   │   └── rate_limit.py         # 限流中间件
│   │   │
│   │   └── utils/                    # 工具函数
│   │       ├── __init__.py
│   │       ├── security.py           # 安全相关
│   │       ├── logger.py             # 日志配置
│   │       ├── cache.py              # 缓存工具
│   │       └── helpers.py            # 辅助函数
│   │
│   ├── tests/                        # 测试
│   │   ├── __init__.py
│   │   ├── conftest.py               # pytest配置
│   │   ├── test_agents/              # Agent测试
│   │   ├── test_api/                 # API测试
│   │   ├── test_core/                # 核心服务测试
│   │   └── test_integration/         # 集成测试
│   │
│   ├── scripts/                      # 脚本
│   │   ├── init_db.py                # 初始化数据库
│   │   ├── seed_data.py              # 填充测试数据
│   │   └── run_migrations.py         # 运行迁移
│   │
│   ├── requirements.txt              # Python依赖
│   ├── requirements-dev.txt          # 开发依赖
│   ├── Dockerfile                    # Docker镜像
│   ├── docker-compose.yml            # Docker Compose配置
│   ├── .env.example                  # 环境变量示例
│   └── README.md                     # 后端文档
│
├── frontend/                         # 前端应用
│   ├── public/                       # 静态资源
│   │   ├── favicon.ico
│   │   ├── logo.svg
│   │   └── images/
│   │
│   ├── src/
│   │   ├── app/                      # Next.js App Router
│   │   │   ├── layout.tsx            # 根布局
│   │   │   ├── page.tsx              # 首页
│   │   │   ├── (auth)/               # 认证路由组
│   │   │   │   ├── login/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── register/
│   │   │   │       └── page.tsx
│   │   │   ├── dashboard/            # Dashboard
│   │   │   │   └── page.tsx
│   │   │   ├── chat/                 # 聊天界面
│   │   │   │   └── [sessionId]/
│   │   │   │       └── page.tsx
│   │   │   ├── projects/             # 项目管理
│   │   │   │   ├── page.tsx
│   │   │   │   └── [projectId]/
│   │   │   │       └── page.tsx
│   │   │   └── settings/             # 设置
│   │   │       └── page.tsx
│   │   │
│   │   ├── components/               # React组件
│   │   │   ├── ui/                   # shadcn/ui组件
│   │   │   │   ├── button.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── dropdown.tsx
│   │   │   │   ├── tabs.tsx
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── layout/               # 布局组件
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── MainLayout.tsx
│   │   │   │
│   │   │   ├── chat/                 # 聊天相关组件
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── MessageItem.tsx
│   │   │   │   ├── InputBox.tsx
│   │   │   │   ├── AgentIndicator.tsx
│   │   │   │   └── FileAttachment.tsx
│   │   │   │
│   │   │   ├── editor/               # 编辑器组件
│   │   │   │   ├── CodeEditor.tsx
│   │   │   │   ├── FileTree.tsx
│   │   │   │   ├── Terminal.tsx
│   │   │   │   └── EditorTabs.tsx
│   │   │   │
│   │   │   ├── preview/              # 预览组件
│   │   │   │   ├── PreviewPanel.tsx
│   │   │   │   ├── DeviceSelector.tsx
│   │   │   │   ├── Console.tsx
│   │   │   │   └── NetworkPanel.tsx
│   │   │   │
│   │   │   ├── task/                 # 任务组件
│   │   │   │   ├── TaskDashboard.tsx
│   │   │   │   ├── TaskList.tsx
│   │   │   │   ├── TaskItem.tsx
│   │   │   │   └── DependencyGraph.tsx
│   │   │   │
│   │   │   └── common/               # 通用组件
│   │   │       ├── Loading.tsx
│   │   │       ├── ErrorBoundary.tsx
│   │   │       ├── Toast.tsx
│   │   │       └── Modal.tsx
│   │   │
│   │   ├── lib/                      # 工具库
│   │   │   ├── api/                  # API客户端
│   │   │   │   ├── client.ts         # Axios配置
│   │   │   │   ├── auth.ts           # 认证API
│   │   │   │   ├── session.ts        # 会话API
│   │   │   │   ├── chat.ts           # 聊天API
│   │   │   │   ├── file.ts           # 文件API
│   │   │   │   └── deploy.ts         # 部署API
│   │   │   │
│   │   │   ├── websocket/            # WebSocket客户端
│   │   │   │   ├── client.ts
│   │   │   │   └── handlers.ts
│   │   │   │
│   │   │   ├── utils/                # 工具函数
│   │   │   │   ├── format.ts
│   │   │   │   ├── validation.ts
│   │   │   │   └── storage.ts
│   │   │   │
│   │   │   └── constants.ts          # 常量定义
│   │   │
│   │   ├── hooks/                    # 自定义Hooks
│   │   │   ├── useAuth.ts            # 认证Hook
│   │   │   ├── useSession.ts         # 会话Hook
│   │   │   ├── useWebSocket.ts       # WebSocket Hook
│   │   │   ├── useChat.ts            # 聊天Hook
│   │   │   ├── useEditor.ts          # 编辑器Hook
│   │   │   └── useTask.ts            # 任务Hook
│   │   │
│   │   ├── store/                    # 状态管理 (Zustand)
│   │   │   ├── authStore.ts          # 认证状态
│   │   │   ├── sessionStore.ts       # 会话状态
│   │   │   ├── chatStore.ts          # 聊天状态
│   │   │   ├── editorStore.ts        # 编辑器状态
│   │   │   └── taskStore.ts          # 任务状态
│   │   │
│   │   ├── types/                    # TypeScript类型定义
│   │   │   ├── api.ts                # API类型
│   │   │   ├── agent.ts              # Agent类型
│   │   │   ├── message.ts            # 消息类型
│   │   │   ├── task.ts               # 任务类型
│   │   │   └── file.ts               # 文件类型
│   │   │
│   │   └── styles/                   # 样式文件
│   │       ├── globals.css           # 全局样式
│   │       └── themes/               # 主题配置
│   │           ├── light.css
│   │           └── dark.css
│   │
│   ├── tests/                        # 前端测试
│   │   ├── unit/                     # 单元测试
│   │   ├── integration/              # 集成测试
│   │   └── e2e/                      # E2E测试 (Playwright)
│   │
│   ├── package.json                  # npm依赖
│   ├── tsconfig.json                 # TypeScript配置
│   ├── next.config.js                # Next.js配置
│   ├── tailwind.config.js            # Tailwind配置
│   ├── .eslintrc.json                # ESLint配置
│   ├── .prettierrc                   # Prettier配置
│   ├── Dockerfile                    # Docker镜像
│   └── README.md                     # 前端文档
│
├── docs/                             # 文档
│   ├── prd/                          # 产品需求文档
│   │   └── mgx_mvp_prd.md
│   ├── design/                       # 设计文档
│   │   ├── system_design.md
│   │   ├── architect.plantuml
│   │   ├── class_diagram.plantuml
│   │   ├── sequence_diagram.plantuml
│   │   ├── er_diagram.plantuml
│   │   ├── ui_navigation.plantuml
│   │   └── file_tree.md
│   ├── api/                          # API文档
│   │   └── openapi.yaml
│   └── deployment/                   # 部署文档
│       ├── docker.md
│       ├── kubernetes.md
│       └── production.md
│
├── infrastructure/                   # 基础设施配置
│   ├── docker/                       # Docker配置
│   │   ├── backend.Dockerfile
│   │   ├── frontend.Dockerfile
│   │   └── sandbox.Dockerfile
│   ├── k8s/                          # Kubernetes配置
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   └── terraform/                    # Terraform配置
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
│
├── scripts/                          # 项目脚本
│   ├── setup.sh                      # 环境设置
│   ├── dev.sh                        # 启动开发环境
│   ├── build.sh                      # 构建项目
│   ├── deploy.sh                     # 部署脚本
│   └── test.sh                       # 运行测试
│
├── .github/                          # GitHub配置
│   ├── workflows/                    # GitHub Actions
│   │   ├── ci.yml                    # 持续集成
│   │   ├── cd.yml                    # 持续部署
│   │   └── test.yml                  # 测试工作流
│   └── ISSUE_TEMPLATE/               # Issue模板
│
├── .gitignore                        # Git忽略文件
├── .env.example                      # 环境变量示例
├── docker-compose.yml                # Docker Compose配置
├── Makefile                          # Make命令
├── LICENSE                           # 开源协议
└── README.md                         # 项目说明
```

## 关键文件说明

### 后端核心文件

#### `backend/app/main.py`
- FastAPI应用入口
- 注册路由和中间件
- 配置CORS和WebSocket
- 启动事件处理

#### `backend/app/agents/base.py`
- BaseAgent抽象类
- 定义Agent通用接口
- 实现基础思考和执行逻辑

#### `backend/app/core/llm/service.py`
- LLMService统一接口
- 管理多个LLM提供商
- 实现fallback和负载均衡

#### `backend/app/core/tools/executor.py`
- ToolExecutor工具执行引擎
- 注册和管理所有工具
- 执行工具并返回结果

#### `backend/app/core/sandbox/docker.py`
- Docker容器管理
- 创建和销毁沙箱环境
- 资源限制和安全隔离

#### `backend/app/tasks/scheduler.py`
- TaskScheduler任务调度器
- 解析任务依赖关系
- 优先级队列管理

### 前端核心文件

#### `frontend/src/app/layout.tsx`
- Next.js根布局
- 全局样式和Provider
- 主题配置

#### `frontend/src/components/chat/ChatInterface.tsx`
- 主聊天界面组件
- 集成消息列表和输入框
- WebSocket连接管理

#### `frontend/src/components/editor/CodeEditor.tsx`
- Monaco编辑器集成
- 语法高亮和自动补全
- 文件保存和同步

#### `frontend/src/lib/api/client.ts`
- Axios HTTP客户端配置
- 请求拦截器(添加token)
- 响应拦截器(错误处理)

#### `frontend/src/lib/websocket/client.ts`
- WebSocket客户端封装
- 自动重连机制
- 消息队列和事件处理

#### `frontend/src/store/chatStore.ts`
- Zustand聊天状态管理
- 消息历史
- 流式输出状态

### 配置文件

#### `docker-compose.yml`
- 本地开发环境编排
- 服务: backend, frontend, postgres, redis, qdrant
- 网络和卷配置

#### `.env.example`
- 环境变量模板
- 数据库连接
- API密钥
- 服务配置

## 文件命名规范

### Python文件
- 模块: 小写+下划线 (snake_case)
- 类: 大驼峰 (PascalCase)
- 函数/变量: 小写+下划线 (snake_case)

### TypeScript/React文件
- 组件: 大驼峰 (PascalCase.tsx)
- 工具函数: 小驼峰 (camelCase.ts)
- 类型定义: 大驼峰 (PascalCase.ts)
- Hooks: use前缀 (useXxx.ts)

### 目录
- 小写+连字符 (kebab-case)
- 特殊目录: 下划线前缀 (如 `_components`)

## 模块依赖关系

### 后端依赖层次
```
API Layer (api/)
    ↓
Service Layer (services/)
    ↓
Agent Layer (agents/)
    ↓
Core Layer (core/)
    ↓
Data Layer (models/, db/)
```

### 前端依赖层次
```
Pages (app/)
    ↓
Components (components/)
    ↓
Hooks (hooks/)
    ↓
Store (store/)
    ↓
API/Utils (lib/)
```

## 开发工作流

### 本地开发
1. 克隆仓库
2. 复制 `.env.example` 到 `.env`
3. 运行 `docker-compose up -d` 启动服务
4. 后端: `cd backend && pip install -r requirements-dev.txt && uvicorn app.main:app --reload`
5. 前端: `cd frontend && npm install && npm run dev`

### 测试
- 后端: `pytest tests/`
- 前端: `npm run test`
- E2E: `npm run test:e2e`

### 部署
- 开发环境: Docker Compose
- 生产环境: Kubernetes + Helm
- CI/CD: GitHub Actions

---

该文件结构遵循以下原则:
1. **关注点分离**: 前后端独立，模块职责清晰
2. **可扩展性**: 易于添加新Agent、工具、组件
3. **可测试性**: 测试文件与源码对应
4. **可维护性**: 统一的命名规范和目录结构
5. **生产就绪**: 包含完整的配置、文档、部署脚本