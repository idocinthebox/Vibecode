"""Background confidence decay job.

Runs the ``decay_confidence()`` function from ``vibecode.core.health_service``
on a fixed interval (default 6 hours). Designed to run in a daemon thread
so it never blocks startup and never prevents clean shutdown.

Usage::

    from vibecode.jobs.confidence_decay import start_decay_scheduler
    start_decay_scheduler(base_dir)
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_scheduler_started = False
_scheduler_lock = threading.Lock()


def run_once(base_dir: Path) -> int:
    """Run one decay pass and return the number of patterns decayed.

    Opens its own SQLite connection to avoid threading conflicts.
    Returns 0 if the database does not exist or decay fails.
    """
    from vibecode.core.health_service import decay_confidence
    from vibecode.db.sqlite_connection import get_connection, get_db_path

    db_path = get_db_path(base_dir)
    if not db_path.exists():
        return 0
    try:
        conn = get_connection(base_dir)
        decayed = decay_confidence(conn)
        conn.close()
        logger.debug("Confidence decay pass: %d patterns updated", decayed)
        return decayed
    except Exception as exc:
        logger.warning("Confidence decay error: %s", exc)
        return 0


def _decay_loop(base_dir: Path, interval_seconds: int) -> None:
    """Infinite loop that calls run_once every *interval_seconds*."""
    while True:
        try:
            run_once(base_dir)
        except Exception as exc:  # pragma: no cover
            logger.warning("Unhandled error in decay loop: %s", exc)
        time.sleep(interval_seconds)


def start_decay_scheduler(base_dir: Path, interval_hours: int = 6) -> bool:
    """Start the background decay scheduler thread (idempotent).

    Returns True if the scheduler was started, False if already running.
    """
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return False
        interval_seconds = interval_hours * 3600
        thread = threading.Thread(
            target=_decay_loop,
            args=(Path(base_dir), interval_seconds),
            daemon=True,
            name="vibecode-confidence-decay",
        )
        thread.start()
        _scheduler_started = True
        logger.info(
            "Confidence decay scheduler started (interval=%dh, thread=%s)",
            interval_hours,
            thread.name,
        )
        return True
