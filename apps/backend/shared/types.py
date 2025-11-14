"""提供 FastAPI 网关与 Agent 运行时共享的枚举 literal。"""

from typing import Literal

# 阶段一内置的代理人格列表。
AgentRole = Literal['Mike', 'Emma', 'Bob', 'Alex', 'David', 'Iris']

# TODO(后续优化): 当前 SenderRole 粒度偏抽象，需结合业务与前端展示重新梳理枚举。
# 前端识别的消息发送方角色。
SenderRole = Literal['user', 'mike', 'agent', 'status']

__all__ = ['AgentRole', 'SenderRole']
