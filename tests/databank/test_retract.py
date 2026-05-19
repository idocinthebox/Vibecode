"""Phase 3 Pro server retract behavior tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from server.pro.main import create_pro_app

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def _client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("PRO_API_TOKEN", "test-token")
    return TestClient(create_pro_app(data_dir=tmp_path))


def _submit_and_approve(client: TestClient) -> str:
    payload = {
        "memory_type": "failure_pattern",
        "data": {
            "task_intent": "Use Depends in FastAPI",
            "prevention_rule": "Avoid module-level SQLite connections",
            "language": "python",
            "framework": "fastapi",
            "tags": ["sqlite", "fastapi"],
        },
        "submitted_by": "tests",
    }

    created = client.post("/databank/contributions", json=payload, headers=AUTH_HEADERS)
    assert created.status_code == 200
    submission_id = created.json()["submission_id"]

    queue = client.get("/databank/moderation/queue", headers=AUTH_HEADERS)
    assert queue.status_code == 200
    pending = queue.json().get("queue", [])
    pending_item = next((item for item in pending if item["id"] == submission_id), None)
    assert pending_item is not None

    approved = client.post(
        f"/databank/moderation/{submission_id}/approve",
        json={},
        headers=AUTH_HEADERS,
    )
    assert approved.status_code == 200
    return submission_id


def test_retract_contribution_removes_item_from_search_results(tmp_path, monkeypatch) -> None:
    client = _client(tmp_path, monkeypatch)
    submission_id = _submit_and_approve(client)

    before = client.post(
        "/databank/search",
        json={"query": "sqlite FastAPI", "max_results": 10},
        headers=AUTH_HEADERS,
    )
    assert before.status_code == 200
    before_ids = [item["submission_id"] for item in before.json().get("results", [])]
    assert submission_id in before_ids

    retracted = client.delete(f"/databank/contributions/{submission_id}", headers=AUTH_HEADERS)
    assert retracted.status_code == 200
    assert retracted.json().get("ok") is True

    after = client.post(
        "/databank/search",
        json={"query": "sqlite FastAPI", "max_results": 10},
        headers=AUTH_HEADERS,
    )
    assert after.status_code == 200
    after_ids = [item["submission_id"] for item in after.json().get("results", [])]
    assert submission_id not in after_ids
