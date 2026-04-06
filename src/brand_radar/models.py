from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ScanRequest:
    queries: list[str]
    lookback_days: int = 90
    accel_days: int = 30
    max_results_per_query: int = 30
    market: str = "us"


@dataclass
class Article:
    query: str
    title: str
    link: str
    published: datetime | None
    summary: str
    source: str = ""


@dataclass
class Lead:
    company_name: str
    brand_name: str
    industry: str
    total_score: int
    growth_score: int
    global_score: int
    tm_gap_score: int
    outreach_score: int
    window_status: str
    lead_reason: str
    outreach_angle: str
    tm_note: str
    tm_review_needed: int
    signals: str
    source_urls: str
    outreach_draft: str
    created_at: datetime = field(default_factory=datetime.utcnow)
