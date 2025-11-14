from __future__ import annotations

from typing import Dict, List

FILE_FENCE_START = "```file:"
FILE_FENCE_END = "```endfile"
FILE_FENCE_ALT_END = "```"


def extract_file_blocks(text: str) -> List[Dict[str, str]]:
    specs: List[Dict[str, str]] = []
    index = 0
    length = len(text)
    while index < length:
        start = text.find(FILE_FENCE_START, index)
        if start == -1:
            break
        header_end = text.find('\n', start)
        if header_end == -1:
            break
        header = text[start + len(FILE_FENCE_START):header_end].strip()
        body_start = header_end + 1
        end = text.find(FILE_FENCE_END, body_start)
        if end == -1:
            alt_end = text.find(FILE_FENCE_ALT_END, body_start)
            next_start = text.find(FILE_FENCE_START, body_start)
            candidates = [pos for pos in [alt_end, next_start] if pos != -1]
            if candidates:
                cutoff = min(candidates)
                body = text[body_start:cutoff]
                index = cutoff if cutoff == next_start else cutoff + len(FILE_FENCE_ALT_END)
            else:
                body = text[body_start:]
                index = length
        else:
            body = text[body_start:end]
            newline_after = text.find('\n', end)
            if newline_after == -1:
                index = end + len(FILE_FENCE_END)
            else:
                index = newline_after + 1
        if not header:
            continue
        segments = header.split()
        path = segments[0]
        mode = 'overwrite'
        for token in segments[1:]:
            token_lower = token.lower()
            if token_lower in {'append', 'overwrite'}:
                mode = token_lower
        specs.append({'path': path, 'mode': mode, 'content': body.strip()})
    return specs
