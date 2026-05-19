"""Shared Pro-server auth dependency."""

from __future__ import annotations

import os

from fastapi import Header, HTTPException


def require_bearer(authorization: str | None = Header(default=None)) -> str:
    expected = os.environ.get("PRO_API_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="Pro server token not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid bearer token")
    return token