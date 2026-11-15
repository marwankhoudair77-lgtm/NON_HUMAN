from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Scenario, StudyArea
from app.schemas.scenarios import ScenarioCreate

router = APIRouter(tags=["scenarios"])


@router.post("/scenarios")
def create_scenario(payload: ScenarioCreate, db: Session = Depends(get_db)):
    if payload.study_area_id and db.get(StudyArea, payload.study_area_id) is None:
        raise HTTPException(404, detail={"code": "study_area_not_found", "message": "Study area not found."})
    scenario = Scenario(
        title=payload.title,
        indicator=payload.indicator,
        study_area_id=payload.study_area_id,
        assumptions=payload.assumptions,
        baseline_reference=payload.baseline_reference,
        calculation_method=None,
        status="illustrative_only",
        result=None,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return {
        "id": scenario.id,
        "title": scenario.title,
        "indicator": scenario.indicator,
        "study_area_id": scenario.study_area_id,
        "assumptions": scenario.assumptions,
        "baseline_reference": scenario.baseline_reference,
        "calculation_method": None,
        "status": "illustrative_only",
        "result": None,
        "message": "Scenario assumptions were stored only. No environmental calculation or forecast was performed.",
    }


@router.get("/scenarios/{scenario_id}")
def get_scenario(scenario_id: str, db: Session = Depends(get_db)):
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(404, detail={"code": "scenario_not_found", "message": "Scenario not found."})
    return {
        "id": scenario.id,
        "title": scenario.title,
        "indicator": scenario.indicator,
        "study_area_id": scenario.study_area_id,
        "assumptions": scenario.assumptions,
        "baseline_reference": scenario.baseline_reference,
        "calculation_method": scenario.calculation_method,
        "status": scenario.status,
        "result": scenario.result,
    }


@router.get("/scenarios/{scenario_id}/results")
def get_scenario_results(scenario_id: str, db: Session = Depends(get_db)):
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise HTTPException(404, detail={"code": "scenario_not_found", "message": "Scenario not found."})
    return {
        "scenario_id": scenario.id,
        "status": "illustrative_only",
        "result": None,
        "message": "No validated model is configured. This scenario is not a forecast.",
    }
