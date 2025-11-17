from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, TYPE_CHECKING

from shared.types import AgentRole, SenderRole

if TYPE_CHECKING:  # pragma: no cover
    from app.models import Message


StreamPublisher = Callable[[Dict[str, Any]], Awaitable[None]]
PersistFn = Callable[[SenderRole, Optional[AgentRole], str, Optional[str], Optional[datetime]], 'Message']


class StreamContext:
    """Holds streaming state (publisher + persistence callback) for a session."""

    def __init__(
        self,
        *,
        session_id: str,
        owner_id: str,
        publisher: Optional[StreamPublisher],
        persist_fn: Optional[PersistFn] = None,
    ) -> None:
        # 保存 session 基本信息，方便 debug 或扩展
        self.session_id = session_id
        self.owner_id = owner_id
        self.publisher = publisher
        self._persist_fn = persist_fn  # 统一的落库回调
        self._persisted: List['Message'] = []  # 已经写入的消息缓存，供调用方返回

    def record_message(
        self,
        *,
        sender: SenderRole,
        agent: Optional[AgentRole],
        content: str,
        message_id: Optional[str],
        timestamp: Optional[str] = None,
    ) -> 'Message':
        # 将单条事件写入存储；若 persist_fn 缺失则视为配置错误
        if not self._persist_fn:
            raise RuntimeError('StreamContext missing persist_fn')
        parsed = _parse_timestamp(timestamp)
        message = self._persist_fn(sender, agent, content, message_id, parsed)
        self._persisted.append(message)
        return message

    def persisted_messages(self) -> List['Message']:
        return list(self._persisted)


_stream_context: ContextVar[Optional[StreamContext]] = ContextVar('stream_context', default=None)


def push_stream_context(context: StreamContext) -> object:
    # 入栈当前上下文，返回 token 便于出栈
    return _stream_context.set(context)


def pop_stream_context(token: object) -> None:
    # 根据 token 恢复上一个上下文
    _stream_context.reset(token)


def current_stream_context() -> Optional[StreamContext]:
    # 获取当前协程可见的上下文
    return _stream_context.get()


def _parse_timestamp(value: Optional[str]) -> datetime:
    if value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.utcnow()
