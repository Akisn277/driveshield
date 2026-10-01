import jwt
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import AUTH_PASSWORD, AUTH_USERNAME, JWT_ALGORITHM, JWT_SECRET_KEY
from app.database.postgres import Base, get_db
from app.models.user import User
from app.main import app


_test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(_test_engine)
_TestSession = sessionmaker(bind=_test_engine, autocommit=False, autoflush=False)


def _test_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _test_db
client = TestClient(app)


def test_successful_login_returns_jwt_with_role():
    response = client.post("/api/auth/login", json={"username": AUTH_USERNAME, "password": AUTH_PASSWORD})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    claims = jwt.decode(body["access_token"], JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    assert claims["sub"] == AUTH_USERNAME
    assert claims["role"] == "fleet_manager"


def test_invalid_credentials_are_rejected():
    response = client.post("/api/auth/login", json={"username": AUTH_USERNAME, "password": "wrong-password"})

    assert response.status_code == 401


def test_missing_token_is_rejected():
    response = client.get("/api/dashboard/summary")

    assert response.status_code == 401


def test_valid_token_is_accepted():
    login = client.post("/api/auth/login", json={"username": AUTH_USERNAME, "password": AUTH_PASSWORD})
    response = client.get(
        "/api/dashboard/summary",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )

    assert response.status_code == 200
    assert set(response.json()) == {"vehicles_monitored", "events_processed", "active_anomalies", "critical_alerts"}


def test_successful_signup():
    response = client.post("/api/auth/signup", json={"name": "New Manager", "username": "new_manager", "email": "new.manager@example.com", "password": "strong-pass-123", "confirm_password": "strong-pass-123"})

    assert response.status_code == 201
    assert response.json()["username"] == "new_manager"


def test_duplicate_signup_is_rejected():
    payload = {"name": "Duplicate Manager", "username": "duplicate_manager", "email": "duplicate@example.com", "password": "strong-pass-123", "confirm_password": "strong-pass-123"}
    assert client.post("/api/auth/signup", json=payload).status_code == 201

    duplicate = client.post("/api/auth/signup", json=payload)

    assert duplicate.status_code == 409


def test_invalid_signup_input_is_rejected():
    response = client.post("/api/auth/signup", json={"name": "A", "username": "bad user", "email": "not-an-email", "password": "short", "confirm_password": "different"})

    assert response.status_code == 422


def test_signup_password_is_hashed():
    client.post("/api/auth/signup", json={"name": "Hash Manager", "username": "hash_manager", "email": "hash@example.com", "password": "strong-pass-123", "confirm_password": "strong-pass-123"})
    db = _TestSession()
    try:
        user = db.query(User).filter(User.username == "hash_manager").one()
        assert user.password_hash != "strong-pass-123"
        assert PasswordHash.recommended().verify("strong-pass-123", user.password_hash)
    finally:
        db.close()
