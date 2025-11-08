# MGX MVP 系统设计文档

## 1. 实现方案

### 1.1 核心技术选型

#### 后端技术栈
- **框架**: FastAPI (Python 3.11+)
  - 理由: 高性能异步框架，原生支持WebSocket，类型提示完善，文档自动生成
- **Agent框架**: 自研多Agent协作系统
  - 理由: 灵活可控，支持自定义Agent行为和精确的任务调度
  - LLM调用: 使用 LangChain 的 LLM 封装（ChatOpenAI, ChatAnthropic 等）
  - 工具系统: 参考 LangChain Tool 接口，实现自定义 ToolExecutor
  - 不依赖 LangChain 的 Agent 编排能力，实现自己的协作逻辑
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
- Mike Agent作为唯一入口和决策者
- 实现基于有向无环图(DAG)的任务依赖管理
- Mike负责任务规划、分配、监控和质量把关
- 其他Agent完成任务后向Mike汇报，由Mike决定下一步

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
- ✅ 完整的Agent团队（6人团队，缺一不可）:
  - Mike Agent (Team Leader) - 需求分析、任务规划、团队协调、质量把关
  - Emma Agent (Product Manager) - 需求分析、市场调研、PRD编写
  - Bob Agent (Architect) - 系统架构设计、技术选型、设计文档
  - Alex Agent (Engineer) - 代码开发、测试、部署
  - David Agent (Data Analyst) - 数据分析、可视化、机器学习（基础能力）
  - Iris Agent (Researcher) - 信息收集、网络搜索、文档研究
- ✅ 前端网页开发能力(React/Next.js/Shadcn-ui)
- ✅ 代码编辑器和文件管理
- ✅ 预览功能（Preview Server + nginx 反向代理）
- ✅ GitHub集成(代码提交)
- ✅ WebSocket 鉴权和安全机制（JWT + Token 刷新）
**Phase 2 (功能扩展)**:
- Supabase后端集成（增强 Alex 的后端能力）
- 多模型切换（增强 LLM Service）
- 部署到Vercel/Netlify（增强部署能力）
- Python/数据科学支持（增强 David 的能力）
- 高级搜索与爬虫支持（增强 Iris 的能力）
**Phase 3 (高级功能)**:
- 协作功能(多用户实时编辑)
- 项目模板库
- 私有部署支持
- 企业级功能（权限管理、审计日志）
- 性能优化与扩展性


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
8. Mike分配任务给Bob设计架构
9. Bob完成后向Mike汇报，Mike审查通过
10. Mike分配任务给Alex生成代码（ChatUI显示Agent工作状态和进度）
11. Alex完成后向Mike汇报，Mike审查通过
12. 用户在代码编辑器中查看生成的文件（占据70%屏幕空间）
13. 点击"预览"查看实时效果
14. 满意后点击"部署"发布到线上

#### 流程2: 迭代修改现有项目
1. 用户从Dashboard选择已有项目
2. 进入会话，ChatUI显示历史对话和当前状态
3. 输入修改需求: "把导航栏改成深色主题"
4. Mike分析需求，直接分配给Alex修改
5. Alex完成后向Mike汇报，Mike审查通过（状态实时显示在ChatUI）
6. 用户在预览中实时看到变化
7. 确认后提交到GitHub

#### 流程3: 复杂需求多Agent协作
1. 用户输入: "开发一个带后端的博客系统"
2. Mike分析需求，识别为复杂任务
3. Mike制定任务计划并发送TaskOverview到ChatUI:
   - Emma: 分析需求，创建功能清单
   - Bob: 设计系统架构和数据库模型
   - Alex: 实现前后端代码
4. Mike依次分配任务，每个Agent完成后向Mike汇报
5. Mike评估每个交付物，决定是否继续下一步
6. 所有任务完成后，Mike通知用户

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
- FastAPI Gateway: RESTful API入口，所有请求转发给Mike
- WebSocket Server: 实时双向通信（支持流式输出和状态广播）
- Authentication Middleware: 认证和授权

#### Agent编排层 (Agent Orchestration Layer) - **核心改进**

**Mike Agent (Team Leader) - 唯一入口和决策者**:
- **角色定位**: 团队大脑，所有用户请求的唯一入口
- **核心职责**:
  - 需求分析: 理解用户意图，评估复杂度
  - 任务规划: 制定执行计划，分解任务
  - 团队协调: 分配任务给合适的Agent
  - 进度监控: 实时追踪任务状态
  - 质量把关: 审查每个Agent的交付物
  - 决策下一步: 根据完成情况决定后续行动
- **消息流**: 用户 → Mike → 其他Agent → Mike → 用户

**Agent Manager - 技术支撑层**:
- **角色定位**: 从"决策者"变为"技术支撑"
- **核心职责**:
  - 管理Agent实例的生命周期
  - 执行Mike的指令
  - 提供消息路由服务
  - 维护会话状态
