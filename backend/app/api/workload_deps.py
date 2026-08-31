from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.models.workload import WorkloadIdentity, IdentityCredential
from app.core.security import verify_password

def get_current_workload(
    x_client_id: str = Header(...),
    x_client_secret: str = Header(...),
    db: Session = Depends(get_db)
) -> WorkloadIdentity:
    from datetime import datetime, timezone
    from app.models.audit import SecurityEvent
    
    now = datetime.now(timezone.utc)
    
    def log_invalid_auth(reason: str):
        evt = SecurityEvent(
            event_type="INVALID_AUTHENTICATION",
            severity="HIGH",
            description=reason,
            source_identity=x_client_id,
            timestamp=now
        )
        db.add(evt)
        db.commit()

    # Fetch the credential by client_id
    cred = db.query(IdentityCredential).filter(IdentityCredential.client_id == x_client_id).first()
    if not cred:
        log_invalid_auth("Unknown client ID")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials")
        
    if not verify_password(x_client_secret, cred.hashed_secret):
        log_invalid_auth("Invalid client secret")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client credentials")

    # Enforce Expiration and Rotation semantics
    if not cred.is_active:
        log_invalid_auth("Credential is not active (rotated)")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credential is inactive")
        
    if cred.revoked_at is not None:
        log_invalid_auth("Credential was revoked")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credential is revoked")
        
    if cred.expires_at is not None and cred.expires_at.tzinfo is None:
        # Make it aware if somehow naive
        cred.expires_at = cred.expires_at.replace(tzinfo=timezone.utc)
        
    if cred.expires_at is not None and now >= cred.expires_at:
        log_invalid_auth("Credential has expired")
        
        # Log credential expiry explicitly as an event
        evt = SecurityEvent(
            event_type="CREDENTIAL_EXPIRED",
            severity="MEDIUM",
            description=f"Credential {cred.client_id} expired at {cred.expires_at}",
            source_identity=cred.identity.name if cred.identity else x_client_id,
            timestamp=now
        )
        db.add(evt)
        db.commit()
        
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credential has expired")
        
    identity = cred.identity
    if identity.status != "ACTIVE":
        # Do not log as invalid auth, log as suspended access attempt
        evt = SecurityEvent(
            event_type="SUSPENDED_ACCESS_ATTEMPT",
            severity="HIGH",
            description="Attempt to access with suspended identity",
            source_identity=identity.name,
            timestamp=now
        )
        db.add(evt)
        db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Identity is suspended")
        
    return identity
