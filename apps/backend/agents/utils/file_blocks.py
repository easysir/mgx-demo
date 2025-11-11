from __future__ import annotations

from typing import Dict, List

FILE_FENCE_START = "```file:"
FILE_FENCE_END = "```endfile"


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
            next_start = text.find(FILE_FENCE_START, body_start)
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
