"""Tests for Phase 5: Rate-limit middleware."""

from __future__ import annotations

import asyncio
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from vibecode.api.middleware import RateLimitMiddleware


def _make_app(default_per_min: int = 5, pre_edit_check_per_min: int = 2) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        default_per_min=default_per_min,
        pre_edit_check_per_min=pre_edit_check_per_min,
    )

    @app.get("/health")
    def health() -> dict:
        return {"ok": True}

    @app.post("/memory/pre-edit-check")
    def pre_edit_check() -> dict:
        return {"matches": []}

    return app


def test_requests_below_limit_succeed() -> None:
    app = _make_app(default_per_min=10)
    client = TestClient(app, raise_server_exceptions=True)
    for _ in range(5):
        resp = client.get("/health")
        assert resp.status_code == 200


def test_requests_above_limit_return_429() -> None:
    app = _make_app(default_per_min=3)
    client = TestClient(app, raise_server_exceptions=True)
    statuses = [client.get("/health").status_code for _ in range(6)]
    assert statuses[:3] == [200, 200, 200]
    assert 429 in statuses[3:]


def test_pre_edit_check_uses_tighter_limit() -> None:
    app = _make_app(default_per_min=20, pre_edit_check_per_min=2)
    client = TestClient(app, raise_server_exceptions=True)
    statuses = [client.post("/memory/pre-edit-check", json={}).status_code for _ in range(5)]
    assert statuses[0] == 200
    assert statuses[1] == 200
    assert 429 in statuses[2:]


def test_429_response_has_json_body() -> None:
    app = _make_app(default_per_min=1)
    client = TestClient(app, raise_server_exceptions=True)
    client.get("/health")
    resp = client.get("/health")
    assert resp.status_code == 429
    assert resp.headers.get("retry-after") == "60"
    body = resp.json()
    assert body["error"] == "RATE_LIMITED"
    assert "limit_per_min" in body


def test_xff_spoofing_does_not_bypass_limit() -> None:
    app = _make_app(default_per_min=1)
    client = TestClient(app, raise_server_exceptions=True)

    first = client.get("/health", headers={"X-Forwarded-For": "203.0.113.1"})
    second = client.get("/health", headers={"X-Forwarded-For": "198.51.100.2"})

    assert first.status_code == 200
    assert second.status_code == 429
