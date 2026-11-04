"""Thin HTTP client for the Fantasy Pulse API. The UI never imports backend code."""
import httpx


class ApiError(Exception):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class PulseAPI:
    def __init__(self, base_url: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout      # generous: free hosts can take a while to wake up

    def _request(self, method: str, path: str, **kwargs):
        try:
            r = httpx.request(method, f"{self.base_url}{path}", timeout=self.timeout, **kwargs)
        except httpx.RequestError as exc:
            raise ApiError(f"Cannot reach the API at {self.base_url} ({exc.__class__.__name__}).") from exc
        if r.status_code >= 400:
            try:
                detail = r.json().get("detail", r.text)
            except Exception:
                detail = r.text
            if isinstance(detail, list):   # FastAPI validation errors
                detail = "; ".join(str(d.get("msg", d)) for d in detail)
            raise ApiError(str(detail), r.status_code)
        return r.json()

    def health(self):
        return self._request("GET", "/health")

    def matches(self):
        return self._request("GET", "/matches")

    def match(self, match_id: str):
        return self._request("GET", f"/matches/{match_id}")

    def sample_team(self, match_id: str):
        return self._request("GET", f"/matches/{match_id}/sample-team")

    def pulse(self, payload: dict):
        return self._request("POST", "/pulse", json=payload)

    def chat(self, payload: dict):
        return self._request("POST", "/chat", json=payload)
