"""SQLAlchemy engine/session setup against games.db."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from config import DATABASE_URI

engine = create_engine(DATABASE_URI, connect_args={"check_same_thread": False})
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))

Base = declarative_base()


def init_db(bind=None):
    """Create all tables that don't exist yet."""
    import models  # noqa: F401  (ensure models are registered on Base.metadata)

    Base.metadata.create_all(bind=bind or engine)
