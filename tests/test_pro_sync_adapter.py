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

    def post(self, url: str, **kwargs) -> MockHTTPX.Response:
        self.calls.append(("POST", url, kwargs))
        return self.responses.get(url, self.Response({"error": "not_mocked"}))

    def get(self, url: str, **kwargs) -> MockHTTPX.Response:
        self.calls.append(("GET", url, kwargs))
        return self.responses.get(url, self.Response({"error": "not_mocked"}))

    def delete(self, url: str, **kwargs) -> MockHTTPX.Response:
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
    mock = MockHTTPX({"http://localhost:8766/databank/contributions/sub-001": MockHTTPX.Response({"ok": True})})
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


def test_pro_share_redacts_secrets_and_uses_allowlist(temp_base, monkeypatch) -> None:
    from vibecode.core.memory_service import VibeCodeService
    from vibecode.db.sqlite_connection import get_connection
    from vibecode.db.sqlite_schema import create_schema

    conn = get_connection(temp_base)
    create_schema(conn)
    conn.execute(
        """
        INSERT INTO failure_patterns (
            failure_id, task_intent, bad_suggestion, failure_reason, prevention_rule,
            language, framework, severity, content_hash, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """,
        (
            "failure-1",
            "Avoid leaks",
            "echo key",
            "Leaked token sk_live_abc123secret in logs",
            "Never print secrets",
            "python",
            "pytest",
            "high",
            "hash-1",
            "2026-05-18T00:00:00Z",
            "2026-05-18T00:00:00Z",
        ),
    )
    conn.commit()
    conn.close()

    captured: dict[str, object] = {}

    class Adapter:
        def is_configured(self) -> bool:
            return True

        def submit(self, memory_type: str, data: dict) -> dict:
            captured["memory_type"] = memory_type
            captured["data"] = data
            return {"ok": True, "submission_id": "sub-1", "review_state": "pending"}

    service = VibeCodeService(base_dir=temp_base)
    monkeypatch.setattr(service, "_get_pro_adapter", lambda: Adapter())

    try:
        result = service.pro_share("failure_pattern", "failure-1")
        assert result.get("submission_id") == "sub-1"
        payload = captured["data"]
        assert isinstance(payload, dict)
        assert "sk_live_" not in str(payload.get("failure_reason", ""))
        assert "content_hash" not in payload
        assert set(payload.keys()) == {
            "failure_id",
            "task_intent",
            "bad_suggestion",
            "failure_reason",
            "prevention_rule",
            "corrected_approach",
            "language",
            "framework",
            "severity",
        }
    finally:
        if service.conn is not None:
            service.conn.close()


def test_pro_share_rejects_disallowed_project(temp_base, monkeypatch) -> None:
    from vibecode.core.memory_service import VibeCodeService

    class Adapter:
        def is_configured(self) -> bool:
            return True

    service = VibeCodeService(base_dir=temp_base)
    monkeypatch.setattr(service, "_get_pro_adapter", lambda: Adapter())

    result = service.pro_share("failure_pattern", "missing", project_path="D:/not-allowed")
    assert result["error"] == "PROJECT_NOT_ALLOWED"


def test_pro_methods_map_adapter_exceptions_to_stable_error(temp_base, monkeypatch) -> None:
    from vibecode.core.memory_service import VibeCodeService

    class Adapter:
        def is_configured(self) -> bool:
            return True

        def submit(self, memory_type: str, data: dict) -> dict:
            raise RuntimeError("adapter down")

        def retract(self, submission_id: str) -> dict:
            raise RuntimeError("adapter down")

        def get_status(self) -> dict:
            raise RuntimeError("adapter down")

        def search(self, query: str, max_results: int = 10) -> dict:
            raise RuntimeError("adapter down")

    service = VibeCodeService(base_dir=temp_base)
    monkeypatch.setattr(service, "_get_pro_adapter", lambda: Adapter())

    assert service.pro_retract("sub-1")["error"] == "PRO_REQUEST_FAILED"
    assert service.pro_status()["error"] == "PRO_REQUEST_FAILED"
    assert service.pro_search("threading")["error"] == "PRO_REQUEST_FAILED"
