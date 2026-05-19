from unittest.mock import patch

from fastapi.testclient import TestClient


def test_startup_starts_decay_scheduler(tmp_path, monkeypatch):
    monkeypatch.setenv("VIBECODE_DATA_DIR", str(tmp_path))
    with patch("vibecode.api.app.start_decay_scheduler") as start, patch("vibecode.api.app.run_once") as eager:
        from vibecode.api.app import create_app

        with TestClient(create_app()):
            pass

        start.assert_called_once()
        eager.assert_called_once()
