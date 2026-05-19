from __future__ import annotations

from fastapi.testclient import TestClient

from server.pro.main import create_pro_app


def _payload() -> dict:
    return {
        "memory_type": "failure_pattern",
        "data": {
            "task_intent": "Auth test",
            "prevention_rule": "Use bearer token",
        },
        "submitted_by": "tests",
    }


def test_missing_header_returns_401(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRO_API_TOKEN", "test-token")
    client = TestClient(create_pro_app(data_dir=tmp_path))

    resp = client.post("/databank/contributions", json=_payload())
    assert resp.status_code == 401


def test_wrong_token_returns_403(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PRO_API_TOKEN", "test-token")
    client = TestClient(create_pro_app(data_dir=tmp_path))

    resp = client.post(
        "/databank/contributions",
        json=_payload(),
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert resp.status_code == 403


def test_missing_env_returns_503(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("PRO_API_TOKEN", raising=False)
    client = TestClient(create_pro_app(data_dir=tmp_path))

    resp = client.post(
        "/databank/contributions",
        json=_payload(),
        headers={"Authorization": "Bearer test-token"},
    )
    assert resp.status_code == 503
