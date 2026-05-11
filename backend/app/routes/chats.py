from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import SessionData
from app.models.schemas import (
    ChatMessageOut,
    ChatSessionCreateOut,
    ChatSessionOut,
    ChatSessionRenameIn,
)
from app.routes.deps import require_session
from app.services.repo import Repo
from app.services.supabase_client import get_supabase


router = APIRouter(prefix="/api", tags=["chats"])


@router.get("/chats", response_model=list[ChatSessionOut])
def list_chats(session: SessionData = Depends(require_session)):
    repo = Repo(get_supabase())
    return repo.list_chat_sessions(user_id=session.user_id)


@router.post("/chats", response_model=ChatSessionCreateOut)
def create_chat(session: SessionData = Depends(require_session)):
    repo = Repo(get_supabase())
    created = repo.create_chat_session(user_id=session.user_id, title="New chat")
    return ChatSessionCreateOut(id=created["id"])


@router.patch("/chats/{session_id}")
def rename_chat(session_id: str, body: ChatSessionRenameIn, session: SessionData = Depends(require_session)):
    repo = Repo(get_supabase())
    repo.rename_chat_session(session_id=session_id, user_id=session.user_id, title=body.title.strip())
    return {"ok": True}


@router.delete("/chats/{session_id}")
def delete_chat(session_id: str, session: SessionData = Depends(require_session)):
    repo = Repo(get_supabase())
    repo.delete_chat_session(session_id=session_id, user_id=session.user_id)
    return {"ok": True}


@router.get("/chats/{session_id}/messages", response_model=list[ChatMessageOut])
def get_messages(session_id: str, session: SessionData = Depends(require_session)):
    repo = Repo(get_supabase())
    return repo.list_messages(session_id=session_id, user_id=session.user_id)

