import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.workload import WorkloadIdentity, IdentityCredential
from app.schemas.workload import WorkloadIdentityCreate, WorkloadIdentity as WorkloadIdentitySchema, IdentityCredentialCreateResponse
from app.core.security import get_password_hash
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=WorkloadIdentitySchema)
def create_workload_identity(
    *,
    db: Session = Depends(deps.get_db),
    workload_in: WorkloadIdentityCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    # Need admin check here ideally. Skipping full RBAC check for simplicity of scaffolding
    identity = db.query(WorkloadIdentity).filter(WorkloadIdentity.name == workload_in.name).first()
    if identity:
        raise HTTPException(status_code=400, detail="Identity already exists.")
    
    identity = WorkloadIdentity(
        name=workload_in.name,
        description=workload_in.description,
        owner=workload_in.owner,
        environment=workload_in.environment,
        trust_level=workload_in.trust_level,
        status="ACTIVE"
    )
    db.add(identity)
    db.commit()
    db.refresh(identity)
    return identity

@router.get("/", response_model=List[WorkloadIdentitySchema])
def read_identities(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return db.query(WorkloadIdentity).all()

@router.post("/{identity_id}/credentials", response_model=IdentityCredentialCreateResponse)
def create_credential(
    *,
    db: Session = Depends(deps.get_db),
    identity_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    identity = db.query(WorkloadIdentity).filter(WorkloadIdentity.id == identity_id).first()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    raw_secret = str(uuid.uuid4())
    client_id = f"aegis_{uuid.uuid4().hex[:16]}"
    hashed_secret = get_password_hash(raw_secret)
    
    credential = IdentityCredential(
        identity_id=identity.id,
        client_id=client_id,
        hashed_secret=hashed_secret
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)
    
    return {"client_id": client_id, "client_secret": raw_secret}

@router.put("/{identity_id}/suspend", response_model=WorkloadIdentitySchema)
def suspend_identity(
    *,
    db: Session = Depends(deps.get_db),
    identity_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    identity = db.query(WorkloadIdentity).filter(WorkloadIdentity.id == identity_id).first()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    identity.status = "SUSPENDED"
    db.commit()
    db.refresh(identity)
    return identity

@router.put("/{identity_id}/reactivate", response_model=WorkloadIdentitySchema)
def reactivate_identity(
    *,
    db: Session = Depends(deps.get_db),
    identity_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    identity = db.query(WorkloadIdentity).filter(WorkloadIdentity.id == identity_id).first()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    identity.status = "ACTIVE"
    db.commit()
    db.refresh(identity)
    return identity
