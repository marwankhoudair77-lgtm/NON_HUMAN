from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import require_admin_token
from app.db.session import get_db
from app.models import ProcessingJob, ProcessingRun

router = APIRouter(tags=["jobs"])


@router.post("/ingestion/jobs", dependencies=[Depends(require_admin_token)])
def request_ingestion_job(payload: dict):
    source_key = payload.get("source_key")
    raise HTTPException(
        status_code=501,
        detail={
            "code": "source_connector_not_implemented",
            "message": "No verified automatic acquisition connector is enabled. Use the authorized manual upload workflow; this request did not start a download.",
            "source_key": source_key,
        },
    )


@router.get("/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise HTTPException(404, detail={"code": "job_not_found", "message": "Job not found."})
    return job


@router.post("/processing/jobs", dependencies=[Depends(require_admin_token)])
def request_processing_job(payload: dict):
    operation = payload.get("operation")
    raise HTTPException(
        status_code=501,
        detail={
            "code": "processing_worker_not_configured",
            "message": "Product-specific QA and raster processing are not enabled until the source product, QA rules, and a processing worker are verified. No processing job was created.",
            "requested_operation": operation,
        },
    )


@router.get("/processing/jobs/{job_id}")
def get_processing_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise HTTPException(404, detail={"code": "job_not_found", "message": "Processing job not found."})
    return job


@router.post("/jobs/{job_id}/cancel", dependencies=[Depends(require_admin_token)])
def cancel_job(job_id: str, db: Session = Depends(get_db)):
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise HTTPException(404, detail={"code": "job_not_found", "message": "Job not found."})
    if job.status not in {"queued", "requested"}:
        raise HTTPException(409, detail={"code": "job_not_cancellable", "message": "Only queued jobs can be cancelled by this API version."})
    job.status = "cancelled"
    job.message = "Cancelled by an authorized operator."
    db.commit()
    db.refresh(job)
    return job


@router.get("/processing/runs/{run_id}")
def get_processing_run(run_id: str, db: Session = Depends(get_db)):
    run = db.get(ProcessingRun, run_id)
    if run is None:
        raise HTTPException(404, detail={"code": "processing_run_not_found", "message": "Processing run not found."})
    return run
