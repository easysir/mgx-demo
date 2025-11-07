# MGX MVP 系统设计文档

## 1. 实现方案

### 1.1 核心技术选型

#### 后端技术栈
- **框架**: FastAPI (Python 3.11+)
  - 理由: 高性能异步框架，原生支持WebSocket，类型提示完善，文档自动生成
- **Agent框架**: 自研基于LangChain的多Agent系统
  - 理由: 灵活可控，支持自定义Agent行为和工具集成
- **数据库**: 
  - PostgreSQL 15+ (主数据库，存储用户、会话、任务等结构化数据)
  - Redis 7+ (缓存、消息队列、会话状态)
  - Qdrant/Weaviate (向量数据库，用于上下文检索和语义搜索)
- **消息队列**: Redis Streams + Celery
  - 理由: 轻量级，适合MVP阶段，后期可迁移到RabbitMQ/Kafka
- **代码执行**: Docker容器沙箱
  - 理由: 安全隔离，资源可控，支持多语言环境

#### 前端技术栈
- **框架**: Next.js 14 (React 18)
  - 理由: SSR/SSG支持，优秀的开发体验，丰富的生态
- **UI组件库**: shadcn/ui + Tailwind CSS
  - 理由: 现代化设计，高度可定制，与Next.js完美集成
- **状态管理**: Zustand
  - 理由: 轻量级，API简洁，适合中小型应用
- **代码编辑器**: Monaco Editor
  - 理由: VS Code同款编辑器，功能强大，语法高亮完善
- **实时通信**: Socket.IO Client
  - 理由: 与FastAPI-SocketIO配合，支持自动重连和房间管理

#### LLM集成
- **支持模型**:
  - OpenAI (GPT-4, GPT-3.5-turbo)
  - Anthropic (Claude 3 Sonnet/Opus)
  - Google (Gemini Pro)
  - 开源模型 (通过Ollama本地部署)
- **集成方式**: 统一的LLMService抽象层，支持模型切换和fallback机制

### 1.2 关键技术挑战及解决方案

#### 挑战1: 多Agent协作和任务调度
**解决方案**:
- 实现基于有向无环图(DAG)的任务依赖管理
- 使用优先级队列确保关键任务优先执行
- Agent间通过消息总线(Message Router)异步通信
- 实现任务超时和失败重试机制

#### 挑战2: 上下文管理和长对话记忆
**解决方案**:
- 使用滑动窗口保留最近N轮对话
- 关键信息提取并存入向量数据库
- 基于相似度检索历史上下文
- 实现分层记忆: 短期(Redis) + 长期(向量DB)

#### 挑战3: 代码执行安全性
**解决方案**:
- 每个会话独立Docker容器
- 资源限制: CPU、内存、磁盘、网络
- 白名单机制: 限制可执行命令和可访问文件
- 超时自动清理机制

#### 挑战4: 实时流式输出
**解决方案**:
- WebSocket双向通信
- LLM流式API + Server-Sent Events (SSE)
- 前端增量渲染，避免重绘整个界面
- 消息队列缓冲，防止消息丢失

### 1.3 MVP阶段功能范围

**Phase 1 (MVP核心)**:
- ✅ 用户认证和会话管理
- ✅ 基础聊天界面和流式输出
- ✅ Mike(协调者) + Alex(工程师)两个核心Agent
- ✅ 前端网页开发能力(React/Next.js)
- ✅ 代码编辑器和文件管理
- ✅ 基础预览功能
- ✅ GitHub集成(代码提交)

**Phase 2 (功能扩展)**:
- Emma(产品经理) + Bob(架构师)
- Supabase后端集成
- 多模型切换
- 部署到Vercel/Netlify

**Phase 3 (高级功能)**:
- David(数据分析) + Iris(研究员)
- Python/数据科学支持
- 协作功能(多用户)
- 项目模板库

---

## 2. 主要用户交互模式

### 2.1 核心用户流程

