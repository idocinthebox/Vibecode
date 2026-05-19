"""Tests for Phase 4: Pro Sync Adapter."""
from __future__ import annotations

import pytest


class MockHTTPX:
    """Minimal httpx mock for unit tests."""

    class Response:
        def __init__(self, data: dict, status_code: int = 200) -> None:
            self._data = data
            self.status_code = status_code

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

        def json(self) -> dict:
            return self._data

    def __init__(self, responses: dict) -> None:
        self.responses = responses
        self.calls: list[tuple] = []

    def post(self, url: str, **kwargs) -> "MockHTTPX.Response":
        self.calls.append(("POST", url, kwargs))
        return self.responses.get(url, self.Response({"error": "not_mocked"}))

    def get(self, url: str, **kwargs) -> "MockHTTPX.Response":
        self.calls.append(("GET", url, kwargs))
        return self.responses.get(url, self.Response({"error": "not_mocked"}))

    def delete(self, url: str, **kwargs) -> "MockHTTPX.Response":
        self.calls.append(("DELETE", url, kwargs))
        return self.responses.get(url, self.Response({"error": "not_mocked"}))


def test_pro_sync_adapter_not_configured_when_missing_env() -> None:
    from vibecode.integrations.pro_sync import ProSyncAdapter

    adapter = ProSyncAdapter(endpoint="", token="")
    assert not adapter.is_configured()


def test_pro_sync_adapter_configured_when_both_set() -> None:
    from vibecode.integrations.pro_sync import ProSyncAdapter

    adapter = ProSyncAdapter(endpoint="http://localhost:8766", token="tok-abc123")
    assert adapter.is_configured()


def test_pro_sync_submit_returns_submission_id(monkeypatch) -> None:
    from vibecode import integrations

    mock = MockHTTPX(
        {
            "http://localhost:8766/databank/contributions": MockHTTPX.Response(
                {"submission_id": "sub-001", "review_state": "pending"}
            )
        }
    )
    monkeypatch.setattr(
        "vibecode.integrations.pro_sync._get_httpx",
        lambda: mock,
    )
    from vibecode.integrations.pro_sync import ProSyncAdapter

    adapter = ProSyncAdapter(endpoint="http://localhost:8766", token="tok-abc123")
    result = adapter.submit(
        memory_type="failure_pattern",
        data={"task_intent": "test", "prevention_rule": "do not test"},
    )
    assert result.get("submission_id") == "sub-001"


def test_pro_sync_search_returns_results(monkeypatch) -> None:
    mock = MockHTTPX(
        {
            "http://localhost:8766/databank/search": MockHTTPX.Response(
                {"results": [{"title": "Use Depends()", "memory_type": "failure_pattern"}], "total": 1}
            )
        }
    )
    monkeypatch.setattr("vibecode.integrations.pro_sync._get_httpx", lambda: mock)
    from vibecode.integrations.pro_sync import ProSyncAdapter

    adapter = ProSyncAdapter(endpoint="http://localhost:8766", token="tok-abc123")
    result = adapter.search(query="sqlite threading")
    assert len(result["results"]) == 1


def test_pro_sync_retract_sends_delete(monkeypatch) -> None:
    mock = MockHTTPX(
        {"http://localhost:8766/databank/contributions/sub-001": MockHTTPX.Response({"ok": True})}
    )
    monkeypatch.setattr("vibecode.integrations.pro_sync._get_httpx", lambda: mock)
    from vibecode.integrations.pro_sync import ProSyncAdapter

    adapter = ProSyncAdapter(endpoint="http://localhost:8766", token="tok-abc123")
    result = adapter.retract("sub-001")
    assert result.get("ok") is True
    assert any(c[0] == "DELETE" for c in mock.calls)


def test_pro_sync_network_error_returns_error_dict(monkeypatch) -> None:
    def _raise(*a, **kw):
        raise ConnectionError("refused")

    import types

    broken = types.SimpleNamespace(
        post=lambda *a, **kw: (_ for _ in ()).throw(ConnectionError("refused")),
        get=lambda *a, **kw: (_ for _ in ()).throw(ConnectionError("refused")),
        delete=lambda *a, **kw: (_ for _ in ()).throw(ConnectionError("refused")),
    )
    monkeypatch.setattr("vibecode.integrations.pro_sync._get_httpx", lambda: broken)
    from vibecode.integrations.pro_sync import ProSyncAdapter

    adapter = ProSyncAdapter(endpoint="http://localhost:8766", token="tok-abc123")
    result = adapter.get_status()
    assert "error" in result
