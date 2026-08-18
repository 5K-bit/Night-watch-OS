from __future__ import annotations

import json
from io import BytesIO

from nightwatch.client import NightwatchClient


class _Response:
    def __init__(self, payload) -> None:
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._body


def test_client_uses_http_boundary(monkeypatch) -> None:
    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"] = request.full_url
        seen["method"] = request.get_method()
        seen["timeout"] = timeout
        return _Response({"ok": True})

    monkeypatch.setattr("nightwatch.client.urlopen", fake_urlopen)
    client = NightwatchClient("http://127.0.0.1:8037/", timeout=1.5)

    assert client.health() == {"ok": True}
    assert seen == {
        "url": "http://127.0.0.1:8037/api/health",
        "method": "GET",
        "timeout": 1.5,
    }
