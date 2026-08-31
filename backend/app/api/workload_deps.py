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
    # Fetch the credential by client_id
    cred = db.query(IdentityCredential).filter(IdentityCredential.client_id == x_client_id).first()
    if not cred or not cred.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or inactive client credentials")
        
    identity = cred.identity
    if identity.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Identity is suspended")
        
    if not verify_password(x_client_secret, cred.hashed_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid client secret")
        
    return identity
