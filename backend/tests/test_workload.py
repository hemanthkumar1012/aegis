import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.workload import WorkloadIdentity
from app.core.security import create_access_token

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    db = SessionLocal()
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
    db.close()
    return create_access_token(subject="admin@aegis.local")

def test_create_identity(admin_token):
    response = client.post(
        "/api/v1/workloads/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "test-service-1", "owner": "test", "environment": "dev"}
    )
    # 200 or 400 if exists
    assert response.status_code in [200, 400]

def test_create_credential(admin_token):
    db = SessionLocal()
    identity = db.query(WorkloadIdentity).filter_by(name="test-service-1").first()
    db.close()
    
    if not identity:
        pytest.skip("Identity not created")
        
    response = client.post(
        f"/api/v1/workloads/{identity.id}/credentials",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert "client_secret" in response.json()

def test_suspend_identity(admin_token):
    db = SessionLocal()
    identity = db.query(WorkloadIdentity).filter_by(name="test-service-1").first()
    db.close()
    
    if not identity:
        pytest.skip("Identity not created")
        
    response = client.put(
        f"/api/v1/workloads/{identity.id}/suspend",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "SUSPENDED"
@pytest.fixture(scope="module")
def viewer_token():
    db = SessionLocal()
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
    db.close()
    return create_access_token(subject="viewer@aegis.local")

def test_viewer_cannot_create_identity(viewer_token):
    response = client.post(
        "/api/v1/workloads/",
        headers={"Authorization": f"Bearer {viewer_token}"},
        json={"name": "test-service-viewer", "owner": "test", "environment": "dev"}
    )
    assert response.status_code == 403

def test_viewer_cannot_suspend(viewer_token, admin_token):
    db = SessionLocal()
    identity = db.query(WorkloadIdentity).filter_by(name="test-service-1").first()
    db.close()
    if not identity:
        pytest.skip("Identity not created")
        
    response = client.put(
        f"/api/v1/workloads/{identity.id}/suspend",
        headers={"Authorization": f"Bearer {viewer_token}"}
    )
    assert response.status_code == 403
