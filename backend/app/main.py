from fastapi import FastAPI, HTTPException
from sqlalchemy import text, func
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.models import (
    BaseMode,
    CutIteration,
    CutSession,
    Defect,
    Material,
    RecommendationRule,
)
from app.schemas import (
    CutIterationCreate,
    CutIterationRead,
    BaseModeRead,
    CutSessionCreate,
    CutSessionRead,
    CutSessionReadWithIterations,
    RecommendationRequest,
    RecommendationRead,
    RecommendationRuleCreate,
    RecommendationRuleRead,
    RecommendationRuleUpdate,
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


@app.get("/sessions/{session_id}/base-mode", response_model=BaseModeRead)
def get_base_mode(session_id: int) -> BaseModeRead:
    with SessionLocal() as db:
        session = db.get(CutSession, session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="session not found")

        exact_mode = (
            db.query(BaseMode)
            .join(Material, BaseMode.material_id == Material.id)
            .filter(
                Material.material_group == session.material_group,
                BaseMode.gas_type == session.gas_branch,
                BaseMode.thickness_mm == session.thickness_mm,
            )
            .order_by(BaseMode.id.asc())
            .first()
        )
        if exact_mode is not None:
            return BaseModeRead(
                power=exact_mode.power_percent,
                speed=exact_mode.speed_m_min,
                frequency=exact_mode.frequency_hz or 0.0,
                pressure=exact_mode.pressure_bar,
                focus=exact_mode.focus_mm,
                height=exact_mode.cutting_height_mm,
                duty_cycle=exact_mode.duty_cycle_percent or 0.0,
                nozzle=exact_mode.nozzle_diameter_mm,
                explanation="Exact match used",
            )

        nearest_mode = (
            db.query(BaseMode)
            .join(Material, BaseMode.material_id == Material.id)
            .filter(
                Material.material_group == session.material_group,
                BaseMode.gas_type == session.gas_branch,
            )
            .order_by(
                func.abs(BaseMode.thickness_mm - session.thickness_mm).asc(),
                BaseMode.id.asc(),
            )
            .first()
        )
        if nearest_mode is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"base mode not found for material_group={session.material_group}, "
                    f"gas_branch={session.gas_branch}"
                ),
            )

        return BaseModeRead(
            power=nearest_mode.power_percent,
            speed=nearest_mode.speed_m_min,
            frequency=nearest_mode.frequency_hz or 0.0,
            pressure=nearest_mode.pressure_bar,
            focus=nearest_mode.focus_mm,
            height=nearest_mode.cutting_height_mm,
            duty_cycle=nearest_mode.duty_cycle_percent or 0.0,
            nozzle=nearest_mode.nozzle_diameter_mm,
            explanation=(
                f"Nearest thickness {nearest_mode.thickness_mm:g} used instead of "
                f"{session.thickness_mm:g}"
            ),
        )


@app.post(
    "/sessions/{session_id}/iterations",
    response_model=CutIterationRead,
    status_code=201,
)
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


@app.get("/rules", response_model=list[RecommendationRuleRead])
def list_rules() -> list[RecommendationRule]:
    with SessionLocal() as db:
        return db.query(RecommendationRule).order_by(RecommendationRule.id.asc()).all()


@app.post("/rules", response_model=RecommendationRuleRead, status_code=201)
def create_rule(payload: RecommendationRuleCreate) -> RecommendationRule:
    with SessionLocal() as db:
        defect = db.query(Defect).filter(Defect.code == payload.defect_code).first()
        if defect is None:
            raise HTTPException(status_code=400, detail="unknown defect_code")

        rule = RecommendationRule(**payload.model_dump())
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule


@app.patch("/rules/{rule_id}", response_model=RecommendationRuleRead)
def update_rule(rule_id: int, payload: RecommendationRuleUpdate) -> RecommendationRule:
    with SessionLocal() as db:
        rule = db.get(RecommendationRule, rule_id)
        if rule is None:
            raise HTTPException(status_code=404, detail="rule not found")

        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(rule, field, value)

        db.commit()
        db.refresh(rule)
        return rule


@app.delete("/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: int) -> None:
    with SessionLocal() as db:
        rule = db.get(RecommendationRule, rule_id)
        if rule is None:
            raise HTTPException(status_code=404, detail="rule not found")

        db.delete(rule)
        db.commit()
