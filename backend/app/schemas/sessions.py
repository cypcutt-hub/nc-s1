from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CutSessionCreate(BaseModel):
    machine_name: str
    material_group: str
    thickness_mm: float = Field(gt=0)
    gas_branch: str


class CutSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    machine_name: str
    material_group: str
    thickness_mm: float
    gas_branch: str
    created_at: datetime


class CutIterationCreate(BaseModel):
    step_number: int
    defect_code: str
    severity_level: int = Field(ge=0, le=3)

    power_before: float
    speed_before: float
    frequency_before: float
    pressure_before: float
    focus_before: float
    height_before: float
    duty_cycle_before: float
    nozzle_before: float

    power_after: float
    speed_after: float
    frequency_after: float
    pressure_after: float
    focus_after: float
    height_after: float
    duty_cycle_after: float
    nozzle_after: float


class CutIterationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    step_number: int
    defect_code: str
    severity_level: int

    power_before: float
    speed_before: float
    frequency_before: float
    pressure_before: float
    focus_before: float
    height_before: float
    duty_cycle_before: float
    nozzle_before: float

    power_after: float
    speed_after: float
    frequency_after: float
    pressure_after: float
    focus_after: float
    height_after: float
    duty_cycle_after: float
    nozzle_after: float

    created_at: datetime


class CutSessionReadWithIterations(CutSessionRead):
    iterations: list[CutIterationRead]


class RecommendationRead(BaseModel):
    power_after: float
    speed_after: float
    frequency_after: float
    pressure_after: float
    focus_after: float
    height_after: float
    duty_cycle_after: float
    nozzle_after: float
