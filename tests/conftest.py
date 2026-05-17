from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_base() -> Path:
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)
