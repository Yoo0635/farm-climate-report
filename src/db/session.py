"""SQLAlchemy engine and session factory.

Reads `DATABASE_URL` from environment. Example:
postgresql+psycopg2://farm_user:password@db:5432/farm_db
"""

from __future__ import annotations

import os
from typing import Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        # Sensible default for local/compose when env not set
        url = "postgresql+psycopg2://farm_user:change_me@localhost:5432/farm_db"
    return url


def get_engine():
    return create_engine(_database_url(), pool_pre_ping=True, future=True)


def get_session_maker() -> Callable[[], "Session"]:
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, future=True)