#### 流程1: 新用户首次使用
1. 用户访问平台首页
2. 点击"开始使用"按钮
3. 注册/登录(支持邮箱或OAuth)
4. 进入Dashboard，看到欢迎引导
5. 点击"新建会话"进入聊天界面
6. 输入需求: "创建一个个人作品集网站"
7. Mike Agent分析需求并制定任务计划
8. Alex Agent开始生成代码
9. 用户在代码编辑器中查看生成的文件
10. 点击"预览"查看实时效果
11. 满意后点击"部署"发布到线上

#### 流程2: 迭代修改现有项目
1. 用户从Dashboard选择已有项目
2. 进入会话，查看历史对话和文件
3. 输入修改需求: "把导航栏改成深色主题"
4. Alex Agent理解上下文并修改相关文件
5. 用户在预览中实时看到变化
6. 确认后提交到GitHub

#### 流程3: 复杂需求多Agent协作
1. 用户输入: "开发一个带后端的博客系统"
2. Mike Agent识别为复杂任务，分配给多个Agent:
   - Emma: 分析需求，创建功能清单
   - Bob: 设计系统架构和数据库模型
   - Alex: 实现前后端代码
3. 用户在任务面板中查看各Agent的进度
4. 每个Agent完成后发送通知
5. 用户可随时介入修改或提供反馈

### 2.2 UI交互细节

#### 聊天界面
- **输入框**: 
  - 支持多行输入(Shift+Enter换行)
  - 文件拖拽上传
  - @提及特定Agent
  - 快捷命令(如/deploy, /preview)
- **消息展示**:
  - 用户消息右对齐(蓝色气泡)
  - Agent消息左对齐(灰色气泡)
  - 代码块语法高亮
  - 思考过程可折叠展示
  - 流式输出逐字显示

#### 代码编辑器
- **文件树**: 左侧边栏，支持展开/折叠
- **编辑区**: 中间主区域，多标签页
- **终端**: 底部可折叠，显示命令执行结果
- **快捷操作**:
  - Cmd/Ctrl + S: 保存文件
  - Cmd/Ctrl + P: 快速打开文件
  - Cmd/Ctrl + /: 注释代码

#### 预览面板
- **响应式视图**: 桌面/平板/手机切换
- **实时刷新**: 代码修改后自动更新
- **控制台**: 显示JavaScript错误和日志
- **网络面板**: 查看API请求(开发模式)

#### 任务面板
- **任务列表**: 显示当前会话所有任务
- **状态指示**: Pending/In Progress/Completed/Failed
- **依赖关系**: 可视化任务依赖图
- **Agent头像**: 显示任务负责人

---

## 3. 系统架构

### 3.1 整体架构图

详见 `architect.plantuml`，主要分为以下层次:

#### 前端层 (Frontend Layer)
- Web UI: 主应用入口
- Chat Interface: 聊天交互组件
- Code Editor: Monaco编辑器集成
- File Manager: 文件树和操作
- Preview Panel: 实时预览
- Task Dashboard: 任务管理面板

#### API网关层 (API Gateway Layer)
- FastAPI Gateway: RESTful API入口
- WebSocket Server: 实时双向通信
- Authentication Middleware: 认证和授权

#### Agent编排层 (Agent Orchestration Layer)
- Agent Manager: Agent生命周期管理
- Task Scheduler: 任务调度和依赖解析
- Message Router: 消息路由和广播
- Agent Pool: 
  - Mike Agent (团队负责人)
  - Emma Agent (产品经理)
  - Bob Agent (架构师)
  - Alex Agent (工程师)
  - David Agent (数据分析师)
  - Iris Agent (研究员)

#### 核心服务层 (Core Services Layer)
- LLM Service: 多模型统一接口
- Tool Executor: 工具执行引擎
- Code Sandbox: 代码沙箱
- Session Manager: 会话管理
- Context Store: 上下文存储

#### 工具集成层 (Tool & Integration Layer)
- Editor Tool: 文件读写
- Terminal Tool: 命令执行
- Search Tool: 网络搜索和语义检索
- Git Integration: GitHub/GitLab集成
- Supabase Client: 后端服务集成

