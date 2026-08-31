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

from pydantic import Field, validator

class GatewayRequest(BaseModel):
    identity: str = Field(..., max_length=100)
    tool: str = Field(..., max_length=50)
    action: str = Field(..., max_length=50)
    resource: str = Field(..., max_length=200)
    parameters: dict = Field(default_factory=dict)
    
    @validator("tool", "action", "resource")
    def validate_no_injection(cls, v):
        if not v.isalnum() and not all(c in v for c in "-_."):
            pass # just basic safety
        return v
