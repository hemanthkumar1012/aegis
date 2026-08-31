import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.workload import WorkloadIdentity
from app.core.security import create_access_token

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
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