- **不再负责**: 任务分配决策、工作流编排

**Task Scheduler - 任务调度器**:
- 管理任务队列和依赖关系
- 任务完成时通知Mike（而非直接分配下一个任务）
- 实时广播任务状态更新到ChatUI

**Message Router - 消息路由器**:
- 将用户消息路由到Mike
- 将Mike的指令路由到目标Agent
- 将Agent的汇报路由回Mike
- 广播状态更新到WebSocket

**Execution Team - 执行团队**:
- Emma Agent (产品经理): 需求分析和调研
- Bob Agent (架构师): 系统架构设计
- Alex Agent (工程师): 代码开发和部署
- David Agent (数据分析师): 数据处理和可视化
- Iris Agent (研究员): 信息收集和研究
- **所有Agent完成任务后向Mike汇报，不直接与用户交互**

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

#### 决策2: 为什么Mike必须是唯一入口?
- **符合真实团队管理**: Team Leader是决策者，不是平级成员
- **清晰的责任链**: 用户 → Mike → Team → Mike → 用户
- **质量保证**: Mike审查每个交付物，确保质量
- **灵活决策**: Mike根据实际情况动态调整任务分配
- **避免混乱**: 防止多个Agent直接响应用户造成冲突

#### 决策3: 为什么选择FastAPI而非Flask/Django?
- **性能**: 基于Starlette和Pydantic，异步性能优秀
- **类型安全**: 原生支持类型提示，减少运行时错误
- **文档**: 自动生成OpenAPI文档，前后端协作更高效
- **WebSocket**: 原生支持，无需额外插件

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

**MikeAgent (Team Leader)** - 核心决策者:
- `analyze_requirement(message: str) -> RequirementAnalysis`: 分析用户需求
- `create_task_plan(analysis: RequirementAnalysis) -> TaskPlan`: 制定任务计划
- `assign_task_to_agent(agent: str, task: Task) -> None`: 分配任务给Agent
- `on_agent_completed(agent: str, result: Any) -> NextAction`: Agent完成后的决策
- `review_deliverable(result: Any) -> ReviewResult`: 审查交付物
- `monitor_team_progress() -> ProgressReport`: 监控团队进度
- `decide_next_step(context: Context) -> Decision`: 决定下一步行动
- `send_task_overview(session_id: str, tasks: List[Task]) -> None`: 发送任务总览

**其他Agent (Execution Team)**:
- `EmmaAgent`, `BobAgent`, `AlexAgent`, `DavidAgent`, `IrisAgent`
- 所有Agent都有 `report_to_mike(result: Any) -> None` 方法
- 完成任务后向Mike汇报，而非直接与用户交互

#### 消息系统（扩展）

**Message** - 基础消息实体:
- `message_id: str`
- `sender: str`
- `receiver: str`
- `content: str`
- `message_type: MessageType`
- `timestamp: datetime`

**MessageType** - 消息类型枚举:
- USER_INPUT: 用户输入
- AGENT_RESPONSE: Agent回复
- AGENT_MESSAGE: Agent工作消息
- TASK_OVERVIEW: 任务总览
- TASK_ASSIGNMENT: 任务分配
- AGENT_REPORT: Agent汇报
- TOOL_EXECUTION: 工具执行
- SYSTEM_NOTIFICATION: 系统通知

**AgentMessage** - Agent工作消息（新增）:
- `agent: str`
- `status: AgentStatus` (working/waiting/completed/failed)
- `progress: Optional[float]` (0-100)
- `tasks: Optional[List[Task]]`

**TaskOverviewMessage** - 任务总览消息（Mike发送）:
- `agent: str = "Mike"`
- `overall_progress: float`
- `tasks: List[Task]`

**MessageRouter** - 消息路由器:
- `route_to_mike(message: Message) -> None`: 路由到Mike
- `route_from_mike(message: Message, target: str) -> None`: 从Mike路由
- `send_to_websocket(session_id: str, message: Message) -> None`: 发送到WebSocket

#### 任务管理（增强）

**Task** - 任务实体:
- `task_id: str`
- `task_type: str`
- `description: str`
- `assignee: str`
- `dependencies: List[str]`
- `status: TaskStatus`
- `progress: float`
- `created_by: str = "Mike"` (新增)
- `update_progress(progress: float) -> None`: 更新进度

**TaskScheduler** - 任务调度器:
- `schedule_task(task: Task) -> None`
- `update_task_progress(task_id: str, progress: float) -> None`
- `notify_mike_on_completion(task: Task) -> None`: 完成时通知Mike
- `broadcast_task_update(session_id: str) -> None`: 广播任务更新

