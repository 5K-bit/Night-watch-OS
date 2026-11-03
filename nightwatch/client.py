from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class NightwatchClientError(RuntimeError):
    pass


class NightwatchClient:
    """Small HTTP client used by OBEOS surfaces and local integrations."""

    def __init__(self, base_url: str = "http://127.0.0.1:8037", timeout: float = 3.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, payload: dict | None = None):
        body = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = Request(f"{self.base_url}{path}", data=body, headers=headers, method=method)
        try:
            with urlopen(req, timeout=self.timeout) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else None
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise NightwatchClientError(f"Nightwatch HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise NightwatchClientError(f"Nightwatch unavailable: {exc.reason}") from exc

    def health(self):
        return self._request("GET", "/api/health")

    def current_shift(self):
        return self._request("GET", "/api/shift/current")

    def start_shift(self):
        return self._request("POST", "/api/shift/start")

    def end_shift(self):
        return self._request("POST", "/api/shift/end")

    def tasks(self):
        return self._request("GET", "/api/tasks/current")

    def create_task(self, title: str):
        return self._request("POST", "/api/tasks", {"title": title})

    def complete_task(self, task_id: int):
        return self._request("POST", f"/api/tasks/{task_id}/complete")

    def reopen_task(self, task_id: int):
        return self._request("POST", f"/api/tasks/{task_id}/reopen")

    def delete_task(self, task_id: int):
        return self._request("DELETE", f"/api/tasks/{task_id}")

    def system_snapshot(self):
        return self._request("GET", "/api/system")
