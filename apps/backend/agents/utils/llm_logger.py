"""Utility helpers to persist raw agent/LLM interactions per session."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_ROOT_DIR = Path(__file__).resolve().parents[4]
_SESSION_DIR = _ROOT_DIR / 'data' / 'sessions'
_SESSION_DIR.mkdir(parents=True, exist_ok=True)

_session_locks: Dict[str, asyncio.Lock] = {}


def _get_session_lock(session_id: str) -> asyncio.Lock:
    lock = _session_locks.get(session_id)
    if lock is None:
        lock = asyncio.Lock()
        _session_locks[session_id] = lock
    return lock


def _append_entry(path: Path, entry: Dict[str, Any]) -> None:
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(existing, list):
                existing = []
        except json.JSONDecodeError:
            existing = []
    else:
        existing = []
    existing.append(entry)
    tmp_path = path.with_suffix('.tmp')
    tmp_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp_path.replace(path)


async def record_llm_interaction(
    *,
    session_id: str,
    agent: str,
    prompt: str,
    provider: str,
    raw_response: str,
    final_response: Optional[str] = None,
    interaction: str = 'act',
) -> None:
    """Persist a single agent/LLM exchange to data/sessions/{session}_llm.json."""

    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'agent': agent,
        'interaction': interaction,
        'provider': provider,
        'prompt': prompt,
        'raw_response': raw_response,
        'final_response': final_response if final_response is not None else raw_response,
    }
    file_path = _SESSION_DIR / f'{session_id}_llm.json'
    lock = _get_session_lock(session_id)
    async with lock:
        await asyncio.to_thread(_append_entry, file_path, entry)


__all__ = ['record_llm_interaction']
