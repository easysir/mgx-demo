"""Agent implementations."""

from .base import AgentContext, BaseAgent
from .roles.alex import AlexAgent
from .roles.bob import BobAgent
from .roles.david import DavidAgent
from .roles.emma import EmmaAgent
from .roles.iris import IrisAgent
from .roles.mike import MikeAgent

AGENT_CLASS_MAP = {
    'Mike': MikeAgent,
    'Emma': EmmaAgent,
    'Bob': BobAgent,
    'Alex': AlexAgent,
    'David': DavidAgent,
    'Iris': IrisAgent,
}

__all__ = [
    'AgentContext',
    'BaseAgent',
    'AlexAgent',
    'BobAgent',
    'DavidAgent',
    'EmmaAgent',
    'IrisAgent',
    'MikeAgent',
    'AGENT_CLASS_MAP',
]
