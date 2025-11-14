# Backend API Overview

所有 REST 接口默认挂载在 `/api/v1`，除登录外均需要在 `Authorization: Bearer <token>` 头中携带登录返回的 `access_token`。WebSocket 入口为 `/api/ws`.

## Authentication

| Method | Path | Description | Auth |
| --- | --- | --- | --- |
| `POST` | `/auth/login` | 使用邮箱/密码登录，返回 `TokenResponse(access_token, token_type)` | 否 |
| `GET` | `/auth/me?token=<token>` | 用于调试/自检，返回用户 `UserProfile` | 否（通过 query 提供 token） |

## Sessions

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/sessions` | 列出当前用户的所有会话（最近创建的在前） |
| `POST` | `/sessions` | 创建新会话；可携带 `SessionCreate` 指定标题 |
| `GET` | `/sessions/{session_id}` | 获取单个会话元数据 |
| `GET` | `/sessions/{session_id}/messages` | 拉取该会话的完整消息历史 |
| `DELETE` | `/sessions/{session_id}` | 删除会话，同时销毁沙箱、停止文件 watcher |

## Chat

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/chat/messages` | 发送用户消息，触发 Agent workflow。请求体为 `MessageCreate(session_id, content)`，响应为 `ChatTurn { user, responses[] }` |
| `GET` | `/chat/messages/{session_id}` | 仅拉取消息（与 `/sessions/{id}/messages` 一致，前端保留兼容） |

## Files

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/files/{session_id}/tree` | 浏览沙箱文件树（可传 `root`、`depth`、`include_hidden`） |
| `GET` | `/files/{session_id}?path=...` | 读取指定文件内容 |

## Sandbox Management

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/sandbox/launch` | 启动沙箱容器；可复用既有 `session_id` 或创建新会话 |
| `POST` | `/sandbox/destroy` | 销毁单个会话的沙箱容器 |
| `POST` | `/sandbox/destroy_all` | 销毁当前用户名下所有沙箱容器 |
| `POST` | `/sandbox/exec` | 在沙箱中执行命令（`command`, `cwd`, `env`, `timeout`） |
| `GET` | `/sandbox/preview/{session_id}` | 查询允许的预览端口映射，返回可访问的 URL 列表 |

## WebSocket Stream

| Method | Path | Description |
| --- | --- | --- |
| `WS` | `/ws/sessions/{session_id}` | 房间广播通道，推送 `message`/`status`/`tool_call`/`file_change` 等事件。客户端需在连接前完成登录并复用同一 token（由前端负责添加 Cookie/头部）。 |

## 事件说明

- `message`: 用户或 Agent 输出（`sender`, `agent`, `content`, `message_id`, `timestamp`, `final`）
- `status`: 工作流状态更新（通常由 Mike 发起）
- `tool_call`: 工具执行日志（来自 `_handle_tool_call_event`）
- `file_change`: 沙箱文件变更（write/append 之后触发）

以上端点涵盖了当前后台的主要能力；若扩展新的工具或微服务，请在 `docs/api/backend.md` 按上述格式补充。***