**TaskPlan** - 任务计划:
- `created_by: str = "Mike"` (新增)
- `calculate_overall_progress() -> float`: 计算整体进度

**AgentManager** - Agent管理器（角色调整）:
- `mike_agent: MikeAgent`: Mike实例引用
- `execute_mike_instruction(instruction: Instruction) -> None`: 执行Mike指令
- `notify_mike_completion(agent_name: str, result: Any) -> None`: 通知Mike完成

#### LLM服务
- `LLMService`: LLM统一接口
- `LLMProvider`: 提供商接口 (OpenAI, Anthropic, Gemini)

#### 工具系统
- `Tool`: 工具接口
- `ToolExecutor`: 工具执行器

#### WebSocket服务（增强）
- `WebSocketServer`: 
  - `stream_agent_response(session_id: str, chunks: Iterator[str]) -> None`: 流式输出

### 4.2 关键API接口

#### 认证相关
```
POST /api/auth/register
POST /api/auth/login
```

#### 会话管理
```
POST /api/sessions/create
GET /api/sessions/{session_id}
```

#### 消息交互
```
POST /api/chat/message
Input: {
  "session_id": "uuid",
  "content": "string",
  "message_type": "USER_INPUT"
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
```

#### 文件操作
```
GET /api/files/{session_id}
POST /api/files/write
GET /api/files/read
```

#### 部署相关
```
POST /api/deploy
GET /api/deploy/{deployment_id}/status
```

---

## 5. 程序调用流程

### 5.1 完整用户请求处理流程

详见 `sequence_diagram.plantuml`，主要步骤:

#### 阶段1: 会话初始化
1. 用户访问平台 -> Web UI
2. Web UI -> API Gateway: POST /api/sessions/create
3. API Gateway -> Database: 创建会话
4. Web UI -> WebSocket Server: 建立连接

#### 阶段2: 用户提交需求 (Mike作为唯一入口)
1. 用户输入: "创建一个作品集网站"
2. Web UI -> API Gateway: POST /api/chat/message
3. **API Gateway -> Mike Agent: 转发用户消息** (所有请求先到Mike)
4. Mike -> LLM Service: 分析需求
5. Mike -> Mike: 创建任务计划
6. **Mike -> WebSocket: 发送TaskOverviewMessage**
7. WebSocket -> ChatUI: 显示任务总览

#### 阶段3: Mike分配架构设计任务
1. **Mike -> Agent Manager: 获取Bob实例**
2. **Mike -> Bob: 分配任务** "设计作品集网站架构"
3. Bob -> WebSocket: 发送AgentMessage(status='working')
4. Bob -> Tool Executor: 读取需求
5. Bob -> LLM Service: 生成架构设计
6. Bob -> WebSocket: 更新进度
7. Bob -> Tool Executor: 写入架构文档
8. **Bob -> Mike: 汇报完成，返回架构设计** (向Mike汇报，不是Agent Manager)

#### 阶段4: Mike评估并分配开发任务
1. **Mike -> Mike: 评估Bob的架构设计** (Mike审查交付物)
2. **Mike -> LLM: 评估架构质量**
3. **Mike -> WebSocket: 更新TaskOverview(overall_progress=50)**
4. **Mike -> Agent Manager: 获取Alex实例**
5. **Mike -> Alex: 分配任务** "根据架构实现代码"
6. Alex -> WebSocket: 发送AgentMessage(status='working')
7. Alex -> Tool Executor: 读取架构文档
8. 循环: Alex生成各组件代码
   - Alex -> LLM: 生成代码
   - Alex -> WebSocket: 更新进度
   - Alex -> Tool Executor: 写入文件
9. Alex -> Tool Executor: npm install, npm build
10. **Alex -> Mike: 汇报完成，返回代码和构建结果**

#### 阶段5: Mike审查并通知用户
1. **Mike -> Mike: 审查Alex的代码** (最终质量把关)
2. **Mike -> LLM: 代码审查**
3. **Mike -> WebSocket: 更新TaskOverview(overall_progress=100)**
4. **Mike -> WebSocket: 发送完成消息给用户**
5. WebSocket -> ChatUI: 显示Mike的消息
6. ChatUI -> User: 展示完成通知

#### 阶段6: 用户预览和部署
1. 用户点击"预览" -> 渲染预览
2. 用户点击"部署"
3. **API Gateway -> Mike: 转发部署请求** (部署也通过Mike)
4. **Mike -> Alex: 分配部署任务**
5. Alex -> Tool Executor: Git push, Deploy
6. **Alex -> Mike: 汇报部署完成**
7. **Mike -> WebSocket: 发送部署成功消息**
8. WebSocket -> ChatUI: 显示部署链接

#### 阶段7: 上下文持久化
1. **Mike -> Database: 保存会话上下文**

### 5.2 关键流程说明

