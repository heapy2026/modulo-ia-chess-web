"""Unit tests for backend/db.py."""

from sqlalchemy import create_engine, inspect

from db import init_db


def test_init_db_creates_sqlite_file_with_tables(tmp_path):
    db_file = tmp_path / "test_games.db"
    test_engine = create_engine(f"sqlite:///{db_file}")

    init_db(bind=test_engine)

    assert db_file.exists()
    tables = inspect(test_engine).get_table_names()
    assert "games" in tables
    assert "moves" in tables