#### 数据层 (Data Layer)
- PostgreSQL: 主数据库
- Redis: 缓存和队列
- Vector DB: 向量存储
- File Storage: S3或本地文件系统

#### 外部服务 (External Services)
- OpenAI API
- Anthropic API
- Google Gemini
- GitHub API
- Supabase

### 3.2 关键设计决策

#### 决策1: 为什么选择FastAPI而非Flask/Django?
- **性能**: 基于Starlette和Pydantic，异步性能优秀
- **类型安全**: 原生支持类型提示，减少运行时错误
- **文档**: 自动生成OpenAPI文档，前后端协作更高效
- **WebSocket**: 原生支持，无需额外插件

#### 决策2: 为什么自研Agent框架而非直接用LangChain?
- **灵活性**: 完全控制Agent行为和工具集成
- **性能**: 避免LangChain的抽象开销
- **定制化**: 针对MGX场景优化，如任务依赖管理
- **学习成本**: 团队可以深入理解Agent机制

#### 决策3: 为什么用Docker而非VM或直接执行?
- **安全**: 容器级别隔离，限制资源访问
- **轻量**: 启动快，资源占用少
- **一致性**: 开发、测试、生产环境一致
- **可扩展**: 易于横向扩展和负载均衡

---

## 4. 数据结构和接口

### 4.1 核心数据模型

详见 `class_diagram.plantuml`，主要包括:

#### Agent系统
- `BaseAgent`: 抽象基类，定义Agent通用接口
  - `process_message(message: Message) -> Response`: 处理消息
  - `execute_tool(tool_name: str, params: Dict) -> ToolResult`: 执行工具
  - `think(context: Context) -> Thought`: 思考过程
  - `act(action: Action) -> ActionResult`: 执行动作

- `MikeAgent`, `EmmaAgent`, `BobAgent`, `AlexAgent`, `DavidAgent`, `IrisAgent`: 具体Agent实现

#### 消息系统
- `Message`: 消息实体
  - `message_id: str`
  - `sender: str`
  - `receiver: str`
  - `content: str`
  - `message_type: MessageType`
  - `timestamp: datetime`

- `MessageRouter`: 消息路由器
  - `route_message(message: Message) -> None`
  - `broadcast_message(message: Message, agents: List[str]) -> None`

#### 任务管理
- `Task`: 任务实体
  - `task_id: str`
  - `task_type: str`
  - `description: str`
  - `assignee: str`
  - `dependencies: List[str]`
  - `status: TaskStatus`

- `TaskScheduler`: 任务调度器
  - `schedule_task(task: Task) -> None`
  - `get_next_task() -> Optional[Task]`
  - `resolve_dependencies(task: Task) -> bool`

#### LLM服务
- `LLMService`: LLM统一接口
  - `generate(prompt: str, model: str, params: Dict) -> LLMResponse`
  - `stream_generate(prompt: str, model: str, params: Dict) -> Iterator[str]`
  - `embed(text: str, model: str) -> List[float]`

- `LLMProvider`: 提供商接口
  - `OpenAIProvider`
  - `AnthropicProvider`
  - `GeminiProvider`

#### 工具系统
- `Tool`: 工具接口
  - `execute(params: Dict) -> ToolResult`
  - `validate_params(params: Dict) -> bool`

- `ToolExecutor`: 工具执行器
  - `register_tool(tool: Tool) -> None`
  - `execute_tool(tool_name: str, params: Dict) -> ToolResult`

### 4.2 关键API接口

#### 认证相关
```
POST /api/auth/register
Input: {
  "email": "string",
  "password": "string",
  "username": "string"
}
Output: {
  "user_id": "uuid",
  "token": "string"
}

POST /api/auth/login
Input: {
  "email": "string",
  "password": "string"
}
Output: {
  "user_id": "uuid",
  "token": "string",
  "expires_at": "timestamp"
}
```

#### 会话管理
```
POST /api/sessions/create
Input: {
  "user_id": "uuid"
}
Output: {
  "session_id": "uuid",
  "created_at": "timestamp",
  "ws_url": "string"
}

GET /api/sessions/{session_id}
Output: {
  "session_id": "uuid",
  "user_id": "uuid",
  "created_at": "timestamp",
  "last_active": "timestamp",
  "context": {
    "working_directory": "string",
    "file_tree": {},
    "variables": {}
  }
}
```

