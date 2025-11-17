from __future__ import annotations

from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Iterable, Optional
from uuid import uuid4

from shared.types import AgentRole, SenderRole

from .context import current_stream_context


EventPayload = Dict[str, Any]  # 统一的 WebSocket 事件 payload 结构
StreamPublisher = Callable[[Dict[str, Any]], Awaitable[None]]


def _message_id(value: Optional[str]) -> str:
    # 若调用方未传 message_id，这里生成一个新的 UUID
    return value or str(uuid4())


def _resolve_publisher(explicit: Optional[StreamPublisher]) -> Optional[StreamPublisher]:
    # 优先使用调用方显式传入的 publisher，否则回退到当前上下文
    if explicit:
        return explicit
    ctx = current_stream_context()
    return ctx.publisher if ctx else None


def _ensure_timestamp(timestamp: Optional[str]) -> str:
    if timestamp:
        try:
            datetime.fromisoformat(timestamp)
            return timestamp
        except ValueError:
            pass
    return datetime.utcnow().isoformat()


async def publish_event(event: EventPayload, publisher: Optional[StreamPublisher] = None) -> None:
    # 最底层的发送函数：publisher 可能为空（例如未开启流式）
    resolved = _resolve_publisher(publisher)
    if not resolved:
        return
    await resolved(event)


async def publish_token(
    *,
    sender: SenderRole,
    agent: Optional[AgentRole],
    content: str,
    message_id: str,
    final: bool,
    publisher: Optional[StreamPublisher] = None,
    persist_final: bool = False,
    timestamp: Optional[str] = None,
) -> None:
    # token 事件：供 LLM 流式输出复用
    ts = _ensure_timestamp(timestamp)
    ctx = current_stream_context()
    if final and persist_final and ctx:
        ctx.record_message(
            sender=sender,
            agent=agent,
            content=content,
            message_id=message_id,
            timestamp=ts,
        )
    await publish_event(
        token_event(
            sender=sender,
            agent=agent,
            content=content,
            message_id=message_id,
            final=final,
            timestamp=ts,
        ),
        publisher,
    )


async def publish_status(
    *,
    content: str,
    agent: Optional[AgentRole | str] = None,
    message_id: Optional[str] = None,
    publisher: Optional[StreamPublisher] = None,
    timestamp: Optional[str] = None,
    persist: bool = True,
) -> str:
    # 状态提示：默认由 Mike 或具体 agent 发送
    resolved_id = _message_id(message_id)
    ts = _ensure_timestamp(timestamp)
    ctx = current_stream_context()
    if persist and ctx:
        ctx.record_message(
            sender='status',
            agent=agent,  # type: ignore[arg-type]
            content=content,
            message_id=resolved_id,
            timestamp=ts,
        )
    await publish_event(
        status_event(
            content=content,
            agent=agent,
            message_id=resolved_id,
            timestamp=ts,
        ),
        publisher,
    )
    return resolved_id


async def publish_error(
    *,
    content: str,
    agent: Optional[AgentRole | str],
    message_id: Optional[str] = None,
    publisher: Optional[StreamPublisher] = None,
    timestamp: Optional[str] = None,
    persist: bool = True,
) -> str:
    # 异常提示：展示在聊天区域，供用户知晓失败原因
    resolved_id = _message_id(message_id)
    ts = _ensure_timestamp(timestamp)
    ctx = current_stream_context()
    if persist and ctx:
        ctx.record_message(
            sender='status',
            agent=agent,  # type: ignore[arg-type]
            content=content,
            message_id=resolved_id,
            timestamp=ts,
        )
    await publish_event(
        error_event(
            content=content,
            agent=agent,
            message_id=resolved_id,
            timestamp=ts,
        ),
        publisher,
    )
    return resolved_id


async def publish_tool_call(
    *,
    tool: str,
    content: str,
    invoker: str,
    agent: Optional[AgentRole],
    message_id: Optional[str] = None,
    timestamp: Optional[str] = None,
    publisher: Optional[StreamPublisher] = None,
    persist: bool = True,
) -> str:
    # 工具调用事件：带上工具名、调用者与时间戳
    resolved_id = _message_id(message_id)
    ts = _ensure_timestamp(timestamp)
    ctx = current_stream_context()
    if persist and ctx:
        ctx.record_message(
            sender='agent',
            agent=agent,
            content=content,
            message_id=resolved_id,
            timestamp=ts,
        )
    await publish_event(
        tool_call_event(
            tool=tool,
            content=content,
            invoker=invoker,
            agent=agent,
            message_id=resolved_id,
            timestamp=ts,
        ),
        publisher,
    )
    return resolved_id


def token_event(
    *,
    sender: SenderRole,
    agent: Optional[AgentRole],
    content: str,
    message_id: str,
    final: bool,
    timestamp: Optional[str] = None,
) -> EventPayload:
    # token 类型在前端代表流式消息（final 控制是否落入历史）
    event: EventPayload = {
        'type': 'token',
        'sender': sender,
        'agent': agent,
        'content': content,
        'message_id': message_id,
        'final': final,
    }
    if timestamp:
        event['timestamp'] = timestamp
    return event


def status_event(
    *,
    content: str,
    # status 类型用于展示阶段进度或 shell 执行日志
    agent: Optional[AgentRole | str],
    message_id: str,
    timestamp: Optional[str] = None,
) -> EventPayload:
    event: EventPayload = {
        'type': 'status',
        'sender': 'status',
        'agent': agent,
        'content': content,
        'message_id': message_id,
        'final': True,
    }
    if timestamp:
        event['timestamp'] = timestamp
    return event


def error_event(
    *,
    content: str,
    agent: Optional[AgentRole | str],
    message_id: str,
    timestamp: Optional[str] = None,
) -> EventPayload:
    # error 类型提示不可恢复的失败，sender 统一标记为 status
    event: EventPayload = {
        'type': 'error',
        'sender': 'status',
        'agent': agent,
        'content': content,
        'message_id': message_id,
        'final': True,
    }
    if timestamp:
        event['timestamp'] = timestamp
    return event


def message_event(
    *,
    sender: SenderRole,
    agent: Optional[AgentRole],
    content: str,
    message_id: str,
    timestamp: Optional[str] = None,
) -> EventPayload:
    # message 类型用于用户输入或其它需要立即展示的普通消息
    event: EventPayload = {
        'type': 'message',
        'sender': sender,
        'agent': agent,
        'content': content,
        'message_id': message_id,
        'final': True,
    }
    if timestamp:
        event['timestamp'] = timestamp
    return event


def tool_call_event(
    *,
    tool: str,
    content: str,
    invoker: str,
    agent: Optional[AgentRole],
    message_id: str,
    timestamp: Optional[str] = None,
) -> EventPayload:
    # tool_call 类型作为“系统消息”展示工具调用摘要
    event: EventPayload = {
        'type': 'tool_call',
        'sender': 'agent',
        'agent': agent,
        'invoker': invoker,
        'tool': tool,
        'content': content,
        'message_id': message_id,
        'final': True,
    }
    if timestamp:
        event['timestamp'] = timestamp
    return event


def file_change_event(paths: Iterable[str]) -> EventPayload:
    # 文件变更事件不落库，只用于触发前端刷新文件树
    return {'type': 'file_change', 'paths': list(paths)}
