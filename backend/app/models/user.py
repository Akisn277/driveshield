from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from app.database.postgres import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="fleet_manager")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
