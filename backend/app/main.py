from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.models import CutIteration, CutSession, Defect
from app.schemas import (
    CutIterationCreate,
    CutIterationRead,
    CutSessionCreate,
    CutSessionRead,
    CutSessionReadWithIterations,
    RecommendationRequest,
    RecommendationRead,
)
from app.services import build_recommendation, build_recommendation_from_iteration

app = FastAPI(title="NeuroCut API")


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


@app.post("/sessions", response_model=CutSessionRead, status_code=201)
def create_session(payload: CutSessionCreate) -> CutSession:
    with SessionLocal() as db:
        session = CutSession(
            machine_name=payload.machine_name,
            material_group=payload.material_group,
            thickness_mm=payload.thickness_mm,
            gas_branch=payload.gas_branch,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session


@app.get("/sessions/{session_id}", response_model=CutSessionReadWithIterations)
def get_session(session_id: int) -> CutSession:
    with SessionLocal() as db:
        session = db.get(CutSession, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="session not found")

        session.iterations.sort(key=lambda iteration: iteration.step_number)
        return session


@app.post("/sessions/{session_id}/iterations", response_model=CutIterationRead, status_code=201)
def add_iteration(session_id: int, payload: CutIterationCreate) -> CutIteration:
    with SessionLocal() as db:
        session = db.get(CutSession, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="session not found")

        defect = db.query(Defect).filter(Defect.code == payload.defect_code).first()
        if defect is None:
            raise HTTPException(status_code=400, detail="unknown defect_code")

        iteration = CutIteration(session_id=session_id, **payload.model_dump())
        db.add(iteration)
        db.commit()
        db.refresh(iteration)
        return iteration


@app.post("/sessions/{session_id}/recommend", response_model=RecommendationRead)
def recommend_next_mode(
    session_id: int, payload: RecommendationRequest | None = None
) -> RecommendationRead:
    with SessionLocal() as db:
        session = db.get(CutSession, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="session not found")

        if payload is not None:
            defect = db.query(Defect).filter(Defect.code == payload.defect_code).first()
            if defect is None:
                raise HTTPException(status_code=400, detail="unknown defect_code")

            return build_recommendation(
                db=db,
                defect_code=payload.defect_code,
                severity_level=payload.severity_level,
                current_mode=payload.current_mode.model_dump(),
                session=session,
            )

        last_iteration = (
            db.query(CutIteration)
            .filter(CutIteration.session_id == session_id)
            .order_by(CutIteration.step_number.desc())
            .first()
        )
        if last_iteration is None:
            raise HTTPException(status_code=400, detail="session has no iterations")

        return build_recommendation_from_iteration(last_iteration, session, db)
