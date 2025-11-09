"""Common literal types shared between the FastAPI gateway and agent runtime."""

from typing import Literal

# Agent personas supported in Phase 1.
AgentRole = Literal['Mike', 'Emma', 'Bob', 'Alex', 'David', 'Iris']

# Message senders that the frontend understands.
SenderRole = Literal['user', 'mike', 'agent', 'status']

__all__ = ['AgentRole', 'SenderRole']
