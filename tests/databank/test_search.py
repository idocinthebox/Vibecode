"""Phase 3 Pro server search and feedback tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.pro.main import create_pro_app

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("PRO_API_TOKEN", "test-token")
    return TestClient(create_pro_app(data_dir=tmp_path))


def _submit(client: TestClient, title: str, summary: str) -> str:
    payload = {
        "memory_type": "failure_pattern",
        "data": {
            "task_intent": title,
            "prevention_rule": summary,
            "language": "python",
            "framework": "pytest",
            "tags": ["search"],
        },
        "submitted_by": "tests",
    }
    body = client.post("/databank/contributions", json=payload, headers=AUTH_HEADERS).json()
    return body["submission_id"]


def test_search_returns_ranked_results(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    _submit(client, "Use Depends in FastAPI", "avoid sqlite thread issues")
    _submit(client, "Pin dependencies", "avoid package drift in CI")
    _submit(client, "Completely unrelated guidance", "foo bar baz")

    # Approve items via moderation endpoint so they become searchable
    queue = client.get("/databank/moderation/queue", headers=AUTH_HEADERS).json()["queue"]
    for item in queue:
        client.post(f"/databank/moderation/{item['id']}/approve", json={}, headers=AUTH_HEADERS)

    resp = client.post("/databank/search", json={"query": "sqlite thread", "max_results": 10}, headers=AUTH_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert len(body["results"]) >= 1
    assert "Depends" in body["results"][0]["title"]


def test_feedback_updates_usefulness(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)

    sid = _submit(client, "Use Depends in FastAPI", "avoid sqlite thread issues")
    queue = client.get("/databank/moderation/queue", headers=AUTH_HEADERS).json()["queue"]
    for item in queue:
        client.post(f"/databank/moderation/{item['id']}/approve", json={}, headers=AUTH_HEADERS)

    fb = client.post("/databank/feedback", json={"submission_id": sid, "was_useful": True}, headers=AUTH_HEADERS)
    assert fb.status_code == 200
    assert fb.json().get("ok") is True
