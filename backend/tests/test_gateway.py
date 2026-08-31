import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.workload import WorkloadIdentity, IdentityCredential
from app.core.security import get_password_hash
from app.models.policy import Policy

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def setup_test_data(db_session):
    # Setup Role and Permissions
    from app.models.user import Role, Permission
    role = db_session.query(Role).filter_by(name="test-role").first()
    if not role:
        role = Role(name="test-role")
        db_session.add(role)
        db_session.commit()
    
    perm = db_session.query(Permission).filter_by(name="database.read").first()
    if not perm:
        perm = Permission(name="database.read")
        db_session.add(perm)
        db_session.commit()
        
    role.permissions.append(perm)
    db_session.commit()

    # Setup test identity
    client_name = "test-identity"
    raw_secret = "test-secret"
    client_id = "aegis_test1234"
    
    identity = db_session.query(WorkloadIdentity).filter_by(name=client_name).first()
    if not identity:
        identity = WorkloadIdentity(name=client_name, owner="test", environment="test", status="ACTIVE", role_id=role.id)
        db_session.add(identity)
        db_session.commit()
        db_session.refresh(identity)
        
        cred = IdentityCredential(identity_id=identity.id, client_id=client_id, hashed_secret=get_password_hash(raw_secret))
        db_session.add(cred)
        db_session.commit()

    # Setup explicit ALLOW policy for testing
    pol = db_session.query(Policy).filter_by(name="test-allow-read").first()
    if not pol:
        pol = Policy(name="test-allow-read", effect="ALLOW", priority=100, conditions={"identity": client_name, "tool": "database", "action": "read"})
        db_session.add(pol)
        db_session.commit()
        
    return {"client_id_header": client_id, "client_name": client_name, "client_secret": raw_secret}

def test_gateway_unauthorized(setup_test_data):
    response = client.post(
        "/api/v1/gateway/execute",
        headers={"x-client-id": "wrong", "x-client-secret": "wrong"},
        json={"identity": "wrong", "tool": "database", "action": "read", "resource": "db1"}
    )
    assert response.status_code == 401

def test_gateway_rbac_deny(setup_test_data):
    creds = setup_test_data
    # tool/action not in Role permissions
    response = client.post(
        "/api/v1/gateway/execute",
        headers={"x-client-id": creds["client_id_header"], "x-client-secret": creds["client_secret"]},
        json={"identity": creds["client_name"], "tool": "payment", "action": "refund", "resource": "res1"}
    )
    assert response.status_code == 403
    assert "Missing RBAC" in response.json()["detail"]["reason"]

def test_gateway_allow(setup_test_data):
    creds = setup_test_data
    response = client.post(
        "/api/v1/gateway/execute",
        headers={"x-client-id": creds["client_id_header"], "x-client-secret": creds["client_secret"]},
        json={"identity": creds["client_name"], "tool": "database", "action": "read", "resource": "db1"}
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "ALLOW"

