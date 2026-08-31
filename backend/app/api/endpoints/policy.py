from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.models.policy import Policy
from app.schemas.policy import PolicyCreate, Policy as PolicySchema
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=PolicySchema)
def create_policy(
    *,
    db: Session = Depends(deps.get_db),
    policy_in: PolicyCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    policy = Policy(
        name=policy_in.name,
        description=policy_in.description,
        effect=policy_in.effect,
        priority=policy_in.priority,
        is_enabled=policy_in.is_enabled,
        conditions=policy_in.conditions
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy

@router.get("/", response_model=List[PolicySchema])
def read_policies(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return db.query(Policy).all()
