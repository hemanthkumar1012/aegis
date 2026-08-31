from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ApprovalRequestSchema(BaseModel):
    id: int
    request_id: str
    identity_name: str
    tool: str
    action: str
    resource: str
    parameters: dict
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ApprovalAction(BaseModel):
    action: str # "APPROVE" or "REJECT"
