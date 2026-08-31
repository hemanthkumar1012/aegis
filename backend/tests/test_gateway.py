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
    # Setup test identity
    client_id = "test-identity"
    client_secret = "test-secret"
    
    identity = db_session.query(WorkloadIdentity).filter_by(name=client_id).first()
    if not identity:
        identity = WorkloadIdentity(name=client_id, owner="test", environment="test", status="ACTIVE")
        db_session.add(identity)
        db_session.commit()
        db_session.refresh(identity)
        
        cred = IdentityCredential(identity_id=identity.id, hashed_secret=get_password_hash(client_secret))
        db_session.add(cred)
        db_session.commit()

    # Setup explicit ALLOW policy for testing
    pol = db_session.query(Policy).filter_by(name="test-allow-read").first()
    if not pol:
        pol = Policy(name="test-allow-read", effect="ALLOW", priority=100, conditions={"identity": client_id, "tool": "database", "action": "read"})
        db_session.add(pol)
        db_session.commit()
        
    return {"client_id": client_id, "client_secret": client_secret}

def test_gateway_unauthorized(setup_test_data):
    response = client.post(
        "/api/v1/gateway/execute",
        headers={"x-client-id": "wrong", "x-client-secret": "wrong"},
        json={"identity": "wrong", "tool": "database", "action": "read", "resource": "db1"}
    )
    assert response.status_code == 401

def test_gateway_default_deny(setup_test_data):
    creds = setup_test_data
    response = client.post(
        "/api/v1/gateway/execute",
        headers={"x-client-id": creds["client_id"], "x-client-secret": creds["client_secret"]},
        json={"identity": creds["client_id"], "tool": "unknown_tool", "action": "delete", "resource": "res1"}
    )
    assert response.status_code == 403
    assert response.json()["detail"]["decision"] == "DENY"

def test_gateway_allow(setup_test_data):
    creds = setup_test_data
    response = client.post(
        "/api/v1/gateway/execute",
        headers={"x-client-id": creds["client_id"], "x-client-secret": creds["client_secret"]},
        json={"identity": creds["client_id"], "tool": "database", "action": "read", "resource": "db1"}
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "ALLOW"
