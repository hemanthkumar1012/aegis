from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WorkloadIdentityBase(BaseModel):
    name: str
    description: Optional[str] = None
    owner: str
    environment: str
    trust_level: str = "LOW"

class WorkloadIdentityCreate(WorkloadIdentityBase):
    pass

class WorkloadIdentity(WorkloadIdentityBase):
    id: int
    status: str
    created_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True

class IdentityCredentialCreateResponse(BaseModel):
    client_id: str
    client_secret: str

class GatewayRequest(BaseModel):
    identity: str
    tool: str
    action: str
    resource: str
    parameters: dict = {}
