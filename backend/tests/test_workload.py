import pytest
from app.main import app
from app.models.workload import WorkloadIdentity
from app.core.security import create_access_token

@pytest.fixture
def admin_token(db_session):
    db = db_session
    from app.models.user import User, Role
    from app.core.security import get_password_hash
    role = db.query(Role).filter_by(name="ADMIN").first()
    if not role:
        role = Role(name="ADMIN")
        db.add(role)
        db.commit()
    user = db.query(User).filter_by(email="admin@aegis.local").first()
    if not user:
        user = User(email="admin@aegis.local", hashed_password=get_password_hash("pass"), role_id=role.id)
        db.add(user)
        db.commit()
    return create_access_token(subject="admin@aegis.local")

def test_create_identity(client, admin_token):
    response = client.post(
        "/api/v1/workloads/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "test-service-1", "owner": "test", "environment": "dev"}
    )
    assert response.status_code == 200

def test_create_credential(client, db_session, admin_token):
    # Setup
    identity = WorkloadIdentity(name="test-service-2", owner="test", environment="dev", status="ACTIVE")
    db_session.add(identity)
    db_session.commit()
    db_session.refresh(identity)
        
    response = client.post(
        f"/api/v1/workloads/{identity.id}/credentials",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert "client_secret" in response.json()

def test_suspend_identity(client, db_session, admin_token):
    identity = WorkloadIdentity(name="test-service-3", owner="test", environment="dev", status="ACTIVE")
    db_session.add(identity)
    db_session.commit()
    db_session.refresh(identity)
        
    response = client.put(
        f"/api/v1/workloads/{identity.id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "SUSPENDED"

@pytest.fixture
def viewer_token(db_session):
    db = db_session
    from app.models.user import User, Role
    from app.core.security import get_password_hash
    role = db.query(Role).filter_by(name="VIEWER").first()
    if not role:
        role = Role(name="VIEWER")
        db.add(role)
        db.commit()
    user = db.query(User).filter_by(email="viewer@aegis.local").first()
    if not user:
        user = User(email="viewer@aegis.local", hashed_password=get_password_hash("pass"), role_id=role.id)
        db.add(user)
        db.commit()
    return create_access_token(subject="viewer@aegis.local")

def test_viewer_cannot_create_identity(client, viewer_token):
    response = client.post(
        "/api/v1/workloads/",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"name": "test-service-4", "description": "Test", "environment": "dev"}
    )
    assert response.status_code == 403

def test_viewer_cannot_suspend(client, db_session, viewer_token, admin_token):
    identity = WorkloadIdentity(name="test-service-5", owner="test", environment="dev", status="ACTIVE")
    db_session.add(identity)
    db_session.commit()
    db_session.refresh(identity)
    
    response = client.put(
        f"/api/v1/workloads/{identity.id}/suspend",
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert response.status_code == 403
