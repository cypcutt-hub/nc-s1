from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.db.session import SessionLocal, get_db
from app.models import CutIteration, CutSession

app = FastAPI(title="NeuroCut API")


class SessionCreate(BaseModel):
    machine_name: str
    material_group: str
    thickness_mm: float
    gas_branch: str


class SessionRead(SessionCreate):
    id: int
    created_at: datetime


class IterationCreate(BaseModel):
    session_id: int
    step_number: int
    defect_code: str
    severity_level: int
    power_before: float
    speed_before: float
    focus_before: float
    pressure_before: float
    power_after: float
    speed_after: float
    focus_after: float
    pressure_after: float


class IterationRead(IterationCreate):
    id: int
    created_at: datetime


class SessionWithIterations(SessionRead):
    iterations: list[IterationRead]


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/db-health")
def db_health_check() -> dict[str, str]:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc


@app.post("/sessions", response_model=SessionRead)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> SessionRead:
    session = CutSession(**payload.model_dump())
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionRead.model_validate(session, from_attributes=True)


@app.get("/sessions/{session_id}", response_model=SessionWithIterations)
def get_session(session_id: int, db: Session = Depends(get_db)) -> SessionWithIterations:
    session = (
        db.query(CutSession)
        .options(selectinload(CutSession.iterations))
        .filter(CutSession.id == session_id)
        .first()
    )
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    return SessionWithIterations.model_validate(session, from_attributes=True)


@app.post("/iterations", response_model=IterationRead)
def create_iteration(payload: IterationCreate, db: Session = Depends(get_db)) -> IterationRead:
    if db.query(CutSession.id).filter(CutSession.id == payload.session_id).first() is None:
        raise HTTPException(status_code=404, detail="session not found")

    iteration = CutIteration(**payload.model_dump())
    db.add(iteration)
    db.commit()
    db.refresh(iteration)
    return IterationRead.model_validate(iteration, from_attributes=True)
