from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class WorkloadIdentity(Base):
    __tablename__ = "workload_identity"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    owner = Column(String)
    environment = Column(String)
    trust_level = Column(String, default="LOW")
    status = Column(String, default="ACTIVE") # ACTIVE, SUSPENDED
    role_id = Column(Integer, ForeignKey("role.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    credentials = relationship("IdentityCredential", back_populates="identity")
    role = relationship("Role")


class IdentityCredential(Base):
    __tablename__ = "identity_credential"

    id = Column(Integer, primary_key=True, index=True)
    identity_id = Column(Integer, ForeignKey("workload_identity.id"))
    client_id = Column(String, unique=True, index=True, nullable=False)
    hashed_secret = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    identity = relationship("WorkloadIdentity", back_populates="credentials")
