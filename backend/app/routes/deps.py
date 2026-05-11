from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException

from app.core.security import SessionData, verify_session


SESSION_COOKIE_NAME = "cortexia_session"


def get_session(cortexia_session: str | None = Cookie(default=None)) -> SessionData | None:
    return verify_session(cortexia_session or "")


def require_session(session: SessionData | None = Depends(get_session)) -> SessionData:
    if session is None:
        raise HTTPException(status_code=401, detail="Not signed in")
    return session

