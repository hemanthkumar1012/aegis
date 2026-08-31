from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.models.audit import AuditLog, SecurityEvent
from app.models.user import User
from app.core.ml_engine import MLEngine

router = APIRouter()

@router.get("/logs")
def read_audit_logs(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

@router.get("/security-events")
def read_security_events(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = 0,
    limit: int = 100
) -> Any:
    return db.query(SecurityEvent).order_by(SecurityEvent.timestamp.desc()).offset(skip).limit(limit).all()

@router.get("/risk/{identity_name}")
def get_identity_risk(
    identity_name: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    ml_engine = MLEngine(db)
    result = ml_engine.detect_anomaly(identity_name)
    return result
