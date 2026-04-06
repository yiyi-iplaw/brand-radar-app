from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

import pandas as pd

from .models import Lead


class BrandRadarDB:
    def __init__(self, path: Path):
        self.path = str(path)
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _ensure_tables(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT,
                    brand_name TEXT,
                    industry TEXT,
                    total_score INTEGER,
                    growth_score INTEGER,
                    global_score INTEGER,
                    tm_gap_score INTEGER,
                    outreach_score INTEGER,
                    window_status TEXT,
                    lead_reason TEXT,
                    outreach_angle TEXT,
                    tm_note TEXT,
                    tm_review_needed INTEGER,
                    signals TEXT,
                    source_urls TEXT,
                    outreach_draft TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(company_name, brand_name)
                )
                """
            )
            conn.commit()

    def upsert_scan_results(self, leads: Iterable[Lead]) -> None:
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO leads (
                    company_name, brand_name, industry, total_score, growth_score,
                    global_score, tm_gap_score, outreach_score, window_status,
                    lead_reason, outreach_angle, tm_note, tm_review_needed,
                    signals, source_urls, outreach_draft
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(company_name, brand_name)
                DO UPDATE SET
                    industry=excluded.industry,
                    total_score=excluded.total_score,
                    growth_score=excluded.growth_score,
                    global_score=excluded.global_score,
                    tm_gap_score=excluded.tm_gap_score,
                    outreach_score=excluded.outreach_score,
                    window_status=excluded.window_status,
                    lead_reason=excluded.lead_reason,
                    outreach_angle=excluded.outreach_angle,
                    tm_note=excluded.tm_note,
                    tm_review_needed=excluded.tm_review_needed,
                    signals=excluded.signals,
                    source_urls=excluded.source_urls,
                    outreach_draft=excluded.outreach_draft,
                    created_at=CURRENT_TIMESTAMP
                """,
                [
                    (
                        lead.company_name,
                        lead.brand_name,
                        lead.industry,
                        lead.total_score,
                        lead.growth_score,
                        lead.global_score,
                        lead.tm_gap_score,
                        lead.outreach_score,
                        lead.window_status,
                        lead.lead_reason,
                        lead.outreach_angle,
                        lead.tm_note,
                        lead.tm_review_needed,
                        lead.signals,
                        lead.source_urls,
                        lead.outreach_draft,
                    )
                    for lead in leads
                ],
            )
            conn.commit()

    def get_leads(self) -> pd.DataFrame:
        with self._connect() as conn:
            df = pd.read_sql_query("SELECT * FROM leads ORDER BY total_score DESC, created_at DESC", conn)
        return df
