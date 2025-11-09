"""LLM service facade that routes prompts to configured providers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

from .providers import LLMProvider, get_builtin_provider


@dataclass
class LLMConfig:
    """Environment-driven configuration for the agent LLM layer."""

    default_provider: str = os.getenv('AGENT_LLM_PROVIDER', 'openai')
    openai_model: str = os.getenv('AGENT_LLM_OPENAI_MODEL', 'gpt-4o-mini')
    anthropic_model: str = os.getenv('AGENT_LLM_ANTHROPIC_MODEL', 'claude-3-5-sonnet')
    gemini_model: str = os.getenv('AGENT_LLM_GEMINI_MODEL', 'gemini-1.5-pro')
    ollama_model: str = os.getenv('AGENT_LLM_OLLAMA_MODEL', 'llama3.1')

    openai_api_key: Optional[str] = os.getenv('OPENAI_API_KEY')
    anthropic_api_key: Optional[str] = os.getenv('ANTHROPIC_API_KEY')
    gemini_api_key: Optional[str] = os.getenv('GEMINI_API_KEY')
    ollama_api_key: Optional[str] = os.getenv('OLLAMA_API_KEY')  # 可能不需要，但保留字段


class LLMService:
    """Routes generation requests to specific providers."""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        self._providers: Dict[str, LLMProvider] = {
            'openai': get_builtin_provider('openai', model=config.openai_model, api_key=config.openai_api_key),
            'anthropic': get_builtin_provider(
                'anthropic', model=config.anthropic_model, api_key=config.anthropic_api_key
            ),
            'gemini': get_builtin_provider('gemini', model=config.gemini_model, api_key=config.gemini_api_key),
            'ollama': get_builtin_provider('ollama', model=config.ollama_model, api_key=config.ollama_api_key),
        }

    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        key = (name or self._config.default_provider).lower()
        provider = self._providers.get(key)
        if not provider:
            raise ValueError(f'LLM provider "{key}" not configured')
        return provider

    async def generate(self, *, prompt: str, provider: Optional[str] = None, **kwargs) -> str:
        """Generate text from the selected provider."""

        selected = self.get_provider(provider)
        return await selected.generate(prompt=prompt, **kwargs)


_LLM_SERVICE: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _LLM_SERVICE
    if _LLM_SERVICE is None:
        _LLM_SERVICE = LLMService(LLMConfig())
    return _LLM_SERVICE


__all__ = ['LLMConfig', 'LLMService', 'get_llm_service']
