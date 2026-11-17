from collections.abc import Generator
from contextlib import contextmanager
import os
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def _resolver_database_url() -> str:
    """Resolve o caminho do SQLite para FLET_APP_STORAGE_DATA (Android/iOS) ou diretório local (Desktop)."""
    storage_dir = os.getenv("FLET_APP_STORAGE_DATA")
    if storage_dir:
        os.makedirs(storage_dir, exist_ok=True)
        db_path = os.path.join(storage_dir, "p4workout.db")
        return f"sqlite:///{db_path}"
    return "sqlite:///./p4workout.db"


DATABASE_URL = _resolver_database_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: Any, connection_record: Any) -> None:
    """Ativa o suporte estrito a Foreign Keys no SQLite a cada nova conexão."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Classe base declarativa do SQLAlchemy 2.0."""

    pass


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager transacional para gerenciamento seguro de sessões SQLite."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
