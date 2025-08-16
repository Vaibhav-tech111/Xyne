# services/ddg_service.py

import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

DDG_URL = "https://api.duckduckgo.com/"  # ✅ Fixed - No trailing space

def search(
    query: str,
    max_results: int = 5,
    safe: bool = True,
    region: Optional[str] = None
) -> List[Dict[str, str]]:
    """
    Query DuckDuckGo Instant Answer API.
    Returns list of dicts: {title, snippet, url}
    """
    params = {
        "q": query,
        "format": "json",
        "no_html": 1,
        "skip_disambig": 1,
        "safe": "on" if safe else "off",
        "region": region or "wt-wt"
    }

    try:
        r = requests.get(DDG_URL, params=params, timeout=8)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        logger.warning(f"[DDG] Request error: {e}")
        return []
    except Exception as e:
        logger.warning(f"[DDG] Unexpected error: {e}")
        return []

    results = []

    # 1. Abstract / Instant Answer
    abstract = data.get("Abstract", "")
    if abstract:
        results.append({
            "title": data.get("Heading", query),
            "snippet": abstract,
            "url": data.get("AbstractURL", "")
        })

    # 2. Related Topics
    for item in data.get("RelatedTopics", []):
        if isinstance(item, dict) and item.get("FirstURL") and item.get("Text"):
            text = item["Text"]
            results.append({
                "title": text.split(" - ")[0] if " - " in text else text[:60],
                "snippet": text,
                "url": item["FirstURL"]
            })

    # 3. Deduplicate by URL
    seen, unique = set(), []
    for item in results:
        url = item["url"]
        if url and url not in seen:
            seen.add(url)
            unique.append(item)

    return unique[:max_results]
