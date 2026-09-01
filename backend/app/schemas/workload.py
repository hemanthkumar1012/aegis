from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)

class IdentityCredentialCreateResponse(BaseModel):
    client_id: str
    client_secret: str

import re
from pydantic import Field, field_validator, ValidationInfo

IDENTIFIER_REGEX = re.compile(r"\A[A-Za-z0-9._-]+\Z")

def validate_identifier(value: str, field_name: str) -> str:
    if not IDENTIFIER_REGEX.match(value):
        raise ValueError(f"Invalid identifier for {field_name}. Must contain only alphanumeric characters, dots, underscores, and hyphens.")
    return value

class GatewayRequest(BaseModel):
    identity: str = Field(..., max_length=100)
    tool: str = Field(..., max_length=50)
    action: str = Field(..., max_length=50)
    resource: str = Field(..., max_length=200)
    parameters: dict = Field(default_factory=dict)
    
    @field_validator("identity", "tool", "action", "resource")
    @classmethod
    def validate_no_injection(cls, v: str, info: ValidationInfo) -> str:
        return validate_identifier(v, info.field_name or "field")
