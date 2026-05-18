from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from vibecode.api.app import create_app
from vibecode.api.routes_harvest import get_harvester
from vibecode.core.security import ProjectAllowlist
from vibecode.harvest.service import KnowledgeHarvester


def test_harvest_preview_scan_and_report_routes(tmp_path: Path) -> None:
    base = tmp_path / ".vibecode"
    base.mkdir()
    allowlist = ProjectAllowlist(base)
    allowlist.add(str(tmp_path))

    (tmp_path / "CLAUDE.md").write_text("Always run tests before commit.", encoding="utf-8")

    app = create_app()
    app.dependency_overrides[get_harvester] = lambda: KnowledgeHarvester(base)
    client = TestClient(app)

    payload = {
        "project_path": str(tmp_path),
        "include": ["CLAUDE.md"],
        "max_files": 50,
        "auto_confirm_threshold": 0.8,
    }

    preview = client.post("/harvest/preview", json=payload)
    assert preview.status_code == 200
    preview_data = preview.json()
    assert preview_data["candidates"] >= 1

    scan = client.post("/harvest/scan", json=payload)
    assert scan.status_code == 200
    scan_data = scan.json()
    assert scan_data["report_id"].startswith("harv_")

    report = client.get("/harvest/report", params={"id": scan_data["report_id"]})
    assert report.status_code == 200
    report_data = report.json()
    assert report_data["report_id"] == scan_data["report_id"]


def test_harvest_routes_require_allowlisted_project(tmp_path: Path) -> None:
    base = tmp_path / ".vibecode"
    base.mkdir()

    project = tmp_path / "project"
    project.mkdir()
    (project / "CLAUDE.md").write_text("Always test", encoding="utf-8")

    app = create_app()
    app.dependency_overrides[get_harvester] = lambda: KnowledgeHarvester(base)
    client = TestClient(app)

    response = client.post(
        "/harvest/scan",
        json={
            "project_path": str(project),
            "include": ["CLAUDE.md"],
        },
    )
    assert response.status_code == 403
    assert "PROJECT_NOT_ALLOWED" in response.text
