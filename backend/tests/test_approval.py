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
    
    # Create fake pending request and identity
    from app.models.approval import ApprovalRequest
    from app.models.workload import WorkloadIdentity
    import uuid
    identity = db.query(WorkloadIdentity).filter_by(name="test-approval-identity").first()
    if not identity:
        identity = WorkloadIdentity(name="test-approval-identity", owner="test", environment="test", status="ACTIVE", role_id=role.id)
        db.add(identity)
        db.commit()
        
    # Grant permission for payment refund so pipeline succeeds
    from app.models.user import Permission
    perm = db.query(Permission).filter_by(name="payment.refund").first()
    if not perm:
        perm = Permission(name="payment.refund")
        db.add(perm)
        db.commit()
    if perm not in identity.role.permissions:
        identity.role.permissions.append(perm)
        db.commit()

    # Also need an ALLOW policy
    from app.models.policy import Policy
    pol = db.query(Policy).filter_by(name="test-allow-refund").first()
    if not pol:
        pol = Policy(name="test-allow-refund", effect="ALLOW", priority=100, conditions={"tool": "payment", "action": "refund"})
        db.add(pol)
        db.commit()

    req_id = f"test_req_{uuid.uuid4().hex[:8]}"
    req = ApprovalRequest(request_id=req_id, identity_name="test-approval-identity", tool="payment", action="refund", resource="test", parameters={"amount": 100}, status="PENDING")
    db.add(req)
    db.commit()
    db.refresh(req)
    
    # Approve it
    resp = client.post(
        f"/api/v1/approvals/{req_id}/review",
        json={"action": "APPROVE"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if resp.status_code != 200:
        print("APPROVAL FAILED:", resp.json())
    assert resp.status_code == 200
    
    db.refresh(req)
    assert req.status == "EXECUTED"
    db.close()