#### 消息交互
```
POST /api/chat/message
Input: {
  "session_id": "uuid",
  "content": "string",
  "message_type": "USER_INPUT"
}
Output: {
  "message_id": "uuid",
  "timestamp": "timestamp",
  "status": "processing"
}

WebSocket /ws/{session_id}
Client -> Server: {
  "type": "message",
  "content": "string"
}
Server -> Client: {
  "type": "agent_response",
  "agent": "Mike",
  "content": "string",
  "is_streaming": true
}
```

#### 文件操作
```
GET /api/files/{session_id}
Output: {
  "files": [
    {
      "path": "string",
      "type": "file|directory",
      "size": "integer",
      "updated_at": "timestamp"
    }
  ]
}

POST /api/files/write
Input: {
  "session_id": "uuid",
  "path": "string",
  "content": "string"
}
Output: {
  "success": true,
  "file_id": "uuid"
}

GET /api/files/read
Input: {
  "session_id": "uuid",
  "path": "string"
}
Output: {
  "content": "string",
  "file_type": "string"
}
```

#### 部署相关
```
POST /api/deploy
Input: {
  "session_id": "uuid",
  "platform": "vercel|netlify|github-pages",
  "config": {}
}
Output: {
  "deployment_id": "uuid",
  "url": "string",
  "status": "deploying"
}

GET /api/deploy/{deployment_id}/status
Output: {
  "status": "success|failed|deploying",
  "url": "string",
  "logs": "string"
}
```

---

## 5. 程序调用流程

### 5.1 完整用户请求处理流程

详见 `sequence_diagram.plantuml`，主要步骤:

#### 阶段1: 会话初始化
1. 用户访问平台 -> Web UI
2. Web UI -> API Gateway: POST /api/sessions/create
3. API Gateway -> Session Manager: create_session()
4. Session Manager -> Database: INSERT session
5. Database -> Session Manager: session_id
6. Session Manager -> API Gateway: Session对象
7. API Gateway -> Web UI: 返回session_id和ws_url
8. Web UI -> WebSocket Server: 建立WebSocket连接
9. WebSocket Server -> Session Manager: 注册连接

#### 阶段2: 用户提交开发需求
1. 用户输入: "创建一个作品集网站"
2. Web UI -> API Gateway: POST /api/chat/message
3. API Gateway -> Session Manager: get_session()
4. API Gateway -> Agent Manager: process_user_request()
5. Agent Manager -> Mike Agent: process_message()
6. Mike Agent -> LLM Service: generate(prompt)
7. LLM Service -> OpenAI API: 调用GPT-4
8. OpenAI API -> LLM Service: 返回任务计划
9. Mike Agent -> Agent Manager: create_task_plan()
10. Agent Manager -> WebSocket Server: 发送任务计划
11. WebSocket Server -> Web UI: 显示任务计划

#### 阶段3: 架构设计任务执行
1. Agent Manager -> Bob Agent: assign_task(task-2)
2. Bob Agent -> Tool Executor: execute_tool("Editor.read")
3. Tool Executor -> Editor Tool: read_file("prd.md")
4. Editor Tool -> Bob Agent: 返回PRD内容
5. Bob Agent -> LLM Service: generate(架构设计prompt)
6. LLM Service -> Anthropic API: 调用Claude
7. Anthropic API -> Bob Agent: 返回架构设计
8. Bob Agent -> Tool Executor: execute_tool("Editor.write")
9. Tool Executor -> Editor Tool: write_file("architecture.md")
10. Bob Agent -> Agent Manager: task_completed()
11. Agent Manager -> WebSocket Server: 通知完成

#### 阶段4: 代码实现任务执行
1. Agent Manager -> Alex Agent: assign_task(task-3)
2. Alex Agent -> Tool Executor: execute_tool("Editor.read")
3. Alex Agent -> LLM Service: generate(代码生成prompt)
4. LLM Service -> Alex Agent: 返回代码
5. 循环: 为每个组件生成代码
   - Alex Agent -> LLM Service: generate_code()
   - Alex Agent -> Tool Executor: execute_tool("Editor.write")
