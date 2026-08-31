from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.base_class import Base

class ApprovalRequest(Base):
    __tablename__ = "approval_request"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True)
    identity_name = Column(String)
    tool = Column(String)
    action = Column(String)
    resource = Column(String)
    parameters = Column(JSON, default=dict)
    
    status = Column(String, default="PENDING") # PENDING, APPROVED, REJECTED, EXPIRED
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    approver_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
