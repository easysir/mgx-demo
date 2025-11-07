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

#### 挑战4: 实时流式输出和状态同步
**解决方案**:
- WebSocket双向通信
- LLM流式API + Server-Sent Events (SSE)
- 前端增量渲染，避免重绘整个界面
- 消息队列缓冲，防止消息丢失
- **ChatUI整合Agent状态和任务进度**，统一展示界面

### 1.3 MVP阶段功能范围

**Phase 1 (MVP核心)**:
- ✅ 用户认证和会话管理
- ✅ 基础聊天界面和流式输出（整合Agent状态和任务进度）
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
5. 点击"新建会话"进入聊天工作区
6. 输入需求: "创建一个个人作品集网站"
7. Mike Agent分析需求并制定任务计划（在ChatUI中显示任务总览）
8. Alex Agent开始生成代码（ChatUI显示Agent工作状态和进度）
9. 用户在代码编辑器中查看生成的文件（占据70%屏幕空间）
10. 点击"预览"查看实时效果
11. 满意后点击"部署"发布到线上

#### 流程2: 迭代修改现有项目
1. 用户从Dashboard选择已有项目
2. 进入会话，ChatUI显示历史对话和当前状态
3. 输入修改需求: "把导航栏改成深色主题"
4. Alex Agent理解上下文并修改相关文件（状态实时显示在ChatUI）
5. 用户在预览中实时看到变化
6. 确认后提交到GitHub

#### 流程3: 复杂需求多Agent协作
1. 用户输入: "开发一个带后端的博客系统"
2. Mike Agent识别为复杂任务，分配给多个Agent
3. ChatUI显示任务总览卡片，包含:
   - Emma: 分析需求，创建功能清单
   - Bob: 设计系统架构和数据库模型
   - Alex: 实现前后端代码
4. 每个Agent的工作消息包含状态指示器和进度条
5. 用户可随时在ChatUI中查看整体进度
6. 每个Agent完成后发送完成消息
7. 用户可随时介入修改或提供反馈

### 2.2 UI交互细节

#### ChatUI（整合版）- 占据30%屏幕宽度
**核心功能整合**:
- **对话消息流**: 用户输入和Agent回复
- **Agent状态展示**: 嵌入在消息卡片中
- **任务进度显示**: 进度条和百分比
- **工作流可视化**: 可折叠的任务列表
- **输入框**: 支持多行、文件上传、@提及

**消息类型**:

1. **普通对话消息**
```typescript
{
  type: 'message',
  role: 'user' | 'assistant',
  content: string,
  timestamp: datetime
}
```

2. **Agent工作消息**（整合状态）
```typescript
{
  type: 'agent_message',
  agent: 'Mike' | 'Emma' | 'Bob' | 'Alex' | 'David' | 'Iris',
  status: 'working' | 'waiting' | 'completed' | 'failed',
  content: string,
  progress?: number,  // 0-100
  tasks?: Task[],
  timestamp: datetime
}
```

3. **任务总览消息**（Mike发送）
```typescript
{
  type: 'task_overview',
  agent: 'Mike',
  overall_progress: number,  // 0-100
  tasks: [
    {
      task_id: string,
      description: string,
      assignee: string,
      status: 'pending' | 'in_progress' | 'completed',
      progress: number
    }
  ],
  timestamp: datetime
}
```

**交互特性**:
- **状态指示器**: 
  - 🟢 Working (动画脉冲)
  - ⏸️ Waiting (灰色)
  - ✅ Completed (绿色勾选)
  - ❌ Failed (红色叉号)
- **进度条**: 嵌入Agent消息卡片，实时更新
- **任务列表**: 可折叠展开，点击查看详情
- **折叠功能**: 支持折叠ChatUI以最大化编辑预览空间
- **流式输出**: Agent回复逐字显示，提升体验

**输入框功能**:
- 支持多行输入(Shift+Enter换行)
- 文件拖拽上传
- @提及特定Agent
- 快捷命令(如/deploy, /preview, /help)

