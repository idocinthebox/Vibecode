from __future__ import annotations

import sqlite3
from datetime import datetime, timezone


def decay_confidence(conn: sqlite3.Connection, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    changed = 0

    for table in ("success_patterns", "failure_patterns"):
        rows = conn.execute(
            f"SELECT id, confidence, COALESCE(last_seen_at, updated_at) AS seen_at FROM {table}"
        ).fetchall()
        for row in rows:
            seen_raw = row["seen_at"]
            if not seen_raw:
                continue
            try:
                seen_at = datetime.fromisoformat(seen_raw)
            except ValueError:
                continue

            days = (now - seen_at.replace(tzinfo=timezone.utc)).days
            if days < 90:
                continue

            stride = max((days - 90) // 30 + 1, 1)
            new_conf = float(row["confidence"])
            for _ in range(stride):
                new_conf *= 0.9

            conn.execute(
                f"UPDATE {table} SET confidence = ?, updated_at = ? WHERE id = ?",
                (max(new_conf, 0.05), now.isoformat(), row["id"]),
            )
            changed += 1

    conn.commit()
    return changed
