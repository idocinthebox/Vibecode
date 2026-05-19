"""Phase 3 Pro server moderation route tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from server.pro.main import create_pro_app


def _submit(client: TestClient) -> str:
    payload = {
        "memory_type": "failure_pattern",
        "data": {
            "task_intent": "Avoid force push",
            "prevention_rule": "Use --force-with-lease",
            "language": "git",
            "framework": "",
            "tags": ["git"],
        },
        "submitted_by": "tests",
    }
    return client.post('/databank/contributions', json=payload).json()['submission_id']


def test_moderation_queue_lists_pending(tmp_path) -> None:
    app = create_pro_app(data_dir=tmp_path)
    client = TestClient(app)

    _submit(client)
    resp = client.get('/databank/moderation/queue')
    assert resp.status_code == 200
    body = resp.json()
    assert body['total'] >= 1


def test_approve_reject_escalate_endpoints(tmp_path) -> None:
    app = create_pro_app(data_dir=tmp_path)
    client = TestClient(app)

    sid = _submit(client)
    queue = client.get('/databank/moderation/queue').json()['queue']
    item_id = queue[0]['id']

    approved = client.post(f'/databank/moderation/{item_id}/approve', json={})
    assert approved.status_code == 200

    sid2 = _submit(client)
    queue2 = client.get('/databank/moderation/queue').json()['queue']
    item_id2 = queue2[0]['id']

    rejected = client.post(f'/databank/moderation/{item_id2}/reject', json={})
    assert rejected.status_code == 200

    sid3 = _submit(client)
    queue3 = client.get('/databank/moderation/queue').json()['queue']
    item_id3 = queue3[0]['id']

    escalated = client.post(f'/databank/moderation/{item_id3}/escalate', json={})
    assert escalated.status_code == 200
