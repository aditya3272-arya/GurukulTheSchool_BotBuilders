from __future__ import annotations

from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.chats import router as chats_router


def create_app() -> FastAPI:
    app = FastAPI(title="Cortexia API", version="0.1.0")

    @app.exception_handler(httpx.TimeoutException)
    async def _supabase_timeout_handler(_request, _exc: httpx.TimeoutException):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Database request timed out. Check SUPABASE_URL, service role key, and network access to Supabase."
            },
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(chats_router)
    app.include_router(chat_router)

    project_root = Path(__file__).resolve().parents[2]
    frontend_dir = project_root / "frontend"
    assets = {
        "Logo.png": project_root / "Logo.png",
        "Cortexia Logo.png": project_root / "Cortexia Logo.png",
        "Round Logo.png": project_root / "Round Logo.png",
    }

    @app.get("/assets/{asset_name}")
    def get_asset(asset_name: str):
        p = assets.get(asset_name)
        if not p or not p.exists():
            return {"error": "asset_not_found"}
        return FileResponse(path=str(p))

    if settings.serve_frontend and frontend_dir.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    return app


app = create_app()
