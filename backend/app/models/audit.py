from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from app.db.base_class import Base

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True)
    identity_name = Column(String, index=True)
    tool = Column(String, index=True)
    action = Column(String, index=True)
    resource = Column(String)
    decision = Column(String) # ALLOW, DENY, REQUIRE_APPROVAL
    policy_applied = Column(String, nullable=True)
    risk_score = Column(Float, nullable=True)
    anomaly_score = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    request_metadata = Column(JSON, default=dict)

class SecurityEvent(Base):
    __tablename__ = "security_event"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True) # AUTHENTICATION_FAILURE, UNAUTHORIZED_ACCESS, etc.
    severity = Column(String) # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(String)
    source_identity = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    details = Column(JSON, default=dict)
