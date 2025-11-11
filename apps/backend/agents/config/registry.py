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

    def describe_agents(self, names: Iterable[AgentRole]) -> list[str]:
        descriptions: list[str] = []
        for name in names:
            meta = self._agents.get(name)
            if not meta:
                descriptions.append(name)
                continue
            descriptions.append(f"{meta.name}（{meta.title}：{meta.description}）")
        return descriptions


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
            description='专注需求澄清与产品规划，输出功能列表与优先级，不直接执行外部调研或编码。',
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
            description='唯一负责代码实现、测试与部署的工程师，可使用文件/终端等工具执行改动。',
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
            description='专职信息检索、网络搜索与资料整理，汇总可引用的外部参考，不修改代码。',
            default_tools=['search'],
        ),
    ]
)
