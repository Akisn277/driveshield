from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import (
    AUTH_PASSWORD,
    AUTH_USERNAME,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
)
from app.models.user import User

ROLE_FLEET_MANAGER = "fleet_manager"
_password_hash = PasswordHash.recommended()
_configured_password_hash = _password_hash.hash(AUTH_PASSWORD)
_bearer = HTTPBearer(auto_error=False)


def authenticate(identifier: str, password: str, db: Session | None = None) -> dict | None:
    if db is not None:
        user = db.query(User).filter(or_(User.username == identifier, User.email == identifier)).first()
        if user and _password_hash.verify(password, user.password_hash):
            return {"username": user.username, "role": user.role}
    if identifier == AUTH_USERNAME and _password_hash.verify(password, _configured_password_hash):
        return {"username": AUTH_USERNAME, "role": ROLE_FLEET_MANAGER}
    return None


def create_user(name: str, username: str, email: str, password: str, db: Session) -> User:
    user = User(
        name=name.strip(),
        username=username.strip(),
        email=email.strip().lower(),
        password_hash=_password_hash.hash(password),
        role=ROLE_FLEET_MANAGER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_access_token(username: str, role: str = ROLE_FLEET_MANAGER) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": username, "role": role, "exp": expires_at},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc
    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token claims")
    return {"username": username, "role": role}


def require_fleet_manager(user: Annotated[dict, Depends(get_current_user)]) -> dict:
    if user["role"] != ROLE_FLEET_MANAGER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Fleet manager role required")
    return user
