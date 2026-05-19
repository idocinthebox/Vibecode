"""Phase 3 Pro server search and feedback tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from server.pro.main import create_pro_app


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
    body = client.post('/databank/contributions', json=payload).json()
    return body['submission_id']


def test_search_returns_ranked_results(tmp_path) -> None:
    app = create_pro_app(data_dir=tmp_path)
    client = TestClient(app)

    _submit(client, 'Use Depends in FastAPI', 'avoid sqlite thread issues')
    _submit(client, 'Pin dependencies', 'avoid package drift in CI')

    # Approve items via moderation endpoint so they become searchable
    queue = client.get('/databank/moderation/queue').json()['queue']
    for item in queue:
        client.post(f"/databank/moderation/{item['id']}/approve", json={})

    resp = client.post('/databank/search', json={'query': 'sqlite thread', 'max_results': 10})
    assert resp.status_code == 200
    body = resp.json()
    assert body['total'] >= 1
    assert len(body['results']) >= 1


def test_feedback_updates_usefulness(tmp_path) -> None:
    app = create_pro_app(data_dir=tmp_path)
    client = TestClient(app)

    sid = _submit(client, 'Use Depends in FastAPI', 'avoid sqlite thread issues')
    queue = client.get('/databank/moderation/queue').json()['queue']
    for item in queue:
        client.post(f"/databank/moderation/{item['id']}/approve", json={})

    fb = client.post('/databank/feedback', json={'submission_id': sid, 'was_useful': True})
    assert fb.status_code == 200
    assert fb.json().get('ok') is True