#### 代码编辑器 + 预览区域 - 占据70%屏幕宽度
**布局**:
- 上方: 文件树（可折叠）
- 中间: Monaco编辑器（多标签页）
- 下方: 终端（可折叠）
- 右侧: 实时预览面板（可切换设备视图）

**编辑器功能**:
- 语法高亮和自动补全
- 多文件标签页
- 代码格式化
- 错误提示和修复建议

**预览面板功能**:
- **响应式视图**: 桌面/平板/手机切换
- **实时刷新**: 代码修改后自动更新
- **控制台**: 显示JavaScript错误和日志
- **网络面板**: 查看API请求(开发模式)
- **全屏模式**: 支持全屏预览和部署

---

## 3. 系统架构

### 3.1 整体架构图

详见 `architect.plantuml`，主要分为以下层次:

#### 前端层 (Frontend Layer)
- Web UI: 主应用入口
- **Chat Interface (整合版)**: 
  - 对话消息流
  - Agent状态展示
  - 任务进度显示
  - 输入框
  - 工作流可视化
  - **占据30%屏幕宽度，支持折叠**
- Code Editor: Monaco编辑器集成
- File Manager: 文件树和操作
- Preview Panel: 实时预览
- **布局**: ChatUI (30%) | Editor+Preview (70%)

#### API网关层 (API Gateway Layer)
- FastAPI Gateway: RESTful API入口
- WebSocket Server: 实时双向通信（支持流式输出和状态广播）
- Authentication Middleware: 认证和授权

#### Agent编排层 (Agent Orchestration Layer)
- Agent Manager: Agent生命周期管理
- Task Scheduler: 任务调度和依赖解析（实时广播任务状态更新）
- Message Router: 消息路由和广播（发送到WebSocket）
- Agent Pool: 
  - Mike Agent (团队负责人) - 发送任务总览消息
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
- Context Store: 上下文存储（包含当前任务计划）

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

#### 决策1: 为什么整合TaskDashboard到ChatUI?
- **减少UI碎片化**: 用户不需要在多个面板间切换
- **提升空间利用**: 为代码编辑器和预览预留70%屏幕空间
- **统一交互模式**: Agent状态、任务进度、对话消息统一展示
- **简化信息架构**: 所有Agent相关信息集中在一个界面
- **支持折叠**: ChatUI可折叠以最大化编辑预览空间

#### 决策2: 为什么选择FastAPI而非Flask/Django?
- **性能**: 基于Starlette和Pydantic，异步性能优秀
- **类型安全**: 原生支持类型提示，减少运行时错误
- **文档**: 自动生成OpenAPI文档，前后端协作更高效
- **WebSocket**: 原生支持，无需额外插件

#### 决策3: 为什么自研Agent框架而非直接用LangChain?
- **灵活性**: 完全控制Agent行为和工具集成
- **性能**: 避免LangChain的抽象开销
- **定制化**: 针对MGX场景优化，如任务依赖管理和实时状态广播
- **学习成本**: 团队可以深入理解Agent机制

#### 决策4: 为什么用Docker而非VM或直接执行?
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

- `MikeAgent`: 团队负责人
  - `send_task_overview(session_id: str, tasks: List[Task]) -> None`: 发送任务总览到ChatUI

- `EmmaAgent`, `BobAgent`, `AlexAgent`, `DavidAgent`, `IrisAgent`: 具体Agent实现

#### 消息系统（扩展）
- `Message`: 基础消息实体
  - `message_id: str`
  - `sender: str`
  - `receiver: str`
  - `content: str`
  - `message_type: MessageType`
  - `timestamp: datetime`

- `AgentMessage`: Agent工作消息（新增）
  - `agent: str`
  - `status: AgentStatus` (working/waiting/completed/failed)
  - `progress: Optional[float]` (0-100)
  - `tasks: Optional[List[Task]]`
  - `create_working_message()`: 创建工作中消息
  - `create_completed_message()`: 创建完成消息

