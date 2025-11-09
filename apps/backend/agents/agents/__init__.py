"""Agent implementations.

Each agent inherits from :class:`BaseAgent` and can access shared tool executors.
Real LLM/tool logic will live here; for now we provide placeholders to clarify
responsibilities.
"""

from .base import BaseAgent
from .team import AGENT_CLASS_MAP

__all__ = ['BaseAgent', 'AGENT_CLASS_MAP']
