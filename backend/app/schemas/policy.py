from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any

class PolicyBase(BaseModel):
    name: str
    description: Optional[str] = None
    effect: str = Field(..., description="ALLOW, DENY, or REQUIRE_APPROVAL")
    priority: int = Field(100, ge=1, le=1000)
    is_enabled: bool = True
    conditions: Dict[str, Any] = {}

    @field_validator("effect")
    @classmethod
    def validate_effect(cls, v):
        if v not in ["ALLOW", "DENY", "REQUIRE_APPROVAL"]:
            raise ValueError("Effect must be ALLOW, DENY, or REQUIRE_APPROVAL")
        return v
        
    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Conditions must be a dictionary")
        # Validate safe fields
        allowed_keys = {"identity", "role", "tool", "action", "resource", "environment", "max_amount", "min_amount", "min_trust_level", "time_start", "time_end", "ip_range"}
        for key in v.keys():
            if key not in allowed_keys:
                raise ValueError(f"Unsupported condition key: {key}")
        return v

class PolicyCreate(PolicyBase):
    pass

class Policy(PolicyBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