6. Alex Agent -> Tool Executor: execute_tool("Terminal.run", "npm install")
7. Tool Executor -> Code Sandbox: execute_command()
8. Code Sandbox -> Tool Executor: 返回执行结果
9. Alex Agent -> Tool Executor: execute_tool("Terminal.run", "npm run build")
10. Alex Agent -> Agent Manager: task_completed()

#### 阶段5: 预览和部署
1. 用户点击"预览"
2. Web UI -> API Gateway: GET /api/preview/{session_id}
3. API Gateway -> Session Manager: get_session_files()
4. Session Manager -> Database: SELECT files
5. API Gateway -> Web UI: 返回文件列表
6. Web UI: 渲染预览

7. 用户点击"部署"
8. Web UI -> API Gateway: POST /api/deploy
9. API Gateway -> Agent Manager: deploy_application()
10. Agent Manager -> Alex Agent: handle_deployment()
11. Alex Agent -> Tool Executor: execute_tool("Git.push")
12. Alex Agent -> Tool Executor: execute_tool("Deploy.vercel")
13. Tool Executor -> Alex Agent: 返回部署URL
14. Alex Agent -> WebSocket Server: 发送部署信息
15. WebSocket Server -> Web UI: 显示部署链接

#### 阶段6: 上下文持久化
1. Agent Manager -> Session Manager: update_session_context()
2. Session Manager -> Database: UPDATE sessions
3. Session Manager -> Context Store: save_context()
4. Context Store -> Redis: 缓存上下文
5. Context Store -> Vector DB: 存储embeddings

### 5.2 关键流程说明

#### Agent间通信机制
- 所有Agent通过Message Router进行通信
- 支持点对点消息和广播消息
- 消息带有优先级，确保关键消息优先处理
- 消息持久化到数据库，支持重放和审计

#### 工具执行流程
- Agent通过Tool Executor统一调用工具
- Tool Executor验证参数合法性
- 工具执行结果包含成功/失败状态和详细输出
- 执行历史记录到数据库，用于调试和优化

#### LLM调用策略
- 优先使用配置的默认模型
- 失败时自动fallback到备用模型
- 支持流式输出，提升用户体验
- 记录token使用量和成本

---

## 6. 数据库ER图

详见 `er_diagram.plantuml`，主要实体:

### 核心实体

#### users (用户表)
- id (PK): uuid
- email: varchar(255)
- username: varchar(100)
- password_hash: varchar(255)
- created_at: timestamp
- subscription_tier: varchar(50)
- credits_remaining: integer

#### sessions (会话表)
- id (PK): uuid
- user_id (FK): uuid -> users.id
- created_at: timestamp
- last_active: timestamp
- status: varchar(20)
- working_directory: text
- context_data: jsonb

#### messages (消息表)
- id (PK): uuid
- session_id (FK): uuid -> sessions.id
- sender: varchar(50)
- receiver: varchar(50)
- content: text
- message_type: varchar(50)
- timestamp: timestamp
- metadata: jsonb

#### tasks (任务表)
- id (PK): uuid
- session_id (FK): uuid -> sessions.id
- task_type: varchar(100)
- description: text
- assignee: varchar(50)
- status: varchar(20)
- priority: integer
- created_at: timestamp
- completed_at: timestamp
- dependencies: text[]
- output_data: jsonb

#### files (文件表)
- id (PK): uuid
- session_id (FK): uuid -> sessions.id
- file_path: text
- content: text
- file_type: varchar(50)
- size: bigint
- created_at: timestamp
- updated_at: timestamp
- checksum: varchar(64)

#### deployments (部署表)
- id (PK): uuid
- session_id (FK): uuid -> sessions.id
- platform: varchar(50)
- deployment_url: text
- deployment_id: varchar(255)
- status: varchar(20)
- created_at: timestamp
- config: jsonb

