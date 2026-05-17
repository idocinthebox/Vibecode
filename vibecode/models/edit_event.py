from __future__ import annotations

from pydantic import BaseModel, Field


class EditRange(BaseModel):
    start_line: int = 0
    start_character: int = 0
    end_line: int = 0
    end_character: int = 0


class EditEvent(BaseModel):
    event_id: str
    project_path: str
    file_path: str
    language: str = ""
    agent_source: str = "unknown"
    range: EditRange = Field(default_factory=EditRange)
    text_before: str = ""
    text_after: str = ""
    timestamp: float
    document_version: int = 0
