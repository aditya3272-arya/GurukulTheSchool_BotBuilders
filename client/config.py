from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class ClientConfig:
    api_base_url: str = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
    http_connect_timeout: float = float(os.getenv("CORTEXIA_HTTP_CONNECT_TIMEOUT", "15"))
    http_read_timeout: float = float(os.getenv("CORTEXIA_HTTP_READ_TIMEOUT", "90"))
    formspree_endpoint: str = os.getenv("FORMSPREE_ENDPOINT", "https://formspree.io/f/YOUR_FORM_ID")
    formspree_query_endpoint: str = os.getenv("FORMSPREE_QUERY_ENDPOINT", "https://formspree.io/f/YOUR_QUERY_FORM_ID")
    splash_delay_ms: int = int(os.getenv("CORTEXIA_SPLASH_DELAY_MS", "2300"))
    dashboard_loader_delay_ms: int = int(os.getenv("CORTEXIA_DASHBOARD_LOADER_DELAY_MS", "1800"))
    school_name: str = os.getenv("SCHOOL_NAME", "Your School")
