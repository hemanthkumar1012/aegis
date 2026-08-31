import pytest
from app.main import app
from app.models.user import User
from app.core.security import get_password_hash, create_access_token
from datetime import timedelta

@pytest.fixture
def setup_users(db_session):
    # Active user
    active_user = db_session.query(User).filter_by(email="active@test.com").first()
    if not active_user:
        active_user = User(email="active@test.com", hashed_password=get_password_hash("password"), is_active=True)
        db_session.add(active_user)
    
    # Inactive user
    inactive_user = db_session.query(User).filter_by(email="inactive@test.com").first()
    if not inactive_user:
        inactive_user = User(email="inactive@test.com", hashed_password=get_password_hash("password"), is_active=False)
        db_session.add(inactive_user)
        
    db_session.commit()

def test_login_success(client, setup_users):
    response = client.post("/api/v1/login/access-token", data={"username": "active@test.com", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password(client, setup_users):
    response = client.post("/api/v1/login/access-token", data={"username": "active@test.com", "password": "wrong"})
    assert response.status_code == 400

def test_login_inactive_user(client, setup_users):
    response = client.post("/api/v1/login/access-token", data={"username": "inactive@test.com", "password": "password"})
    assert response.status_code == 400
    assert "Inactive" in response.json()["detail"]

def test_protected_route_missing_token(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

def test_protected_route_invalid_token(client):
    response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401

def test_protected_route_expired_token(client):
    # create expired token
    token = create_access_token(subject="active@test.com", expires_delta=timedelta(minutes=-10))
    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
