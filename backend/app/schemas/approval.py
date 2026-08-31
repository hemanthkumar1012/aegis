from pydantic import BaseModel
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
    
    class Config:
        from_attributes = True

class ApprovalAction(BaseModel):
    action: str # "APPROVE" or "REJECT"
