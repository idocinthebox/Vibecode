from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class DiagnosticSignal(BaseModel):
    project_path: str
    file_path: str
    message: str = ""
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    is_new: bool = False
    is_resolved: bool = False
    timestamp: float


class TestSignal(BaseModel):
    project_path: str
    status_before: Literal["pass", "fail", "unknown"] = "unknown"
    status_after: Literal["pass", "fail", "unknown"] = "unknown"
    test_name: str = ""
    file_path: str = ""
    timestamp: float


class RevertSignal(BaseModel):
    project_path: str
    event_id: str
    reverted_to_text: str = ""
    timestamp: float


class TerminalSignal(BaseModel):
    project_path: str
    cwd: str
    command: str
    exit_code: int
    ended_at: float
