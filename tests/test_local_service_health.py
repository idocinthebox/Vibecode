from __future__ import annotations

from fastapi.testclient import TestClient

from vibecode.api.app import create_app


def test_health_check_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "storage_backend" in data


def test_service_binds_loopback_only_by_default() -> None:
    from vibecode.config.settings import ServiceSettings

    settings = ServiceSettings()
    assert settings.service_host == "127.0.0.1"
