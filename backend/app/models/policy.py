from sqlalchemy import Column, Integer, String, Boolean, JSON
from app.db.base_class import Base

class Policy(Base):
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    effect = Column(String, nullable=False) # ALLOW, DENY, REQUIRE_APPROVAL
    priority = Column(Integer, default=100)
    is_enabled = Column(Boolean, default=True)
    
    # JSON field to store conditions (e.g., {"resource": "payment", "action": "refund", "max_amount": 500})
    conditions = Column(JSON, default=dict)
