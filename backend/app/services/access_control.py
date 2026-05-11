from __future__ import annotations

from typing import Literal, Tuple

Role = Literal["visitor", "student", "staff"]
AccessLevel = Literal["visitor", "student", "staff"]


_rank: dict[str, int] = {"visitor": 1, "student": 2, "staff": 3}


def has_access(role: Role, required: AccessLevel) -> bool:
    return _rank[role] >= _rank[required]


def denial_reason(role: Role, required: AccessLevel) -> str:
    if role == "visitor" and required in ("student", "staff"):
        return "you are signed in as a Visitor"
    if role == "student" and required == "staff":
        return "this information is for Staff only"
    return "your role does not permit this information"


def clamp_required_access(required: str | None) -> AccessLevel:
    if required in ("visitor", "student", "staff"):
        return required
    return "visitor"

