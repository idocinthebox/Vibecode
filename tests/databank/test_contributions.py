"""Phase 3 Pro server contribution route tests."""
from __future__ import annotations

from fastapi.testclient import TestClient

from server.pro.main import create_pro_app


def test_submit_contribution_returns_submission_id(tmp_path) -> None:
    app = create_pro_app(data_dir=tmp_path)
    client = TestClient(app)

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
    resp = client.post('/databank/contributions', json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body['submission_id']
    assert body['review_state'] == 'pending'


def test_retract_contribution_marks_inactive(tmp_path) -> None:
    app = create_pro_app(data_dir=tmp_path)
    client = TestClient(app)

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
    created = client.post('/databank/contributions', json=payload).json()
    sid = created['submission_id']

    resp = client.delete(f'/databank/contributions/{sid}')
    assert resp.status_code == 200
    assert resp.json().get('ok') is True
