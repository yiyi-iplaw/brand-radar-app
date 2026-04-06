from __future__ import annotations

import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

from .config import settings

RESULT_URL = "https://html.duckduckgo.com/html/?q={query}"

TRADEMARK_HINT_DOMAINS = [
    "uspto.gov",
    "trademarkia.com",
    "trademarkelite.com",
    "justia.com",
]


def search_public_trademark_footprint(mark: str, market: str = "us") -> tuple[int, str, bool]:
    """
    Returns tm_gap_score_fragment, note, review_needed.

    Heuristic only. Designed for lead generation, not clearance.
    """
    mark = (mark or "").strip()
    if not mark:
        return 18, "No mark extracted. Manual review needed.", True

    query = f'"{mark}" trademark {market}'
    url = RESULT_URL.format(query=urllib.parse.quote(query))
    headers = {"User-Agent": settings.user_agent}

    try:
        response = requests.get(url, headers=headers, timeout=settings.request_timeout)
        response.raise_for_status()
        html = response.text
    except Exception:
        return 16, "Public web search failed. Manual trademark review needed.", True

    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True).lower()
    domain_hits = sum(1 for d in TRADEMARK_HINT_DOMAINS if d in text)
    literal_hits = len(re.findall(re.escape(mark.lower()), text))

    if domain_hits >= 2 or literal_hits >= 8:
        return 6, "Likely existing U.S. trademark footprint found in public web results. Manual legal review recommended.", True
    if domain_hits == 1 or literal_hits >= 4:
        return 12, "Some U.S. trademark footprint signals found, but not conclusive. Manual review recommended.", True
    return 24, "No obvious U.S. trademark footprint found in public web search. Strong lead-generation signal only.", True