#### Mike的决策流程
```python
class MikeAgent:
    def process_message(self, message):
        # 1. 分析需求
        analysis = self.analyze_requirement(message)
        
        # 2. 决定执行策略
        if analysis.complexity == "simple":
            # 简单需求直接让Alex开发
            self.assign_task("Alex", task)
        elif analysis.needs_research:
            # 需要调研先让Emma分析
            self.assign_task("Emma", research_task)
        
        # 3. 监控进度
        self.monitor_team_progress()
    
    def on_agent_completed(self, agent_name, result):
        # Agent完成任务后，Mike决定下一步
        if agent_name == "Emma":
            if result.needs_architecture:
                self.assign_task("Bob", arch_task)
            else:
                self.assign_task("Alex", dev_task)
        elif agent_name == "Bob":
            # 审查架构
            review = self.review_deliverable(result)
            if review.approved:
                self.assign_task("Alex", dev_task)
            else:
                self.assign_task("Bob", revise_task)
        elif agent_name == "Alex":
            # 最终审查并通知用户
            self.review_and_notify_user(result)
```

#### Agent间通信机制
- **所有消息通过Mike**: 用户 → Mike → Agent → Mike → 用户
- **Agent向Mike汇报**: 完成任务后调用 `report_to_mike()`
- **Mike决定下一步**: 通过 `on_agent_completed()` 评估并分配新任务
- **消息持久化**: 所有决策和汇报记录到数据库

#### 工具执行流程
- Agent通过Tool Executor统一调用工具
- 工具执行结果返回给Agent
- Agent将结果整合后汇报给Mike

#### LLM调用策略
- 优先使用配置的默认模型
- 失败时自动fallback到备用模型
- **支持流式输出，通过WebSocket推送到ChatUI**
- 记录token使用量和成本

#### 实时状态同步机制
- **Agent状态变化**: Agent -> WebSocket -> ChatUI
- **任务进度更新**: TaskScheduler -> WebSocket -> ChatUI
- **流式输出**: LLM -> Agent -> WebSocket -> ChatUI
- **Mike的决策**: Mike -> WebSocket -> ChatUI

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
- **progress: float**
- **created_by: varchar(50) = "Mike"** (新增)
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
- **progress: float**
- **reported_to_mike: boolean** (新增)
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
- **所有任务由Mike创建 (created_by = "Mike")**
- **Agent执行完成后需要向Mike汇报 (reported_to_mike)**

---

## 7. UI导航路径

详见 `ui_navigation.plantuml`，主要导航流程:

### 主要页面和导航深度

#### Level 0: 入口页面
- **Home Page**: 着陆页，展示产品特性和快速开始

#### Level 1: 认证和主面板
- **Authentication**: 登录/注册页面
- **Dashboard**: 用户主控制台

#### Level 2: 核心工作区
- **Chat Workspace**: 主要工作空间
  - **布局**: [ChatUI 30%] [Editor+Preview 70%]
  - **Chat Interface (整合版)**: 对话消息流 + Agent状态 + 任务进度
  - **Editor & Preview Area**: 代码编辑 + 实时预览

- **Preview & Deploy**: 全屏预览和部署
- **Projects**: 项目管理
- **Settings**: 设置页面

### 导航原则
1. **最大深度2层**: 避免用户迷失（优化后）
2. **高频功能前置**: 聊天、预览、部署一键可达
3. **明确返回路径**: 每个页面都有清晰的返回按钮
4. **快捷导航**: 顶部导航栏始终可见
5. **状态保持**: 切换页面时保持工作状态
6. **空间优化**: ChatUI占30%，Editor+Preview占70%

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

#### 7. Mike的决策透明度
- **问题**: 如何让用户理解Mike的决策过程?
- **待决策**:
  - 是否显示Mike的思考过程?
  - 如何可视化任务分配逻辑?
  - 用户是否可以干预Mike的决策?

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

---

## 9. 总结

本系统设计文档详细描述了MGX MVP的完整技术架构，核心特点:

**架构优势**:
1. **Mike作为唯一入口**: 符合真实团队管理模式，责任链清晰
2. **模块化设计**: 各层次职责清晰，易于扩展和维护
3. **异步架构**: 高性能，支持大规模并发
4. **安全隔离**: Docker沙箱确保代码执行安全
5. **统一交互**: ChatUI整合Agent状态和任务进度，提升用户体验
6. **空间优化**: 为代码编辑和预览预留70%屏幕空间

**核心改进**:
- Mike Agent从平级成员提升为决策者和协调者
- Agent Manager从决策者降级为技术支撑层
- 所有Agent完成任务后向Mike汇报，由Mike决定下一步
- 消息流: 用户 → Mike → Team → Mike → 用户

该设计方案在满足MVP核心功能的同时，为后续迭代预留了充分的扩展空间。