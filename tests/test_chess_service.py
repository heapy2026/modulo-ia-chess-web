"""Unit tests for backend/chess_service.py (TECH_DESIGN.md #2, #3.1, #4.3)."""

from datetime import datetime, timezone

import chess
import pytest

import chess_service
from chess_service import IllegalMoveError
from models import Game, Move

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


# 2.1 New board + FEN
def test_new_board_is_standard_starting_position():
    board = chess_service.new_board()
    assert board.fen() == STARTING_FEN


# 2.2 Replay moves
def test_replay_moves_rebuilds_expected_position():
    board = chess_service.replay_moves(["e2e4", "e7e5"])
    assert board.fen() == "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"


def test_replay_moves_empty_list_is_starting_position():
    board = chess_service.replay_moves([])
    assert board.fen() == STARTING_FEN


# 2.3 Legal-move listing
def test_legal_moves_from_start_has_twenty_moves():
    board = chess_service.new_board()
    moves = chess_service.legal_moves(board)
    assert len(moves) == 20


def test_legal_moves_filtered_by_from_square():
    board = chess_service.new_board()
    moves = chess_service.legal_moves(board, from_square="e2")
    assert {m["to"] for m in moves} == {"e3", "e4"}
    assert all(m["from"] == "e2" for m in moves)
    assert all(m["promotion"] is False for m in moves)


def test_legal_moves_promotion_listed_once_with_flag():
    board = chess.Board("8/P7/8/8/8/8/8/k6K w - - 0 1")
    moves = chess_service.legal_moves(board, from_square="a7")
    assert moves == [{"from": "a7", "to": "a8", "san": "a8+", "promotion": True}]


# 2.4 Apply a move + SAN
def test_apply_move_returns_san_and_updates_board():
    board = chess_service.new_board()
    result = chess_service.apply_move(board, "e2", "e4")
    assert result == {"uci": "e2e4", "san": "e4"}
    assert board.fen() == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"


def test_apply_move_illegal_raises_and_leaves_board_unchanged():
    board = chess_service.new_board()
    fen_before = board.fen()
    with pytest.raises(IllegalMoveError):
        chess_service.apply_move(board, "e2", "e5")
    assert board.fen() == fen_before


# 2.5 Terminal detection
def test_detect_terminal_fools_mate_is_checkmate_black_wins():
    board = chess_service.replay_moves(["f2f3", "e7e5", "g2g4", "d8h4"])
    terminal = chess_service.detect_terminal(board)
    assert terminal == {
        "is_over": True,
        "termination": "checkmate",
        "winner_color": "black",
        "in_check": True,
    }


def test_detect_terminal_stalemate():
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    terminal = chess_service.detect_terminal(board)
    assert terminal == {
        "is_over": True,
        "termination": "stalemate",
        "winner_color": None,
        "in_check": False,
    }


def test_detect_terminal_insufficient_material():
    board = chess.Board("8/8/8/4k3/8/8/8/4K3 w - - 0 1")
    terminal = chess_service.detect_terminal(board)
    assert terminal["termination"] == "insufficient_material"
    assert terminal["is_over"] is True
    assert terminal["winner_color"] is None


def test_detect_terminal_threefold_repetition():
    board = chess_service.replay_moves(
        ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8"]
    )
    terminal = chess_service.detect_terminal(board)
    assert terminal["termination"] == "threefold_repetition"
    assert terminal["is_over"] is True


def test_detect_terminal_fifty_moves():
    board = chess.Board("4k3/8/8/8/8/8/8/4K2R w K - 100 60")
    terminal = chess_service.detect_terminal(board)
    assert terminal["termination"] == "fifty_moves"
    assert terminal["is_over"] is True


def test_detect_terminal_ongoing_game():
    board = chess_service.new_board()
    terminal = chess_service.detect_terminal(board)
    assert terminal == {
        "is_over": False,
        "termination": None,
        "winner_color": None,
        "in_check": False,
    }


# 2.6 Promotion
def test_apply_move_promotion_knight_yields_knight_and_san():
    board = chess.Board("8/P7/8/8/8/8/8/k6K w - - 0 1")
    result = chess_service.apply_move(board, "a7", "a8", promotion="n")
    assert result == {"uci": "a7a8n", "san": "a8=N"}
    assert board.piece_at(chess.A8).piece_type == chess.KNIGHT


@pytest.mark.parametrize(
    "promotion,expected_piece",
    [("q", chess.QUEEN), ("r", chess.ROOK), ("b", chess.BISHOP), ("n", chess.KNIGHT)],
)
def test_apply_move_supports_all_four_promotion_pieces(promotion, expected_piece):
    board = chess.Board("8/P7/8/8/8/8/8/k6K w - - 0 1")
    chess_service.apply_move(board, "a7", "a8", promotion=promotion)
    assert board.piece_at(chess.A8).piece_type == expected_piece


# 2.7 DTO assembly
def test_build_dto_has_all_required_keys_with_correct_values():
    game = Game(
        id="g1",
        alias="Friday match",
        player1_color="white",
        player2_color="black",
        status="in_progress",
        result=None,
        termination=None,
        fen="unused-cache",
    )
    game.created_at = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
    game.updated_at = datetime(2026, 7, 15, 12, 3, 10, tzinfo=timezone.utc)
    game.moves = [
        Move(game_id="g1", ply=1, move_number=1, color="white", uci="e2e4", san="e4"),
        Move(game_id="g1", ply=2, move_number=1, color="black", uci="e7e5", san="e5"),
    ]
    board = chess_service.replay_moves(["e2e4", "e7e5"])

    dto = chess_service.build_dto(game, board)

    assert dto == {
        "id": "g1",
        "alias": "Friday match",
        "player1_color": "white",
        "player2_color": "black",
        "status": "in_progress",
        "result": None,
        "termination": None,
        "fen": board.fen(),
        "turn": "white",
        "turn_player": "player1",
        "in_check": False,
        "legal_moves": chess_service.legal_moves(board),
        "move_history": [
            {"ply": 1, "move_number": 1, "color": "white", "san": "e4"},
            {"ply": 2, "move_number": 1, "color": "black", "san": "e5"},
        ],
        "created_at": "2026-07-15T12:00:00+00:00",
        "updated_at": "2026-07-15T12:03:10+00:00",
    }


def test_build_dto_turn_player_reflects_black_to_move_and_player1_is_black():
    game = Game(
        id="g2",
        alias=None,
        player1_color="black",
        player2_color="white",
        status="in_progress",
        result=None,
        termination=None,
        fen="unused-cache",
    )
    game.created_at = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
    game.updated_at = datetime(2026, 7, 15, 12, 0, 0, tzinfo=timezone.utc)
    game.moves = [
        Move(game_id="g2", ply=1, move_number=1, color="white", uci="e2e4", san="e4"),
    ]
    board = chess_service.replay_moves(["e2e4"])

    dto = chess_service.build_dto(game, board)

    assert dto["turn"] == "black"
    assert dto["turn_player"] == "player1"
