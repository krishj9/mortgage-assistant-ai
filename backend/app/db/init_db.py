from __future__ import annotations

from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    """
    Dev convenience initializer.

    In later phases (and in CI) prefer Alembic migrations for schema changes.
    """

    Base.metadata.create_all(bind=engine)

