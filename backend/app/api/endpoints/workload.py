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
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
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
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    return db.query(WorkloadIdentity).all()

@router.post("/{identity_id}/credentials", response_model=IdentityCredentialCreateResponse)
def create_credential(
    *,
    db: Session = Depends(deps.get_db),
    identity_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    from datetime import datetime, timedelta, timezone
    from app.core.config import settings
    from app.models.audit import SecurityEvent
    
    identity = db.query(WorkloadIdentity).filter(WorkloadIdentity.id == identity_id).first()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
        
    now = datetime.now(timezone.utc)
    
    # Revoke old active credentials (rotation semantics)
    old_credentials = db.query(IdentityCredential).filter(
        IdentityCredential.identity_id == identity.id,
        IdentityCredential.is_active == True
    ).all()
    
    for old_cred in old_credentials:
        old_cred.is_active = False
        old_cred.revoked_at = now
        
        # Audit revocation
        evt = SecurityEvent(
            event_type="CREDENTIAL_REVOKED",
            severity="MEDIUM",
            description=f"Credential {old_cred.client_id} rotated and revoked.",
            source_identity=identity.name,
            timestamp=now
        )
        db.add(evt)
    
    raw_secret = str(uuid.uuid4())
    client_id = f"aegis_{uuid.uuid4().hex[:16]}"
    hashed_secret = get_password_hash(raw_secret)
    
    expires = now + timedelta(days=settings.CREDENTIAL_TTL_DAYS)
    
    credential = IdentityCredential(
        identity_id=identity.id,
        client_id=client_id,
        hashed_secret=hashed_secret,
        is_active=True,
        issued_at=now,
        expires_at=expires
    )
    db.add(credential)
    
    # Audit creation
    evt_create = SecurityEvent(
        event_type="CREDENTIAL_CREATED",
        severity="INFO",
        description=f"New credential {client_id} created, expires {expires.isoformat()}.",
        source_identity=identity.name,
        timestamp=now
    )
    db.add(evt_create)
    
    db.commit()
    db.refresh(credential)
    
    return {"client_id": client_id, "client_secret": raw_secret}

@router.put("/{identity_id}/suspend", response_model=WorkloadIdentitySchema)
def suspend_identity(
    *,
    db: Session = Depends(deps.get_db),
    identity_id: int,
    current_user: User = Depends(deps.get_current_admin_user),
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
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    identity = db.query(WorkloadIdentity).filter(WorkloadIdentity.id == identity_id).first()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    
    identity.status = "ACTIVE"
    db.commit()
    db.refresh(identity)
    return identity
