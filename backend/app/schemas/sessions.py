from datetime import datetime

from typing import Literal

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
    explanation: list[str]


class ModeVector(BaseModel):
    power: float
    speed: float
    frequency: float
    pressure: float
    focus: float
    height: float
    duty_cycle: float
    nozzle: float


class BaseModeRead(BaseModel):
    power: float
    speed: float
    frequency: float
    pressure: float
    focus: float
    height: float
    duty_cycle: float
    nozzle: float
    explanation: str


class RecommendationRequest(BaseModel):
    defect_code: str
    severity_level: int = Field(ge=0, le=3)
    current_mode: ModeVector


RuleParameter = Literal[
    "power",
    "speed",
    "frequency",
    "pressure",
    "focus",
    "height",
    "duty_cycle",
    "nozzle",
]
RuleDirection = Literal["increase", "decrease"]


class RecommendationRuleCreate(BaseModel):
    defect_code: str
    parameter: RuleParameter
    direction: RuleDirection
    base_delta: float = Field(gt=0)
    is_active: bool = True


class RecommendationRuleUpdate(BaseModel):
    parameter: RuleParameter | None = None
    direction: RuleDirection | None = None
    base_delta: float | None = Field(default=None, gt=0)
    is_active: bool | None = None


class RecommendationRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    defect_code: str
    parameter: RuleParameter
    direction: RuleDirection
    base_delta: float
    is_active: bool
