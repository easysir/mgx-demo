"""Agent registry metadata to support dynamic enable/disable and tool configs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional

from shared.types import AgentRole


@dataclass(frozen=True)
class AgentMetadata:
    name: AgentRole
    title: str
    description: str
    enabled: bool = True
    default_tools: list[str] = field(default_factory=list)


class AgentRegistry:
    """Simple in-memory registry that can later be backed by DB/config service."""

    def __init__(self, agents: Iterable[AgentMetadata]) -> None:
        self._agents: Dict[AgentRole, AgentMetadata] = {agent.name: agent for agent in agents}

    def get(self, name: AgentRole) -> Optional[AgentMetadata]:
        return self._agents.get(name)

    def is_enabled(self, name: AgentRole) -> bool:
        meta = self._agents.get(name)
        return bool(meta and meta.enabled)

    def list_enabled(self) -> list[AgentMetadata]:
        return [agent for agent in self._agents.values() if agent.enabled]


default_registry = AgentRegistry(
    [
        AgentMetadata(
            name='Mike',
            title='Team Lead',
            description='负责需求分析、任务规划与质量把关，并向用户同步结果。',
            default_tools=['planning', 'status-broadcast'],
        ),
        AgentMetadata(
            name='Emma',
            title='Product Manager',
            description='做需求澄清，输出功能列表与优先级，辅助Mike决策。',
            default_tools=['analysis'],
        ),
        AgentMetadata(
            name='Bob',
            title='Architect',
            description='制定系统架构与技术方案，评估技术风险。',
            default_tools=['design', 'diagram'],
        ),
        AgentMetadata(
            name='Alex',
            title='Engineer',
            description='负责代码实现、测试与部署。',
            default_tools=['editor', 'terminal', 'git'],
        ),
        AgentMetadata(
            name='David',
            title='Data Analyst',
            description='提供数据分析、可视化与基础机器学习支持。',
            default_tools=['notebook'],
        ),
        AgentMetadata(
            name='Iris',
            title='Researcher',
            description='执行信息检索和资料整理，提供外部参考。',
            default_tools=['search'],
        ),
    ]
)
