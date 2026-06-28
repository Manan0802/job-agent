import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.config import get_settings
from backend.db.models import Base

_settings = get_settings()
_db_path = os.environ.get("DB_PATH", _settings.db_path)
os.makedirs(os.path.dirname(_db_path), exist_ok=True)

engine = create_engine(f"sqlite:///{_db_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


@contextmanager
def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
