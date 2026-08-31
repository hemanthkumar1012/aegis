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
    identity = db.query(WorkloadIdentity).filter(WorkloadIdentity.name == x_client_id).first()
    if not identity:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client ID")
    
    if identity.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Identity is suspended")
        
    # Check credentials
    valid = False
    for cred in identity.credentials:
        if cred.is_active and verify_password(x_client_secret, cred.hashed_secret):
            valid = True
            break
            
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client secret")
        
    return identity
