from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path(os.getenv("BRAND_RADAR_DB_PATH", "brand_radar.db"))
    request_timeout: int = int(os.getenv("BRAND_RADAR_REQUEST_TIMEOUT", "15"))
    default_market: str = os.getenv("BRAND_RADAR_DEFAULT_MARKETS", "us")
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )


settings = Settings()
