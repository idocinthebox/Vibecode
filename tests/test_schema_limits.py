from __future__ import annotations

from pydantic import ValidationError

from vibecode.api.schemas import CaptureFailureRequest, CaptureSuccessRequest, PreEditCheckRequest


def test_capture_success_code_fields_are_limited() -> None:
    too_large = "x" * 10001
    try:
        CaptureSuccessRequest(
            project_path="/tmp/project",
            name="n",
            intent_description="i",
            code_before=too_large,
        )
        assert False, "expected validation error"
    except ValidationError as exc:
        assert "code_* fields" in str(exc)


def test_capture_failure_task_intent_is_limited() -> None:
    too_large = "x" * 501
    try:
        CaptureFailureRequest(
            project_path="/tmp/project",
            task_intent=too_large,
            bad_suggestion="bad",
            failure_reason="reason",
            prevention_rule="rule",
        )
        assert False, "expected validation error"
    except ValidationError as exc:
        assert "task_intent" in str(exc)


def test_tags_are_limited() -> None:
    tags = [f"t{i}" for i in range(51)]
    try:
        CaptureFailureRequest(
            project_path="/tmp/project",
            task_intent="intent",
            bad_suggestion="bad",
            failure_reason="reason",
            prevention_rule="rule",
            tags=tags,
        )
        assert False, "expected validation error"
    except ValidationError as exc:
        assert "tags" in str(exc)


def test_pre_edit_task_intent_limit() -> None:
    too_large = "x" * 501
    try:
        PreEditCheckRequest(
            project_path="/tmp/project",
            file_path="/tmp/project/a.py",
            language="python",
            proposed_text="print('hi')",
            task_intent=too_large,
        )
        assert False, "expected validation error"
    except ValidationError as exc:
        assert "task_intent" in str(exc)
