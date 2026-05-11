from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from app.core.config import settings

Role = Literal["visitor", "student", "staff"]


@dataclass(frozen=True)
class SessionData:
    user_id:  str
    role:     Role
    name:     str
    adm_no:   str | None = None   
    staff_id: str | None = None   


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.session_secret, salt="cortexia-session-v1")


def sign_session(data: SessionData) -> str:
    s = _serializer()
    return s.dumps(
        {
            "user_id":  data.user_id,
            "role":     data.role,
            "name":     data.name,
            "adm_no":   data.adm_no,
            "staff_id": data.staff_id,   
        }
    )


def verify_session(token: str) -> Optional[SessionData]:
    if not token:
        return None
    s = _serializer()
    try:
        payload = s.loads(token, max_age=settings.session_max_age_seconds)
        return SessionData(
            user_id=str(payload["user_id"]),
            role=payload["role"],
            name=str(payload.get("name") or ""),
            adm_no=payload.get("adm_no"),
            staff_id=payload.get("staff_id"),   
        )
    except (BadSignature, SignatureExpired, KeyError, TypeError, ValueError):
        return None