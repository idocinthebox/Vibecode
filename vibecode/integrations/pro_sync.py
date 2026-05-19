"""Pro Databank Sync Adapter.

Thin httpx client for the optional VibeCode Pro shared databank.
All settings are read from env vars: VIBECODE_PRO_ENDPOINT, VIBECODE_PRO_TOKEN.
The adapter is entirely optional — callers must check ``ProSyncAdapter.is_configured()``
before use.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _get_httpx():
    """Lazy import httpx so the rest of the codebase doesn't require it at load."""
    try:
        import httpx
        return httpx
    except ImportError:  # pragma: no cover
        raise ImportError("httpx is required for Pro Sync. Install it with: pip install httpx")


class ProSyncAdapter:
    """HTTP client for the VibeCode Pro shared databank."""

    DEFAULT_TIMEOUT = 10.0

    def __init__(self, endpoint: str = "", token: str = "") -> None:
        self.endpoint = endpoint.rstrip("/")
        self.token = token

    def is_configured(self) -> bool:
        """Return True if both endpoint and token are set."""
        return bool(self.endpoint and self.token)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def submit(
        self,
        memory_type: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Submit a pattern to the Pro databank.

        Args:
            memory_type: ``success_pattern``, ``failure_pattern``, or ``project_rule``
            data: Pattern payload (must not contain secrets — caller must redact first)

        Returns:
            Server response dict with at least ``submission_id``.
        """
        httpx = _get_httpx()
        payload = {"memory_type": memory_type, "data": data}
        try:
            resp = httpx.post(
                f"{self.endpoint}/databank/contributions",
                json=payload,
                headers=self._headers(),
                timeout=self.DEFAULT_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("Pro sync submit failed: %s", exc)
            return {"error": str(exc)}

    def search(self, query: str, max_results: int = 10) -> dict[str, Any]:
        """Search the Pro databank for patterns matching *query*.

        Returns:
            Dict with ``results`` list.
        """
        httpx = _get_httpx()
        payload = {"query": query, "max_results": max_results}
        try:
            resp = httpx.post(
                f"{self.endpoint}/databank/search",
                json=payload,
                headers=self._headers(),
                timeout=self.DEFAULT_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("Pro sync search failed: %s", exc)
            return {"results": [], "error": str(exc)}

    def feedback(self, submission_id: str, was_useful: bool) -> dict[str, Any]:
        """Send feedback on a Pro pattern.

        Args:
            submission_id: The server-assigned submission ID.
            was_useful: Whether the pattern was useful.
        """
        httpx = _get_httpx()
        payload = {"submission_id": submission_id, "was_useful": was_useful}
        try:
            resp = httpx.post(
                f"{self.endpoint}/databank/feedback",
                json=payload,
                headers=self._headers(),
                timeout=self.DEFAULT_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("Pro sync feedback failed: %s", exc)
            return {"error": str(exc)}

    def retract(self, submission_id: str) -> dict[str, Any]:
        """Retract a previously submitted pattern.

        Args:
            submission_id: The server-assigned submission ID to retract.
        """
        httpx = _get_httpx()
        try:
            resp = httpx.delete(
                f"{self.endpoint}/databank/contributions/{submission_id}",
                headers=self._headers(),
                timeout=self.DEFAULT_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("Pro sync retract failed: %s", exc)
            return {"error": str(exc)}

    def get_status(self) -> dict[str, Any]:
        """Return the Pro databank server status and account info."""
        httpx = _get_httpx()
        try:
            resp = httpx.get(
                f"{self.endpoint}/databank/status",
                headers=self._headers(),
                timeout=self.DEFAULT_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("Pro sync get_status failed: %s", exc)
            return {"error": str(exc)}
