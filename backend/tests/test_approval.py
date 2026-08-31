import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal

client = TestClient(app)

def test_approval_flow():
    # Setup user
    from app.models.user import User, Role
    db = SessionLocal()
    role = db.query(Role).filter_by(name="ADMIN").first()
    if not role:
        role = Role(name="ADMIN")
        db.add(role)
        db.commit()
    user = db.query(User).filter_by(email="admin_approver@aegis.local").first()
    if not user:
        from app.core.security import get_password_hash
        user = User(email="admin_approver@aegis.local", hashed_password=get_password_hash("pass"), role_id=role.id)
        db.add(user)
        db.commit()
        
    from app.core.security import create_access_token
    token = create_access_token(subject=user.email)
    
    # Create fake pending request
    from app.models.approval import ApprovalRequest
    import uuid
    req_id = f"test_req_{uuid.uuid4().hex[:8]}"
    req = ApprovalRequest(request_id=req_id, identity_name="test-identity", tool="payment", action="refund", resource="test", status="PENDING")
    db.add(req)
    db.commit()
    db.refresh(req)
    
    # Approve it
    resp = client.post(
        f"/api/v1/approvals/{req_id}/review",
        json={"action": "APPROVE"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert resp.status_code == 200
    
    db.refresh(req)
    assert req.status == "EXECUTED"
    db.close()