- `TaskOverviewMessage`: 任务总览消息（新增）
  - `agent: str = "Mike"`
  - `overall_progress: float`
  - `tasks: List[Task]`
  - `update_progress()`: 更新整体进度

- `MessageRouter`: 消息路由器
  - `route_message(message: Message) -> None`
  - `broadcast_message(message: Message, agents: List[str]) -> None`
  - `send_to_websocket(session_id: str, message: Message) -> None`: 发送到WebSocket

#### 任务管理（增强）
- `Task`: 任务实体
  - `task_id: str`
  - `task_type: str`
  - `description: str`
  - `assignee: str`
  - `dependencies: List[str]`
  - `status: TaskStatus`
  - `progress: float` (新增)
  - `update_progress(progress: float) -> None`: 更新进度

- `TaskScheduler`: 任务调度器
  - `schedule_task(task: Task) -> None`
  - `get_next_task() -> Optional[Task]`
  - `update_task_progress(task_id: str, progress: float) -> None`: 更新任务进度
  - `broadcast_task_update(session_id: str) -> None`: 广播任务更新到ChatUI
  - `resolve_dependencies(task: Task) -> bool`

- `TaskPlan`: 任务计划
  - `calculate_overall_progress() -> float`: 计算整体进度

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

#### WebSocket服务（增强）
- `WebSocketServer`: WebSocket服务器
  - `connect(session_id: str, websocket: WebSocket) -> None`
  - `disconnect(session_id: str) -> None`
  - `send_to_session(session_id: str, message: Message) -> None`
  - `stream_agent_response(session_id: str, chunks: Iterator[str]) -> None`: 流式输出

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
    "variables": {},
    "current_task_plan": {}
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

Server -> Client (普通消息): {
  "type": "message",
  "role": "assistant",
  "content": "string",
  "timestamp": "datetime"
}

Server -> Client (Agent工作消息): {
  "type": "agent_message",
  "agent": "Alex",
  "status": "working",
  "content": "正在生成代码...",
  "progress": 45.5,
  "timestamp": "datetime"
}

Server -> Client (任务总览): {
  "type": "task_overview",
  "agent": "Mike",
  "overall_progress": 60.0,
  "tasks": [
    {
      "task_id": "task-1",
      "description": "需求分析",
      "assignee": "Emma",
      "status": "completed",
      "progress": 100
    },
    {
      "task_id": "task-2",
      "description": "代码生成",
      "assignee": "Alex",
      "status": "in_progress",
      "progress": 45.5
    }
  ],
  "timestamp": "datetime"
}

