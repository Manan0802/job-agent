import logging
import os
from contextlib import contextmanager
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from backend.config import get_settings
from backend.db.models import Base

log = logging.getLogger(__name__)

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
    engine = _get_engine()
    Base.metadata.create_all(engine)
    _add_missing_columns(engine)


def _add_missing_columns(engine) -> None:
    """Bring a database made by an earlier version up to the current models.

    create_all() adds missing tables but never missing columns, so adding a
    field to a model leaves every existing database on the old shape and the
    first query against it fails with "no such column". SQLite can add nullable
    columns in place, which is all this project has ever needed.
    """
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in tables:
                continue
            present = {c["name"] for c in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in present:
                    continue
                if not column.nullable:
                    log.warning(
                        "%s.%s is not nullable and cannot be added to an existing "
                        "database automatically", table.name, column.name,
                    )
                    continue
                type_sql = column.type.compile(engine.dialect)
                log.info("adding missing column %s.%s", table.name, column.name)
                conn.execute(text(f"ALTER TABLE {table.name} ADD COLUMN {column.name} {type_sql}"))


@contextmanager
def get_session() -> Session:
    session = sessionmaker(bind=_get_engine(), expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
