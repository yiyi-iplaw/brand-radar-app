from __future__ import annotations

import urllib.parse
from typing import Iterable

import feedparser
import requests

from .config import settings
from .models import Article, ScanRequest
from .utils import normalize_space, parse_datetime, within_days


GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=zh-CN&gl=CN&ceid=CN:zh-Hans"


def fetch_google_news_rss(query: str) -> list[Article]:
    url = GOOGLE_NEWS_RSS.format(query=urllib.parse.quote(query))
    headers = {"User-Agent": settings.user_agent}
    response = requests.get(url, headers=headers, timeout=settings.request_timeout)
    response.raise_for_status()
    parsed = feedparser.parse(response.text)

    items: list[Article] = []
    for entry in parsed.entries:
        source = ""
        if getattr(entry, "source", None):
            source = getattr(entry.source, "title", "")
        items.append(
            Article(
                query=query,
                title=normalize_space(getattr(entry, "title", "")),
                link=getattr(entry, "link", ""),
                published=parse_datetime(getattr(entry, "published", None)),
                summary=normalize_space(getattr(entry, "summary", "")),
                source=source,
            )
        )
    return items


def scan_queries(req: ScanRequest) -> list[Article]:
    seen: set[str] = set()
    results: list[Article] = []
    for query in req.queries:
        try:
            items = fetch_google_news_rss(query)[: req.max_results_per_query]
        except Exception:
            continue
        for item in items:
            if not item.link or item.link in seen:
                continue
            if item.published and not within_days(item.published, req.lookback_days):
                continue
            seen.add(item.link)
            results.append(item)
    return results