#### agent_executions (Agent执行记录表)
- id (PK): uuid
- session_id (FK): uuid -> sessions.id
- agent_name: varchar(50)
- task_id (FK): uuid -> tasks.id
- started_at: timestamp
- completed_at: timestamp
- status: varchar(20)
- input_data: jsonb
- output_data: jsonb
- error_message: text

#### tool_executions (工具执行记录表)
- id (PK): uuid
- agent_execution_id (FK): uuid -> agent_executions.id
- tool_name: varchar(100)
- parameters: jsonb
- result: jsonb
- execution_time: float
- timestamp: timestamp
- success: boolean
- error_message: text

#### llm_requests (LLM请求记录表)
- id (PK): uuid
- session_id (FK): uuid -> sessions.id
- agent_name: varchar(50)
- model: varchar(100)
- provider: varchar(50)
- prompt: text
- response: text
- tokens_used: integer
- cost: decimal(10,4)
- timestamp: timestamp
- parameters: jsonb

#### context_embeddings (上下文向量表)
- id (PK): uuid
- session_id (FK): uuid -> sessions.id
- content: text
- embedding: vector(1536)
- created_at: timestamp
- metadata: jsonb

#### projects (项目表)
- id (PK): uuid
- user_id (FK): uuid -> users.id
- name: varchar(255)
- description: text
- project_type: varchar(50)
- created_at: timestamp
- updated_at: timestamp
- repository_url: text
- is_public: boolean

#### project_sessions (项目会话关联表)
- project_id (FK, PK): uuid -> projects.id
- session_id (FK, PK): uuid -> sessions.id
- created_at: timestamp

### 关系说明
- 一个用户可以有多个会话和项目
- 一个会话包含多个消息、任务、文件、部署记录
- 一个任务对应多个Agent执行记录
- 一个Agent执行记录包含多个工具执行记录
- 项目和会话是多对多关系(通过project_sessions关联)

---

## 7. UI导航路径

详见 `ui_navigation.plantuml`，主要导航流程:

### 主要页面和导航深度

#### Level 0: 入口页面
- **Home Page**: 着陆页，展示产品特性和快速开始

#### Level 1: 认证和主面板
- **Authentication**: 登录/注册页面
- **Dashboard**: 用户主控制台
  - 最近会话
  - 快速操作
  - 使用统计

#### Level 2: 核心工作区
- **Chat Interface**: 主要工作空间
  - 消息历史
  - 输入框
  - Agent指示器
  - 文件附件
  
  **子面板** (Level 3):
  - Task Panel: 任务列表和状态
  - Code Editor: 代码编辑器
  - File Manager: 文件树管理

- **Preview & Deploy**: 预览和部署
  - 实时预览
  - 响应式视图
  - 控制台日志
  
  **子面板** (Level 3):
  - Deploy Options: 平台选择(Vercel/Netlify/GitHub Pages)

- **Projects**: 项目管理
  - 项目列表
  - 搜索和筛选
  
  **子面板** (Level 3):
  - Project Detail: 项目详情、会话、部署记录

- **Settings**: 设置页面
  - 用户资料
  - API密钥
  - 偏好设置
  - 账单信息

### 导航原则
1. **最大深度3-4层**: 避免用户迷失
2. **高频功能前置**: 聊天、预览、部署一键可达
3. **明确返回路径**: 每个页面都有清晰的返回按钮
4. **快捷导航**: 顶部导航栏始终可见
5. **状态保持**: 切换页面时保持工作状态

### 快捷操作
- 从任何页面可以快速返回Dashboard
- 从聊天界面可以直接跳转到预览/部署
- 从项目列表可以直接打开会话
- 全局搜索功能(Cmd/Ctrl + K)

---

## 8. 不明确的方面

### 8.1 需要进一步明确的技术细节

#### 1. LLM成本控制策略
- **问题**: 多模型调用成本可能很高，如何优化?
- **待决策**:
  - 是否实现请求缓存机制?
  - 如何平衡模型性能和成本?
  - 是否需要用户付费订阅模式?

