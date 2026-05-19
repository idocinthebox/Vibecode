"""Phase 3 Pro server contribution route tests."""

from __future__ import annotations

import sqlite3

from fastapi.testclient import TestClient

from server.pro.main import create_pro_app

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("PRO_API_TOKEN", "test-token")
    return TestClient(create_pro_app(data_dir=tmp_path))


def test_submit_contribution_returns_submission_id(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    payload = {
        "memory_type": "failure_pattern",
        "data": {
            "task_intent": "Avoid module-level sqlite connections",
            "prevention_rule": "Use Depends() in routes",
            "language": "python",
            "framework": "fastapi",
            "tags": ["sqlite", "fastapi"],
        },
        "submitted_by": "tests",
    }
    resp = client.post("/databank/contributions", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["submission_id"]
    assert body["review_state"] == "pending"


def test_retract_contribution_marks_inactive(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    payload = {
        "memory_type": "success_pattern",
        "data": {
            "name": "Test title",
            "reasoning_summary": "Test summary",
            "language": "python",
            "framework": "pytest",
            "tags": ["test"],
        },
        "submitted_by": "tests",
    }
    created = client.post("/databank/contributions", json=payload, headers=AUTH_HEADERS).json()
    sid = created["submission_id"]

    resp = client.delete(f"/databank/contributions/{sid}", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json().get("ok") is True


def test_submit_contribution_redacts_secret(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    payload = {
        "memory_type": "failure_pattern",
        "data": {
            "task_intent": "Leak check",
            "failure_reason": "token sk_live_abc123secret should be redacted",
            "prevention_rule": "Never commit keys",
            "language": "python",
        },
        "submitted_by": "tests",
    }

    resp = client.post("/databank/contributions", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 200
    sid = resp.json()["submission_id"]

    conn = sqlite3.connect(str(tmp_path / "pro_databank.db"))
    row = conn.execute("SELECT body_json FROM databank_patterns WHERE id = ?", (sid,)).fetchone()
    conn.close()

    assert row is not None
    assert "sk_live_" not in row[0]


def test_submit_contribution_rejects_oversized_payload(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    payload = {
        "memory_type": "failure_pattern",
        "data": {
            "task_intent": "too big",
            "prevention_rule": "n/a",
            "x": "a" * 70000,
        },
        "submitted_by": "tests",
    }

    resp = client.post("/databank/contributions", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 413
