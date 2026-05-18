from __future__ import annotations

from pathlib import Path

from vibecode.core.security import ProjectAllowlist
from vibecode.db.sqlite_connection import get_connection
from vibecode.db.sqlite_schema import create_schema
from vibecode.harvest.service import KnowledgeHarvester


def test_harvest_rerun_dedupes_and_increments_occurrence_for_failures(tmp_path: Path) -> None:
    base = tmp_path / ".vibecode"
    base.mkdir()
    allowlist = ProjectAllowlist(base)
    allowlist.add(str(tmp_path))

    doc = tmp_path / "README.md"
    doc.write_text(
        """
## Common mistake: shell quoting
PowerShell escaping caused a broken command.

```powershell
git commit -m \"bad quote\"
```

Fix: Use a here-string for multi-quoted messages.
""".strip(),
        encoding="utf-8",
    )

    harvester = KnowledgeHarvester(base)
    first = harvester.scan(str(tmp_path), include=["README.md"], dry_run=False)
    second = harvester.scan(str(tmp_path), include=["README.md"], dry_run=False)

    assert first["candidates"] >= 1
    assert second["duplicates_skipped"] >= 1

    conn = get_connection(base)
    create_schema(conn)
    row = conn.execute("SELECT COUNT(*) AS c FROM failure_patterns WHERE is_active = 1").fetchone()
    assert row["c"] == 1
    occ = conn.execute("SELECT occurrence_count FROM failure_patterns LIMIT 1").fetchone()
    assert occ["occurrence_count"] >= 2
    conn.close()