#### 2. 代码执行环境的资源限制
- **问题**: Docker容器的CPU、内存、磁盘限制具体数值?
- **待决策**:
  - 免费用户和付费用户的资源配额差异?
  - 如何处理长时间运行的任务?
  - 是否需要任务排队机制?

#### 3. 多用户协作功能
- **问题**: MVP阶段是否需要支持多用户协作?
- **待决策**:
  - 实时协作编辑(类似Google Docs)?
  - 权限管理(只读/编辑/管理员)?
  - 冲突解决机制?

#### 4. 数据隐私和安全
- **问题**: 用户代码和数据的隐私保护措施?
- **待决策**:
  - 是否支持私有部署?
  - 数据加密存储?
  - 是否将用户代码用于模型训练?

#### 5. Agent能力边界
- **问题**: 每个Agent的具体能力范围?
- **待决策**:
  - Emma的市场调研能力(是否需要接入真实数据源)?
  - David的数据分析能力(支持哪些数据格式和可视化库)?
  - Iris的网络爬虫能力(如何避免违反网站ToS)?

### 8.2 需要用户反馈的产品决策

#### 1. 定价模型
- 免费层: 每月X个会话, Y个部署, Z个LLM请求
- 付费层: 价格和功能差异?
- 企业层: 私有部署和定制化支持?

#### 2. 部署平台优先级
- MVP阶段优先支持哪些平台?
- Vercel/Netlify/GitHub Pages/自定义服务器?

#### 3. 编程语言支持顺序
- Phase 1: JavaScript/TypeScript (前端)
- Phase 2: Python (数据科学)
- Phase 3: Go/Java (后端服务)?

#### 4. 模板库范围
- 需要预置哪些项目模板?
- 作品集/博客/电商/SaaS/数据可视化?

### 8.3 技术风险和缓解措施

#### 风险1: LLM输出不稳定
- **缓解**: 多次生成+投票机制, 人工审核关键代码
- **监控**: 记录生成质量指标, 持续优化prompt

#### 风险2: 容器资源耗尽
- **缓解**: 严格资源限制, 任务超时自动终止
- **监控**: 实时监控资源使用, 自动扩缩容

#### 风险3: WebSocket连接不稳定
- **缓解**: 自动重连机制, 消息持久化
- **监控**: 连接状态监控, 异常告警

#### 风险4: 数据库性能瓶颈
- **缓解**: 读写分离, 索引优化, 缓存策略
- **监控**: 慢查询日志, 数据库性能指标

---

## 9. 后续迭代计划

### Phase 1: MVP核心 (4-6周)
- ✅ 基础架构搭建
- ✅ 用户认证和会话管理
- ✅ Mike + Alex Agent实现
- ✅ 前端网页开发能力
- ✅ 基础预览和GitHub集成

### Phase 2: 功能扩展 (4-6周)
- Emma + Bob Agent实现
- Supabase后端集成
- 多模型切换
- 部署到Vercel/Netlify
- 项目模板库

### Phase 3: 高级功能 (6-8周)
- David + Iris Agent实现
- Python/数据科学支持
- 协作功能
- 性能优化和监控
- 企业版功能

### Phase 4: 生态建设 (持续)
- 插件系统
- 社区模板市场
- 开发者API
- 移动端支持

---

## 10. 总结

本系统设计文档详细描述了MGX MVP的完整技术架构，包括:
- 后端Agent系统和前端交互界面的设计
- 多Agent协作机制和任务调度系统
- LLM集成方案和工具系统
- 数据库设计和API接口规范
- 完整的用户交互流程和程序调用流程

**核心优势**:
1. **模块化设计**: 各层次职责清晰，易于扩展和维护
2. **异步架构**: 高性能，支持大规模并发
3. **安全隔离**: Docker沙箱确保代码执行安全
4. **灵活可扩展**: 支持多模型、多工具、多部署平台

**技术亮点**:
- 自研多Agent协作框架
- 统一的LLM服务抽象层
- 实时流式输出
- 完善的上下文管理和记忆机制

该设计方案在满足MVP核心功能的同时，为后续迭代预留了充分的扩展空间。