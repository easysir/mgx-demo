from __future__ import annotations

import html
import re
from typing import Any, Dict, List
from urllib.parse import urlencode

import httpx

from ..executor import Tool, ToolExecutionError


def _clean_html(raw: str) -> str:
    cleaned = re.sub(r'<[^>]+>', '', raw)
    return html.unescape(cleaned).strip()


class WebSearchTool(Tool):
    name = 'web_search'
    description = '使用 DuckDuckGo 执行网络查询，返回带标题/摘要/链接的外部资讯，方便做实时信息收集。'

    async def run(self, *, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get('query')
        if not query:
            raise ToolExecutionError('web_search 需要 "query" 参数')
        try:
            max_results = int(params.get('max_results', 3))
        except (TypeError, ValueError):
            max_results = 3
        max_results = max(1, min(max_results, 5))

        url = f'https://duckduckgo.com/html/?{urlencode({"q": query})}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; MGX-Agent/1.0; +https://example.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise ToolExecutionError(f'web_search 请求失败: {exc.response.status_code}') from exc

        html_body = response.text
        blocks = html_body.split('<div class="result__body">')
        results: List[Dict[str, str]] = []
        for block in blocks[1:]:
            if len(results) >= max_results:
                break
            link_match = re.search(
                r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
                block,
                re.S,
            )
            if not link_match:
                continue
            snippet_match = re.search(
                r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(?P<snippet>.*?)</a>',
                block,
                re.S,
            )
            title = _clean_html(link_match.group('title'))
            snippet = _clean_html(snippet_match.group('snippet')) if snippet_match else ''
            href = link_match.group('href')

            results.append({'title': title or '（无标题）', 'snippet': snippet, 'url': href})

        if not results:
            raise ToolExecutionError('web_search 未能找到任何搜索结果')

        return {
            'query': query,
            'results': results,
        }
