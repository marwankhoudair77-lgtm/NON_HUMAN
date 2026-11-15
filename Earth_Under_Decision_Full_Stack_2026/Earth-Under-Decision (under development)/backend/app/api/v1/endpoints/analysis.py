from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import AnalysisResult, AnalysisRun, TimeSeriesValue

router = APIRouter(tags=["analysis"])


@router.get("/trends")
def get_trends(
    indicator: str = Query(pattern="^(ndvi|lst|precipitation)$"),
    study_area_id: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    db: Session = Depends(get_db),
):
    query = (
        select(TimeSeriesValue, AnalysisRun)
        .join(AnalysisRun, TimeSeriesValue.analysis_run_id == AnalysisRun.id)
        .where(TimeSeriesValue.indicator == indicator, AnalysisRun.status == "completed")
    )
    if study_area_id:
        query = query.where(TimeSeriesValue.study_area_id == study_area_id)
    if start:
        query = query.where(TimeSeriesValue.interval_start >= start)
    if end:
        query = query.where(TimeSeriesValue.interval_start <= end)
    rows = db.execute(query.order_by(TimeSeriesValue.interval_start)).all()
    rows = [
        (value, run) for value, run in rows
        if run.provenance.get("input_assets_scientifically_validated") is True
        and run.provenance.get("product_qa_applied") is True
        and run.provenance.get("time_axis_reviewed") is True
    ]
    if not rows:
        return {
            "data_status": "unavailable",
            "indicator": indicator,
            "study_area_id": study_area_id,
            "series": [],
            "trend_statistics": None,
            "message": "No completed analysis run with scientifically validated inputs, product QA, and reviewed time semantics is available for the requested filters.",
        }
    series = [
        {
            "date": value.interval_start.isoformat(),
            "interval_end": value.interval_end.isoformat() if value.interval_end else None,
            "value": value.value,
            "units": value.units,
            "valid_pixel_count": value.valid_pixel_count,
            "missing_pixel_count": value.missing_pixel_count,
            "quality_summary": value.quality_summary,
        }
        for value, _run in rows
    ]
    run_ids = sorted({run.id for _value, run in rows})
    results = db.scalars(select(AnalysisResult).where(AnalysisResult.analysis_run_id.in_(run_ids))).all()
    return {
        "data_status": "available",
        "indicator": indicator,
        "study_area_id": study_area_id,
        "series": series,
        "trend_statistics": [
            {"result_type": item.result_type, "value": item.value, "unit": item.unit, "p_value": item.p_value, "confidence_interval": item.confidence_interval, "sample_size": item.sample_size, "details": item.details}
            for item in results
        ],
    }


@router.get("/comparisons")
def get_comparisons(indicator: str = Query(pattern="^(ndvi|lst|precipitation)$")):
    return {
        "data_status": "unavailable",
        "indicator": indicator,
        "items": [],
        "message": "Area comparisons require validated boundaries and compatible, quality-screened observations.",
    }


@router.get("/analysis/runs/{run_id}")
def get_analysis_run(run_id: str, db: Session = Depends(get_db)):
    run = db.get(AnalysisRun, run_id)
    if run is None:
        from fastapi import HTTPException
        raise HTTPException(404, detail={"code": "analysis_run_not_found", "message": "Analysis run not found."})
    results = db.scalars(select(AnalysisResult).where(AnalysisResult.analysis_run_id == run_id)).all()
    return {"run": run, "results": results}


@router.get("/analysis/results/{result_id}")
def get_analysis_result(result_id: str, db: Session = Depends(get_db)):
    row = db.get(AnalysisResult, result_id)
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(404, detail={"code": "analysis_result_not_found", "message": "Analysis result not found."})
    return row