Server -> Client (流式输出): {
  "type": "stream_chunk",
  "agent": "Alex",
  "chunk": "部分内容",
  "is_final": false
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
10. **Mike Agent -> WebSocket Server: 发送TaskOverviewMessage**
11. **WebSocket Server -> ChatUI: 显示任务总览卡片**

#### 阶段3: 架构设计任务执行
1. Agent Manager -> Bob Agent: assign_task(task-2)
2. **Bob Agent -> WebSocket Server: 发送AgentMessage(status='working')**
3. **ChatUI: 显示Bob工作状态和进度条**
4. Bob Agent -> Tool Executor: execute_tool("Editor.read")
5. Tool Executor -> Editor Tool: read_file("prd.md")
6. Editor Tool -> Bob Agent: 返回PRD内容
7. Bob Agent -> LLM Service: generate(架构设计prompt)
8. LLM Service -> Anthropic API: 调用Claude
9. **Bob Agent -> WebSocket Server: 更新进度(progress=50)**
10. **ChatUI: 更新进度条到50%**
11. Anthropic API -> Bob Agent: 返回架构设计
12. Bob Agent -> Tool Executor: execute_tool("Editor.write")
13. Tool Executor -> Editor Tool: write_file("architecture.md")
14. **Bob Agent -> WebSocket Server: 发送AgentMessage(status='completed', progress=100)**
15. **ChatUI: 显示Bob完成状态✅**
16. Bob Agent -> Agent Manager: task_completed()
17. **Agent Manager -> WebSocket Server: 更新TaskOverview(overall_progress=33)**

#### 阶段4: 代码实现任务执行
1. Agent Manager -> Alex Agent: assign_task(task-3)
2. **Alex Agent -> WebSocket Server: 发送AgentMessage(status='working')**
3. Alex Agent -> Tool Executor: execute_tool("Editor.read")
4. Alex Agent -> LLM Service: generate(代码生成prompt)
5. LLM Service -> Alex Agent: 返回代码
6. 循环: 为每个组件生成代码
   - Alex Agent -> LLM Service: generate_code()
   - **Alex Agent -> WebSocket Server: 更新进度(progress=20, 40, 60...)**
   - **ChatUI: 实时更新进度条**
   - Alex Agent -> Tool Executor: execute_tool("Editor.write")
7. Alex Agent -> Tool Executor: execute_tool("Terminal.run", "npm install")
8. Tool Executor -> Code Sandbox: execute_command()
9. Code Sandbox -> Tool Executor: 返回执行结果
10. **Alex Agent -> WebSocket Server: 更新进度(progress=80)**
11. Alex Agent -> Tool Executor: execute_tool("Terminal.run", "npm run build")
12. **Alex Agent -> WebSocket Server: 发送AgentMessage(status='completed', progress=100)**
13. **ChatUI: 显示Alex完成状态✅**
14. Alex Agent -> Agent Manager: task_completed()
15. **Agent Manager -> WebSocket Server: 更新TaskOverview(overall_progress=100)**

#### 阶段5: 预览和部署
1. 用户点击"预览"
2. Web UI -> API Gateway: GET /api/preview/{session_id}
3. API Gateway -> Session Manager: get_session_files()
4. Session Manager -> Database: SELECT files
5. API Gateway -> Web UI: 返回文件列表
6. Web UI: 渲染预览（占据70%屏幕空间）

7. 用户点击"部署"
8. Web UI -> API Gateway: POST /api/deploy
9. API Gateway -> Agent Manager: deploy_application()
10. Agent Manager -> Alex Agent: handle_deployment()
11. **Alex Agent -> WebSocket Server: 发送AgentMessage(status='working', content='正在部署...')**
12. Alex Agent -> Tool Executor: execute_tool("Git.push")
13. Alex Agent -> Tool Executor: execute_tool("Deploy.vercel")
14. Tool Executor -> Alex Agent: 返回部署URL
15. **Alex Agent -> WebSocket Server: 发送AgentMessage(status='completed', content='部署成功')**
16. **ChatUI: 显示部署链接**
17. Alex Agent -> WebSocket Server: 发送部署信息
18. WebSocket Server -> Web UI: 显示部署链接

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
- **Agent工作状态通过WebSocket实时推送到ChatUI**
- **任务进度更新触发TaskOverview刷新**
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
- **支持流式输出，通过WebSocket推送到ChatUI**
- 记录token使用量和成本

#### 实时状态同步机制（新增）
- **Agent状态变化**: Agent -> WebSocket -> ChatUI
- **任务进度更新**: TaskScheduler -> WebSocket -> ChatUI
- **流式输出**: LLM -> Agent -> WebSocket -> ChatUI
- **消息类型**: message, agent_message, task_overview, stream_chunk

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
- **progress: float** (新增)
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
- **progress: float** (新增)
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
- **Chat Workspace**: 主要工作空间
  - **布局**: [ChatUI 30%] [Editor+Preview 70%]
  
  **Chat Interface (整合版)**:
  - 对话消息流
  - Agent状态指示器（嵌入消息卡片）
  - 任务进度条（嵌入Agent消息）
  - 任务列表（可折叠展开）
  - 输入框
  - 支持折叠以最大化编辑预览空间
  
  **Editor & Preview Area**:
  - Code Editor (Monaco)
  - File Tree
  - Terminal
  - Live Preview
  - Device selector (响应式视图)

- **Preview & Deploy**: 全屏预览和部署
  - 实时预览
  - 响应式视图
  - 控制台日志
  - 部署选项 (Vercel/Netlify/GitHub Pages)

- **Projects**: 项目管理
  - 项目列表
  - 搜索和筛选
  - 项目详情、会话、部署记录

- **Settings**: 设置页面
  - 用户资料
  - API密钥
  - 偏好设置
  - 账单信息

### 导航原则
1. **最大深度2层**: 避免用户迷失（优化后）
2. **高频功能前置**: 聊天、预览、部署一键可达
3. **明确返回路径**: 每个页面都有清晰的返回按钮
4. **快捷导航**: 顶部导航栏始终可见
5. **状态保持**: 切换页面时保持工作状态
6. **空间优化**: ChatUI占30%，Editor+Preview占70%

### 快捷操作
- 从任何页面可以快速返回Dashboard
- 从聊天工作区可以直接跳转到全屏预览/部署
- 从项目列表可以直接打开会话
- 全局搜索功能(Cmd/Ctrl + K)
- ChatUI折叠快捷键(Cmd/Ctrl + B)

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

#### 6. ChatUI折叠和响应式设计
- **问题**: ChatUI折叠后的最小宽度?
- **待决策**:
  - 折叠后是否只显示输入框?
  - 移动端如何处理30/70布局?
  - 是否支持拖拽调整比例?

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

#### 风险5: ChatUI信息过载
- **缓解**: 消息折叠、分页、搜索功能
- **监控**: 用户交互数据, 优化信息展示

---

## 9. 后续迭代计划

### Phase 1: MVP核心 (4-6周)
- ✅ 基础架构搭建
- ✅ 用户认证和会话管理
- ✅ Mike + Alex Agent实现
- ✅ **ChatUI（整合版）实现**
  - 对话消息流
  - Agent状态展示
  - 任务进度显示
  - 支持折叠
- ✅ 前端网页开发能力
- ✅ 基础预览和GitHub集成
- ✅ **WebSocket实时状态同步**

### Phase 2: 功能扩展 (4-6周)
- Emma + Bob Agent实现
- Supabase后端集成
- 多模型切换
- 部署到Vercel/Netlify
- 项目模板库
- **ChatUI高级功能**:
  - 消息搜索
  - 历史对话导出
  - 自定义主题

### Phase 3: 高级功能 (6-8周)
- David + Iris Agent实现
- Python/数据科学支持
- 协作功能
- 性能优化和监控
- 企业版功能
- **响应式布局优化**

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
- **优化的UI布局: ChatUI(30%) | Editor+Preview(70%)**

**核心优势**:
1. **模块化设计**: 各层次职责清晰，易于扩展和维护
2. **异步架构**: 高性能，支持大规模并发
3. **安全隔离**: Docker沙箱确保代码执行安全
4. **灵活可扩展**: 支持多模型、多工具、多部署平台
5. **统一交互**: ChatUI整合Agent状态和任务进度，提升用户体验
6. **空间优化**: 为代码编辑和预览预留70%屏幕空间

**技术亮点**:
- 自研多Agent协作框架
- 统一的LLM服务抽象层
- 实时流式输出和状态同步
- 完善的上下文管理和记忆机制
- **ChatUI整合设计，减少UI碎片化**

**架构优化**:
- 删除独立的TaskDashboard组件
- 将Agent状态、任务进度整合到ChatUI
- 扩展消息类型支持AgentMessage和TaskOverviewMessage
- 增强WebSocket服务支持实时状态广播
- 优化UI布局，提升空间利用率

该设计方案在满足MVP核心功能的同时，为后续迭代预留了充分的扩展空间。