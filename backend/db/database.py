import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.config import get_settings
from backend.db.models import Base

# Engines are created lazily and cached per DB path, so tests that point
# DB_PATH at a temp file get a fully isolated database (no cross-test bleed).
_engines: dict[str, object] = {}


def _current_db_path() -> str:
    return os.environ.get("DB_PATH") or get_settings().db_path


def _get_engine():
    path = _current_db_path()
    if path not in _engines:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        _engines[path] = create_engine(
            f"sqlite:///{path}", connect_args={"check_same_thread": False}
        )
    return _engines[path]


def init_db() -> None:
    Base.metadata.create_all(_get_engine())


@contextmanager
def get_session() -> Session:
    session = sessionmaker(bind=_get_engine(), expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
