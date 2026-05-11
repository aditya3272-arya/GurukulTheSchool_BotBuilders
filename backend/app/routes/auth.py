from __future__ import annotations
from fastapi import APIRouter, HTTPException, Response, Depends
from app.core.config import settings
from app.core.security import SessionData, sign_session
from app.models.schemas import LoginIn, MeOut
from app.routes.deps import SESSION_COOKIE_NAME, get_session
from app.services.repo import Repo
from app.services.supabase_client import get_supabase

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/me", response_model=MeOut)
def me(session: SessionData | None = Depends(get_session)):
    if session is None:
        raise HTTPException(status_code=401, detail="Not signed in")
    return MeOut(user_id=session.user_id, role=session.role, name=session.name)


@router.post("/login", response_model=MeOut)
def login(body: LoginIn, response: Response):
    repo = Repo(get_supabase())
    school_id = settings.school_id  

    role = body.role
    name = (body.name or "").strip()

    if role == "visitor":
        user = repo.get_or_create_visitor_user(name=name or "Visitor")

    elif role == "student":
        if not body.adm_no or not name:
            raise HTTPException(
                status_code=400,
                detail="adm_no and name are required for student login",
            )
        user = repo.get_student_user(adm_no=body.adm_no.strip(), name=name)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid student credentials")

    elif role == "staff":
        if not body.staff_id or not name:
            raise HTTPException(
                status_code=400,
                detail="staff_id and name are required for staff login",
            )
        user = repo.get_staff_user(staff_id=body.staff_id.strip(), name=name)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid staff credentials")

    else:
        raise HTTPException(status_code=400, detail="Invalid role")

    session = SessionData(
        user_id=user["id"],
        role=user["role"],
        name=user.get("name") or "",
        adm_no=user.get("adm_no"),       
        staff_id=user.get("staff_id"),  
    )

    token = sign_session(session)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.session_max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=False,  
        path="/",
    )
    return MeOut(user_id=session.user_id, role=session.role, name=session.name)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"ok": True}