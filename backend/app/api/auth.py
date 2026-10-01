from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.postgres import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, SignupRequest, TokenResponse
from app.services.auth import ROLE_FLEET_MANAGER, authenticate, create_access_token, create_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate(credentials.username, credentials.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    return TokenResponse(
        access_token=create_access_token(user["username"], user["role"]),
        role=user["role"],
    )


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(credentials: SignupRequest, db: Session = Depends(get_db)):
    if credentials.password != credentials.confirm_password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Passwords do not match")
    if "@" not in credentials.email or credentials.email.startswith("@") or credentials.email.endswith("@"):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid email address")
    duplicate = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.email.lower())
    ).first()
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already registered")
    try:
        user = create_user(credentials.name, credentials.username, credentials.email, credentials.password, db)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already registered") from exc
    return {"message": "Account created", "username": user.username, "role": user.role}
