from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from vibecode.api.schemas import HarvestReportResponse, HarvestScanRequest, HarvestScanResponse
from vibecode.harvest.service import KnowledgeHarvester

router = APIRouter()


def get_harvester() -> KnowledgeHarvester:
    # Instantiate per request to avoid cross-thread sqlite issues in FastAPI.
    return KnowledgeHarvester()


@router.post("/harvest/scan", response_model=HarvestScanResponse)
def harvest_scan(request: HarvestScanRequest, harvester: KnowledgeHarvester = Depends(get_harvester)) -> dict:
    result = harvester.scan(
        project_path=request.project_path,
        include=request.include or None,
        exclude=request.exclude or None,
        max_files=request.max_files,
        auto_confirm_threshold=request.auto_confirm_threshold,
        dry_run=False,
    )
    if "error" in result:
        raise HTTPException(status_code=403, detail=result)
    return result


@router.post("/harvest/preview", response_model=HarvestScanResponse)
def harvest_preview(request: HarvestScanRequest, harvester: KnowledgeHarvester = Depends(get_harvester)) -> dict:
    result = harvester.scan(
        project_path=request.project_path,
        include=request.include or None,
        exclude=request.exclude or None,
        max_files=request.max_files,
        auto_confirm_threshold=request.auto_confirm_threshold,
        dry_run=True,
    )
    if "error" in result:
        raise HTTPException(status_code=403, detail=result)
    return result


@router.get("/harvest/report", response_model=HarvestReportResponse)
def harvest_report(id: str | None = None, harvester: KnowledgeHarvester = Depends(get_harvester)) -> dict:
    return harvester.read_report(id)
