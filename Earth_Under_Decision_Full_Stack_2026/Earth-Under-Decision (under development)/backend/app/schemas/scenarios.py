from pydantic import BaseModel, Field


class ScenarioCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    indicator: str = Field(pattern="^(ndvi|lst|precipitation)$")
    study_area_id: str | None = None
    assumptions: dict = Field(default_factory=dict)
    baseline_reference: str | None = Field(default=None, max_length=200)


class ScenarioRead(BaseModel):
    id: str
    title: str
    indicator: str
    study_area_id: str | None
    assumptions: dict
    baseline_reference: str | None
    calculation_method: str | None
    status: str
    result: dict | None
