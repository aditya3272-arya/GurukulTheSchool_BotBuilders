from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Role = Literal["visitor", "student", "staff"]


class LoginIn(BaseModel):
    role: Role
    name: Optional[str] = Field(default=None, max_length=120)
    adm_no: Optional[str] = Field(default=None, max_length=50)
    staff_id: Optional[str] = Field(default=None, max_length=50)


class MeOut(BaseModel):
    user_id: str
    role: Role
    name: str


class ChatSessionOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class ChatSessionCreateOut(BaseModel):
    id: str


class ChatSessionRenameIn(BaseModel):
    title: str = Field(min_length=1, max_length=80)


class ChatMessageOut(BaseModel):
    id: str
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: str


class ChatTurnIn(BaseModel):
    session_id: str
    message: str = Field(min_length=1, max_length=2000)


class ChatTurnOut(BaseModel):
    answer: str
    follow_ups: List[str] = Field(default_factory=list)
    intent: Dict[str, Any] = Field(default_factory=dict)
