from pydantic import BaseModel
from typing import Optional, Dict, Any

class PolicyBase(BaseModel):
    name: str
    description: Optional[str] = None
    effect: str
    priority: int = 100
    is_enabled: bool = True
    conditions: Dict[str, Any] = {}

class PolicyCreate(PolicyBase):
    pass

class Policy(PolicyBase):
    id: int

    class Config:
        from_attributes = True
