from __future__ import annotations

import json

from nightwatch import obeos_events


class _Response:
    status = 201
    def __enter__(self): return self
    def __exit__(self, *args): return False


def test_publish_event_is_disabled_without_endpoint(monkeypatch):
    monkeypatch.delenv("OBEOS_EVENT_URL", raising=False)
    assert obeos_events.publish_event("nightwatch.task.created", {"task_id": 1}) is False


def test_publish_event_sends_v1_envelope(monkeypatch):
    captured = {}
    monkeypatch.setenv("OBEOS_EVENT_URL", "http://127.0.0.1:8000/events/v1/publish")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response()

    monkeypatch.setattr(obeos_events, "urlopen", fake_urlopen)
    assert obeos_events.publish_event("nightwatch.task.created", {"task_id": 7}) is True
    payload = captured["payload"]
    assert payload["contract_version"] == "1.0"
    assert payload["event_type"] == "nightwatch.task.created"
    assert payload["source"] == "nightwatch"
    assert payload["payload"] == {"task_id": 7}
