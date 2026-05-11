from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx


class CortexiaApiError(RuntimeError):
    pass


def _friendly_http_error(exc: httpx.HTTPError) -> str:
    if isinstance(exc, httpx.ConnectError):
        return (
            "Cannot reach the Cortexia API. Start the backend (uvicorn), then check APP_BASE_URL in .env "
            "(use http://127.0.0.1:8000 on Windows)."
        )
    if isinstance(exc, httpx.ReadTimeout):
        return (
            "The API took too long to respond. If the backend is running, check Supabase connectivity "
            "or increase CORTEXIA_HTTP_READ_TIMEOUT in .env."
        )
    return f"Network error: {exc}"


@dataclass
class CortexiaApiClient:
    base_url: str = "http://127.0.0.1:8000"
    timeout: httpx.Timeout | float = 25.0
    max_retries: int = 2

    def __post_init__(self) -> None:
        t = self.timeout if isinstance(self.timeout, httpx.Timeout) else httpx.Timeout(self.timeout)
        self._client = httpx.Client(
            base_url=self.base_url.rstrip("/"),
            timeout=t,
            headers={"Content-Type": "application/json"},
        )

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        attempts = max(1, int(self.max_retries) + 1)
        response: httpx.Response | None = None
        for attempt in range(attempts):
            try:
                response = self._client.request(method=method, url=path, **kwargs)
                break
            except (httpx.ReadTimeout, httpx.ConnectError) as exc:
                if attempt + 1 >= attempts:
                    raise CortexiaApiError(_friendly_http_error(exc)) from exc
                time.sleep(0.35 * (attempt + 1))
            except httpx.HTTPError as exc:
                raise CortexiaApiError(_friendly_http_error(exc)) from exc

        assert response is not None
        payload: Any
        try:
            payload = response.json() if response.text else None
        except Exception:
            payload = {"raw": response.text}

        if response.is_error:
            detail = None
            if isinstance(payload, dict):
                detail = payload.get("detail") or payload.get("error") or payload.get("raw")
            raise CortexiaApiError(str(detail or f"Request failed ({response.status_code})"))
        return payload

    def login(
        self,
        role: str,
        name: str | None = None,
        adm_no: str | None = None,
        staff_id: str | None = None,
    ) -> dict[str, Any]:
        return dict(
            self._request(
                "POST",
                "/api/auth/login",
                json={
                    "role": role,
                    "name": name,
                    "adm_no": adm_no,
                    "staff_id": staff_id,
                },
            )
        )

    def me(self) -> dict[str, Any]:
        return dict(self._request("GET", "/api/auth/me"))

    def logout(self) -> dict[str, Any]:
        return dict(self._request("POST", "/api/auth/logout"))

    def list_chats(self) -> list[dict[str, Any]]:
        return list(self._request("GET", "/api/chats") or [])

    def create_chat(self) -> dict[str, Any]:
        return dict(self._request("POST", "/api/chats"))

    def rename_chat(self, session_id: str, title: str) -> dict[str, Any]:
        return dict(self._request("PATCH", f"/api/chats/{session_id}", json={"title": title}))

    def delete_chat(self, session_id: str) -> dict[str, Any]:
        return dict(self._request("DELETE", f"/api/chats/{session_id}"))

    def list_messages(self, session_id: str) -> list[dict[str, Any]]:
        return list(self._request("GET", f"/api/chats/{session_id}/messages") or [])

    def chat_turn(self, session_id: str, message: str) -> dict[str, Any]:
        return dict(self._request("POST", "/api/chat", json={"session_id": session_id, "message": message}))

    def submit_feedback(self, endpoint: str, payload: dict[str, Any]) -> None:
        try:
            response = httpx.post(endpoint, json=payload, headers={"Accept": "application/json"}, timeout=20.0)
        except httpx.HTTPError as exc:
            raise CortexiaApiError(f"Feedback network error: {exc}") from exc

        if response.is_error:
            raise CortexiaApiError(f"Feedback failed ({response.status_code})")
