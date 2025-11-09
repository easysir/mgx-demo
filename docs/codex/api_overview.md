# MGX API 概览（MVP）

当前后端实现了基础的认证、会话与聊天接口，便于前端串联“登录 → 创建会话 → 发送消息 → 获取模拟回复”的流程。所有会话/聊天接口都需要在 Header 中携带 `Authorization: Bearer <access_token>`，未登录或缺少 Token 会返回 `401 Unauthorized`。后续扩展（文件、预览、部署等）可基于此继续迭代。

## 0. Auth API

### POST `/api/auth/login`
- **描述**：使用账号/密码登录，返回短期访问 token（MVP 阶段为内存存储）。
- **请求体**：
  ```json
  {
    "email": "demo@mgx.dev",
    "password": "mgx-demo"
  }
  ```
- **响应** `200 OK`：
  ```json
  {
    "access_token": "token-user-1",
    "token_type": "bearer",
    "expires_in": 3600
  }
  ```

### GET `/api/auth/me?token=<access_token>`
- **描述**：通过 token 获取当前用户信息。
- **响应** `200 OK`：
  ```json
  {
    "id": "user-1",
    "email": "demo@mgx.dev",
    "name": "Harvey Yang",
    "credits": 1204,
    "plan": "Pro"
  }
  ```
- 若 token 无效，返回 `401`.

### POST `/api/auth/oauth/{provider}`
- **描述**：第三方登录占位接口，当前返回 `501 Not Implemented`，用于预留微信/GitHub 等方式。

## 1. Session API
> **鉴权**：需在 `Authorization` Header 中携带 `Bearer <access_token>`

### POST `/api/sessions`
- **描述**：创建新的聊天会话。
- **请求体**：
  ```json
  {
    "title": "可选的会话标题"
  }
  ```
  字段可省略，后端会自动使用 `Session <uuid>` 命名。
- **响应** `201 Created`：
  ```json
  {
    "id": "d9e9c8d4-...",
    "title": "Session d9e9c8d4",
    "created_at": "2024-11-15T02:31:20.123456",
    "messages": []
  }
  ```

### GET `/api/sessions/{session_id}`
- 返回指定会话的基础信息与当前消息列表。
- **响应** `200 OK`：与 POST 返回结构一致；若不存在则 `404`.

### GET `/api/sessions/{session_id}/messages`
- 仅返回消息数组，便于前端刷新历史。
- **响应** `200 OK`：
  ```json
  [
    {
      "id": "msg-1",
      "session_id": "d9e9c8d4-...",
      "sender": "user",
      "content": "...",
      "timestamp": "2024-11-15T02:32:01.123456",
      "agent": null
    },
    {
      "id": "msg-2",
      "sender": "status",
      "agent": "Mike",
      "content": "Mike 正在评估任务，准备调度团队。",
      "timestamp": "...",
      "session_id": "d9e9c8d4-..."
    }
  ]
  ```

## 2. Chat API
> **鉴权**：需在 `Authorization` Header 中携带 `Bearer <access_token>`

### POST `/api/chat/messages`
- **描述**：往指定会话发送用户消息，并同时返回模拟的 Agent 回复。
- **请求体**：
  ```json
  {
    "session_id": "d9e9c8d4-...",
    "content": "想要一个带深色导航的个人网站。"
  }
  ```
  - `session_id`：前一步创建的会话 ID；
  - `content`：文本，长度 1~4000。
- **响应** `201 Created`：
  ```json
  {
    "user": { ...Message },
    "responses": [
      { "sender": "status", "agent": "Mike", ... },
      { "sender": "mike", "agent": "Mike", ... },
      { "sender": "status", "agent": "Alex", ... },
      { "sender": "agent", "agent": "Alex", ... }
    ]
  }
  ```
  - 返回结构为一次 “对话回合”；
  - 便于前端直接插入用户发言与多条 Agent 状态/回复；
  - 如会话不存在，返回 `404`.

## 3. 通用说明

- **认证**：目前无鉴权，后续可在 FastAPI 层加入 JWT 中间件。
- **跨域**：`app/main.py` 已启用全量 CORS，允许浏览器直接访问。
- **数据持久化**：当前所有会话/消息存于内存 `SessionStore`，重启后会丢失；后续替换为 PostgreSQL + Redis。
- **Agent 状态消息**：`sender` 字段可能为 `status`，表示 Mike/Alex 等 Agent 的阶段性状态（例如“已接手”“流式输出中”），前端可用来渲染时间线式消息。

如需扩展新接口（文件、预览、任务等），建议保持 `/api/v1/...` 命名，并在 `docs/codex/` 下持续补充文档。
