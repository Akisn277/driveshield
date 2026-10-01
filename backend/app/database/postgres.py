from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import POSTGRES_URL


engine = create_engine(
    POSTGRES_URL,
    pool_pre_ping=True,
    pool_timeout=3,
    connect_args={
        "connect_timeout": 3,
        "options": "-c statement_timeout=3000",
    },
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()