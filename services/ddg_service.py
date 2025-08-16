# services/ddg_service.py
from typing import List, Dict
from contextlib import suppress

try:
    from duckduckgo_search import DDGS
except Exception as e:
    raise RuntimeError("duckduckgo-search is not installed or failed to import") from e


def _normalize(item: Dict) -> Dict[str, str]:
    # Different versions use different keys: title/body/href vs. title/snippet/link
    title = item.get("title") or item.get("heading") or ""
    snippet = item.get("body") or item.get("snippet") or item.get("abstract") or ""
    link = item.get("href") or item.get("link") or item.get("url") or ""
    return {"title": title, "snippet": snippet, "link": link}


def search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    with DDGS(timeout=10) as ddgs:
        gen = None

        # Newer signature (>=4.x): text(query, region=..., safesearch=..., timelimit=None, max_results=5)
        with suppress(TypeError):
            gen = ddgs.text(
                query,
                region="wt-wt",
                safesearch="moderate",
                timelimit=None,
                max_results=max_results,
            )

        # Older signature (~3.9.x): text(query, k=5)
        if gen is None:
            with suppress(TypeError):
                gen = ddgs.text(query, k=max_results)

        # Fallback: try positional max_results
        if gen is None:
            gen = ddgs.text(query, max_results)  # noqa: E999 (older libs accept this)

        for item in gen:
            results.append(_normalize(item))
            if len(results) >= max_results:
                break

    return results
