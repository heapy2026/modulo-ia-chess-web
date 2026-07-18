"""Unit tests for backend/models.py: table shape, relationships, and helpers."""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from db import Base
from models import Game, Move


@pytest.fixture
def session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    s = session_factory()
    yield s
    s.close()


def test_games_table_has_expected_columns(session):
    inspector = inspect(session.bind)
    columns = {c["name"] for c in inspector.get_columns("games")}
    assert columns == {
        "id",
        "alias",
        "player1_color",
        "player2_color",
        "status",
        "result",
        "termination",
        "fen",
        "created_at",
        "updated_at",
        "finished_at",
    }


def test_moves_table_has_expected_columns(session):
    inspector = inspect(session.bind)
    columns = {c["name"] for c in inspector.get_columns("moves")}
    assert columns == {"id", "game_id", "ply", "move_number", "color", "uci", "san"}


def test_game_move_relationship_ordered_by_ply(session):
    game = Game(id="g1", player1_color="white", player2_color="black", fen="startfen")
    session.add(game)
    session.commit()

    session.add_all(
        [
            Move(game_id="g1", ply=2, move_number=1, color="black", uci="e7e5", san="e5"),
            Move(game_id="g1", ply=1, move_number=1, color="white", uci="e2e4", san="e4"),
        ]
    )
    session.commit()

    fetched = session.get(Game, "g1")
    assert [m.uci for m in fetched.moves] == ["e2e4", "e7e5"]


def test_player_label_for_color_when_player1_is_white():
    game = Game(id="g1", player1_color="white", player2_color="black", fen="")
    assert game.player_label_for_color("white") == "player1"
    assert game.player_label_for_color("black") == "player2"


def test_player_label_for_color_when_player1_is_black():
    game = Game(id="g1", player1_color="black", player2_color="white", fen="")
    assert game.player_label_for_color("black") == "player1"
    assert game.player_label_for_color("white") == "player2"
