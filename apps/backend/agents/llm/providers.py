"""LLM provider definitions and simple placeholder implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


class LLMProvider:
    """Minimal provider interface that concrete clients must implement."""

    name: str
    model: str

    async def generate(self, *, prompt: str, **kwargs: Any) -> str:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass
class EchoProvider(LLMProvider):
    """Placeholder provider that simply echoes the prompt with provider info."""

    name: str
    model: str
    api_key: str | None = None

    async def generate(self, *, prompt: str, **kwargs: Any) -> str:
        if not self.api_key:
            return f"[{self.name}:{self.model}] API key 未配置，返回占位响应：{prompt}"
        return f"[{self.name}:{self.model}] {prompt}"


def get_builtin_provider(provider_name: str, *, model: str, api_key: str | None) -> LLMProvider:
    """Factory returning a placeholder provider for the given name."""

    normalized = provider_name.lower()
    if normalized in {'openai', 'anthropic', 'gemini', 'ollama'}:
        return EchoProvider(name=provider_name.capitalize(), model=model, api_key=api_key)
    raise ValueError(f'Unsupported provider: {provider_name}')


__all__ = ['LLMProvider', 'EchoProvider', 'get_builtin_provider']
