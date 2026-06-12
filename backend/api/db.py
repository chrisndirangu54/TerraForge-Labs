from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover
    psycopg = None  # type: ignore[assignment]
    dict_row = None  # type: ignore[assignment]


def database_url() -> str | None:
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit
    host = os.getenv("DB_HOST")
    if not host:
        return None
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "terraforge")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


def db_available() -> bool:
    if psycopg is None:
        return False
    url = database_url()
    if not url:
        return False
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


@contextmanager
def get_connection() -> Generator:
    if psycopg is None:
        raise RuntimeError("psycopg is not installed")
    url = database_url()
    if not url:
        raise RuntimeError("DATABASE_URL or DB_HOST is not configured")
    with psycopg.connect(url, row_factory=dict_row) as conn:
        yield conn