from __future__ import annotations

from pydantic import ValidationError

from vibecode.api.schemas import PreEditCheckRequest, SearchMemoryRequest


def test_project_path_must_be_absolute() -> None:
    try:
        SearchMemoryRequest(query="x", project_path="relative/path")
        assert False, "expected validation error"
    except ValidationError as exc:
        assert "must be an absolute path" in str(exc)


def test_project_path_rejects_traversal() -> None:
    try:
        SearchMemoryRequest(query="x", project_path="/tmp/../etc")
        assert False, "expected validation error"
    except ValidationError as exc:
        assert "path traversal" in str(exc)


def test_file_path_rejects_traversal() -> None:
    try:
        PreEditCheckRequest(
            project_path="/tmp/project",
            file_path="/tmp/project/../secret.py",
            language="python",
            proposed_text="print('hi')",
        )
        assert False, "expected validation error"
    except ValidationError as exc:
        assert "path traversal" in str(exc)


def test_valid_absolute_paths_pass() -> None:
    req = PreEditCheckRequest(
        project_path="/tmp/project",
        file_path="/tmp/project/main.py",
        language="python",
        proposed_text="print('ok')",
    )
    assert req.project_path == "/tmp/project"
