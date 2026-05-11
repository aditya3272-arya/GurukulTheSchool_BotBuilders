from __future__ import annotations

from httpx import Timeout
from supabase import Client, ClientOptions, create_client

from app.core.config import settings


def get_supabase() -> Client:
    t = max(5.0, float(settings.supabase_postgrest_timeout_seconds))
    options = ClientOptions(postgrest_client_timeout=Timeout(t))
    return create_client(settings.supabase_url, settings.supabase_service_role_key, options=options)

