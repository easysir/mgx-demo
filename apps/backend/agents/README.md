# Agents Runtime

该目录承载 MGX 智能体运行时，负责 Mike 团队的编排、工具调用与未来 LLM 集成。当前仍与 FastAPI 网关 (`app/`) 同进程运行，但已经按照“可随时拆分为独立服务”的思路设计。

## 架构概览

```
agents/
├── config/           # Agent 注册表与元数据
├── agents/           # 具体 Agent 实现（Mike/Emma/Bob/...）
├── prompts/          # 提示词模板
├── tools/            # ToolExecutor 及工具适配层
├── llm/              # LLM Service + Provider 适配
├── workflows/        # Mike 指挥团队的编排策略
└── runtime/          # Orchestrator，对外暴露统一入口
```

### 核心流程
1. FastAPI 网关接收用户消息，调用 `AgentRuntimeGateway`。
2. Gateway 创建 `WorkflowContext` 并调用 `AgentExecutor.handle_user_turn`。
3. Orchestrator 基于 `config/registry.py` 中的注册信息与 `workflows/` 策略生成一组 `AgentDispatch`。
4. Gateway 将 dispatch 结果写入会话存储，再通过 WebSocket/API 回传给前端。

### 亮点
- **配置驱动的 Agent Registry**：`config/registry.py` 定义 Agent 元数据（名称、描述、默认工具），可按需启用/禁用，为后续扩编或精简团队提供开关。
- **Workflow + Orchestrator 解耦**：编排策略集中在 `workflows/`，Orchestrator 只负责调度，便于后续替换为 DAG、状态机或事件驱动模型。
- **ToolExecutor 抽象**：所有 LLM/编辑器/终端/Git 等操作通过 `tools/` 统一封装，Agent 本身只决定“用哪个工具”，降低耦合。
- **LLM 接入层**：`llm/service.py` 通过环境变量配置 OpenAI/Anthropic/Gemini/Ollama 等主流模型，现阶段用 EchoProvider 返回可观测结果，方便后续替换为真实 SDK。
- **Shared 契约**：`shared/types.py` 暴露 `AgentRole`/`SenderRole` 等常量，Gateway 与 Agents 同源引用，为未来拆成独立微服务奠定基础。
- **明确的 TODO**：`AgentRuntimeGateway` 和 orchestrator 顶部都写明“可拆分为 RPC/消息队列”的规划，提示后续迁移路径。

## TODO
- 接入真实 LLM & 工具，并将 `agents/agents/` 中的占位逻辑替换为生产实现。
- 在 Phase 2 引入 Redis/DB 做队列与状态持久化，再考虑将 `agents/` 打包为独立服务，通过 RPC/消息队列与 FastAPI 网关通信。
