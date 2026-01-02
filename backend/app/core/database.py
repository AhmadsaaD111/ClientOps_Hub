from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def _build_engine():
    settings = get_settings()
    database_url = settings.database_url

    if database_url.startswith("sqlite:///./"):
        relative_path = database_url.replace("sqlite:///./", "", 1)
        backend_dir = Path(__file__).resolve().parents[2]
        database_url = f"sqlite:///{(backend_dir / relative_path).resolve()}"

    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(database_url, connect_args=connect_args)


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
