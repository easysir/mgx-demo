"""LLM service facade that routes prompts to configured providers."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, AsyncIterator

from .providers import EchoProvider, LLMProvider, get_builtin_provider

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[LLMService] %(levelname)s %(message)s'))
    logger.addHandler(handler)
logger.propagate = False


def _load_local_env() -> None:
    """Load agents/.env so devs don't need to export vars globally."""

    env_path = Path(__file__).resolve().parent.parent / '.env'
    if not env_path.exists():
        return
    try:
        with env_path.open('r', encoding='utf-8') as handler:
            for raw_line in handler:
                line = raw_line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                os.environ.setdefault(key, value)
    except OSError as exc:
        logger.warning('Failed to load agents/.env: %s', exc)


_load_local_env()


class LLMProviderError(Exception):
    """Raised when the underlying LLM provider fails."""

    pass


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
    enable_logging: bool = True


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
        provider_name = getattr(selected, 'name', provider or self._config.default_provider)
        logger.info(
            'LLMService: invoking provider=%s model=%s prompt_len=%d',
            provider_name,
            getattr(selected, 'model', 'unknown'),
            len(prompt),
        )
        try:
            result = await selected.generate(prompt=prompt, **kwargs)
            logger.info('LLMService: provider=%s succeeded response_len=%d', provider_name, len(result))
            return result
        except Exception as exc:
            logger.exception('LLMService: provider=%s failed', provider_name, exc_info=exc)
            raise LLMProviderError(str(exc)) from exc

    async def stream_generate(
        self,
        *,
        prompt: str,
        provider: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream text chunks from the selected provider."""

        selected = self.get_provider(provider)
        provider_name = getattr(selected, 'name', provider or self._config.default_provider)
        stream_method = getattr(selected, 'stream_generate', None)
        if stream_method is None:
            logger.info('LLMService: provider=%s has no stream API, returning single chunk', provider_name)
            result = await selected.generate(prompt=prompt, **kwargs)
            yield result
            return
        logger.info('LLMService: streaming via provider=%s model=%s', provider_name, getattr(selected, 'model', 'unknown'))
        try:
            async for chunk in stream_method(prompt=prompt, **kwargs):
                yield chunk
        except Exception as exc:
            logger.exception('LLMService: streaming provider=%s failed', provider_name, exc_info=exc)
            raise LLMProviderError(str(exc)) from exc


_LLM_SERVICE: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    global _LLM_SERVICE
    if _LLM_SERVICE is None:
        _LLM_SERVICE = LLMService(LLMConfig())
    return _LLM_SERVICE


__all__ = ['LLMConfig', 'LLMService', 'get_llm_service']
