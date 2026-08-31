import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.db.session import SessionLocal
from app.models.workload import WorkloadIdentity, IdentityCredential
from app.core.security import get_password_hash
from app.api.deps import get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def setup_identity_credential(db, **kwargs):
    identity_name = kwargs.pop('identity_name', 'auth-test-identity')
    identity_status = kwargs.pop('identity_status', 'ACTIVE')
    
    identity = db.query(WorkloadIdentity).filter_by(name=identity_name).first()
    if not identity:
        identity = WorkloadIdentity(name=identity_name, owner="test", environment="test", status=identity_status)
        db.add(identity)
        db.commit()
        db.refresh(identity)
    else:
        identity.status = identity_status
        db.commit()

    raw_secret = kwargs.pop('raw_secret', 'secret123')
    hashed_secret = get_password_hash(raw_secret)
    client_id = kwargs.pop('client_id', 'aegis_test_client')

    cred = db.query(IdentityCredential).filter_by(client_id=client_id).first()
    if cred:
        db.delete(cred)
        db.commit()

    cred = IdentityCredential(
        identity_id=identity.id,
        client_id=client_id,
        hashed_secret=hashed_secret,
        is_active=kwargs.get('is_active', True),
        expires_at=kwargs.get('expires_at', None),
        revoked_at=kwargs.get('revoked_at', None)
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)
    
    return {"client_id": client_id, "client_secret": raw_secret}

def execute_gateway_request(creds):
    return client.post(
        "/api/v1/gateway/execute",
        headers={"x-client-id": creds["client_id"], "x-client-secret": creds["client_secret"]},
        json={"identity": "auth-test-identity", "tool": "database", "action": "read", "resource": "res1"}
    )

def test_valid_active_unexpired_credential(db_session):
    creds = setup_identity_credential(
        db_session, 
        is_active=True, 
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    response = execute_gateway_request(creds)
    assert response.status_code != 401

def test_expired_credential(db_session):
    creds = setup_identity_credential(
        db_session, 
        is_active=True, 
        expires_at=datetime.now(timezone.utc) - timedelta(days=1)
    )
    response = execute_gateway_request(creds)
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()

def test_revoked_credential(db_session):
    creds = setup_identity_credential(
        db_session, 
        is_active=True, 
        revoked_at=datetime.now(timezone.utc)
    )
    response = execute_gateway_request(creds)
    assert response.status_code == 401
    assert "revoked" in response.json()["detail"].lower()

def test_inactive_credential(db_session):
    creds = setup_identity_credential(
        db_session, 
        is_active=False
    )
    response = execute_gateway_request(creds)
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()

def test_suspended_identity(db_session):
    creds = setup_identity_credential(
        db_session, 
        identity_status="SUSPENDED",
        is_active=True
    )
    response = execute_gateway_request(creds)
    assert response.status_code == 403
    assert "suspended" in response.json()["detail"].lower()

def test_rotated_credential_semantics(db_session):
    from app.models.user import User, Role
    from app.core.security import create_access_token
    
    role = db_session.query(Role).filter_by(name="ADMIN").first()
    if not role:
        role = Role(name="ADMIN")
        db_session.add(role)
        db_session.commit()
    user = db_session.query(User).filter_by(email="admin_rot@aegis.local").first()
    if not user:
        user = User(email="admin_rot@aegis.local", hashed_password=get_password_hash("pass"), role_id=role.id)
        db_session.add(user)
        db_session.commit()
    admin_token = create_access_token(subject="admin_rot@aegis.local")

    creds = setup_identity_credential(db_session, client_id="old_client")
    
    resp1 = execute_gateway_request(creds)
    assert resp1.status_code != 401
    
    identity = db_session.query(WorkloadIdentity).filter_by(name="auth-test-identity").first()
    
    rot_resp = client.post(
        f"/api/v1/workloads/{identity.id}/credentials",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert rot_resp.status_code == 200
    new_creds = {
        "client_id": rot_resp.json()["client_id"],
        "client_secret": rot_resp.json()["client_secret"]
    }
    
    resp2 = execute_gateway_request(creds)
    assert resp2.status_code == 401
    
    resp3 = execute_gateway_request(new_creds)
    assert resp3.status_code != 401

def test_invalid_client_secret(db_session):
    creds = setup_identity_credential(db_session)
    creds["client_secret"] = "wrongsecret"
    response = execute_gateway_request(creds)
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()

def test_exactly_expired_credential(db_session):
    creds = setup_identity_credential(
        db_session,
        is_active=True,
        expires_at=datetime.now(timezone.utc)
    )
    response = execute_gateway_request(creds)
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()

def test_expired_several_minutes_ago(db_session):
    creds = setup_identity_credential(
        db_session,
        is_active=True,
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=5)
    )
    response = execute_gateway_request(creds)
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()

def test_expiring_in_the_future(db_session):
    creds = setup_identity_credential(
        db_session,
        is_active=True,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    response = execute_gateway_request(creds)
    assert response.status_code != 401
