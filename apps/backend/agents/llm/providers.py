"""LLM provider definitions and simple placeholder implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, AsyncIterator

from openai import AsyncOpenAI, OpenAIError


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


@dataclass
class OpenAIProvider(LLMProvider):
    """Async OpenAI provider using the official SDK."""

    name: str = 'OpenAI'
    model: str = 'gpt-4o-mini'
    api_key: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError('OpenAI API key is required for OpenAIProvider')
        self._client = AsyncOpenAI(api_key=self.api_key)

    async def generate(self, *, prompt: str, **kwargs: Any) -> str:
        try:
            temperature = kwargs.get('temperature', 0.3)
            completion = await self._client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=temperature,
            )
            content = completion.choices[0].message.content
            if isinstance(content, list):
                return ''.join(
                    part.get('text', '') if isinstance(part, dict) else str(part) for part in content
                )
            return content or ''
        except OpenAIError as exc:
            raise RuntimeError(f'OpenAI API error: {exc}') from exc

    async def stream_generate(self, *, prompt: str, **kwargs: Any) -> AsyncIterator[str]:
        try:
            temperature = kwargs.get('temperature', 0.3)
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=temperature,
                stream=True,
            )
            async for chunk in stream:
                choice = chunk.choices[0]
                delta = choice.delta.content
                if not delta:
                    continue
                if isinstance(delta, list):
                    text = ''.join(
                        part.get('text', '') if isinstance(part, dict) else str(part) for part in delta
                    )
                else:
                    text = delta
                if text:
                    yield text
        except OpenAIError as exc:
            raise RuntimeError(f'OpenAI API error: {exc}') from exc


def get_builtin_provider(provider_name: str, *, model: str, api_key: str | None) -> LLMProvider:
    """Factory returning a placeholder provider for the given name."""

    normalized = provider_name.lower()
    if normalized == 'openai':
        if api_key:
            return OpenAIProvider(model=model, api_key=api_key)
        return EchoProvider(name='OpenAI', model=model, api_key=api_key)
    if normalized in {'anthropic', 'gemini', 'ollama'}:
        return EchoProvider(name=provider_name.capitalize(), model=model, api_key=api_key)
    raise ValueError(f'Unsupported provider: {provider_name}')


__all__ = ['LLMProvider', 'EchoProvider', 'OpenAIProvider', 'get_builtin_provider']
