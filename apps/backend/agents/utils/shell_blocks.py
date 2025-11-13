from __future__ import annotations

from typing import Dict, List

SHELL_FENCE_START = "```shell"
SHELL_FENCE_END = "```endshell"


def extract_shell_blocks(text: str) -> List[Dict[str, object]]:
    specs: List[Dict[str, object]] = []
    index = 0
    length = len(text)
    while index < length:
        start = text.find(SHELL_FENCE_START, index)
        if start == -1:
            break
        header_end = text.find('\n', start)
        if header_end == -1:
            break
        header = text[start + len(SHELL_FENCE_START):header_end].strip()
        body_start = header_end + 1
        end = text.find(SHELL_FENCE_END, body_start)
        if end == -1:
            next_start = text.find(SHELL_FENCE_START, body_start)
            if next_start == -1:
                body = text[body_start:]
                index = length
            else:
                body = text[body_start:next_start]
                index = next_start
        else:
            body = text[body_start:end]
            newline_after = text.find('\n', end)
            if newline_after == -1:
                index = end + len(SHELL_FENCE_END)
            else:
                index = newline_after + 1
        command = body.strip()
        if not command:
            continue
        metadata = _parse_shell_header(header)
        metadata['command'] = command
        specs.append(metadata)
    return specs


def _parse_shell_header(header: str) -> Dict[str, object]:
    cwd: str | None = None
    timeout: int | None = None
    env: Dict[str, str] = {}
    if header:
        tokens = header.split()
        for token in tokens:
            if token.startswith("cwd="):
                cwd_value = token.split("=", 1)[1].strip()
                cwd = cwd_value or None
            elif token.startswith("timeout="):
                value = token.split("=", 1)[1].strip()
                try:
                    parsed = int(value)
                    if parsed > 0:
                        timeout = parsed
                except ValueError:
                    continue
            elif token.startswith("env:"):
                pair = token[4:].strip()
                if not pair or "=" not in pair:
                    continue
                key, val = pair.split("=", 1)
                key = key.strip()
                if not key:
                    continue
                env[key] = val.strip()
    return {
        'cwd': cwd,
        'timeout': timeout,
        'env': env,
    }


__all__ = ["extract_shell_blocks"]
