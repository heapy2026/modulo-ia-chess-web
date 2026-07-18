"""REST API blueprint: /api/games, /api/games/{id}, /api/games/{id}/moves,
/api/games/{id}/legal-moves, /api/stats (TECH_DESIGN.md #6).

Routes stay engine-agnostic: all chess logic is delegated to chess_service.
"""

import uuid

from flask import Blueprint, jsonify, request

import chess_service
from db import SessionLocal
from models import Game, Move, utcnow

api_bp = Blueprint("api", __name__, url_prefix="/api")

VALID_COLORS = {"white", "black"}
VALID_STATUSES = {"in_progress", "finished"}
VALID_PROMOTIONS = {"q", "r", "b", "n"}


def _error(status, code, message):
    return jsonify({"error": {"code": code, "message": message}}), status


def _generate_game_id(session):
    for _ in range(5):
        candidate = uuid.uuid4().hex[:8]
        if session.get(Game, candidate) is None:
            return candidate
    raise RuntimeError("Could not generate a unique game id.")


def _complement_color(color):
    return "black" if color == "white" else "white"


def _load_board(game):
    return chess_service.replay_moves([move.uci for move in game.moves])


def _game_summary(game):
    turn_color = "white" if len(game.moves) % 2 == 0 else "black"
    return {
        "id": game.id,
        "alias": game.alias,
        "status": game.status,
        "result": game.result,
        "turn_player": game.player_label_for_color(turn_color),
        "player1_color": game.player1_color,
        "player2_color": game.player2_color,
        "created_at": game.created_at.isoformat(),
    }


@api_bp.post("/games")
def create_game():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _error(400, "BAD_REQUEST", "Request body must be a JSON object.")

    player1_color = body.get("player1_color")
    if player1_color not in VALID_COLORS:
        return _error(400, "BAD_REQUEST", "player1_color must be 'white' or 'black'.")

    alias = body.get("alias")
    if alias is not None and not isinstance(alias, str):
        return _error(400, "BAD_REQUEST", "alias must be a string.")

    session = SessionLocal()
    board = chess_service.new_board()
    game = Game(
        id=_generate_game_id(session),
        alias=alias,
        player1_color=player1_color,
        player2_color=_complement_color(player1_color),
        status="in_progress",
        fen=board.fen(),
    )
    session.add(game)
    session.commit()

    return jsonify(chess_service.build_dto(game, board)), 201


@api_bp.get("/games")
def list_games():
    status = request.args.get("status")
    if status is not None and status not in VALID_STATUSES:
        return _error(400, "BAD_REQUEST", "status must be 'in_progress' or 'finished'.")

    session = SessionLocal()
    query = session.query(Game)
    if status is not None:
        query = query.filter(Game.status == status)
    games = query.order_by(Game.created_at).all()

    return jsonify([_game_summary(game) for game in games])


@api_bp.get("/games/<game_id>")
def get_game(game_id):
    session = SessionLocal()
    game = session.get(Game, game_id)
    if game is None:
        return _error(404, "GAME_NOT_FOUND", f"No game with id '{game_id}'.")

    board = _load_board(game)
    return jsonify(chess_service.build_dto(game, board))


@api_bp.post("/games/<game_id>/moves")
def submit_move(game_id):
    session = SessionLocal()
    game = session.get(Game, game_id)
    if game is None:
        return _error(404, "GAME_NOT_FOUND", f"No game with id '{game_id}'.")
    if game.status == "finished":
        return _error(409, "GAME_FINISHED", "This game has already finished.")

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _error(400, "BAD_REQUEST", "Request body must be a JSON object.")

    from_square = body.get("from")
    to_square = body.get("to")
    if not isinstance(from_square, str) or not isinstance(to_square, str):
        return _error(400, "BAD_REQUEST", "Both 'from' and 'to' fields are required.")
    promotion = body.get("promotion")
    if promotion is not None and promotion not in VALID_PROMOTIONS:
        return _error(400, "BAD_REQUEST", "promotion must be one of 'q', 'r', 'b', 'n'.")

    board = _load_board(game)
    try:
        move_result = chess_service.apply_move(board, from_square, to_square, promotion)
    except chess_service.IllegalMoveError as exc:
        return _error(422, "ILLEGAL_MOVE", exc.message)

    ply = len(game.moves) + 1
    color = "white" if ply % 2 == 1 else "black"
    move_number = (ply + 1) // 2
    game.moves.append(
        Move(
            ply=ply,
            move_number=move_number,
            color=color,
            uci=move_result["uci"],
            san=move_result["san"],
        )
    )

    terminal = chess_service.detect_terminal(board)
    game.fen = board.fen()
    if terminal["is_over"]:
        game.status = "finished"
        game.termination = terminal["termination"]
        game.result = (
            game.player_label_for_color(terminal["winner_color"])
            if terminal["winner_color"]
            else "draw"
        )
        game.finished_at = utcnow()
    session.commit()

    return jsonify(chess_service.build_dto(game, board))


@api_bp.get("/games/<game_id>/legal-moves")
def get_legal_moves(game_id):
    session = SessionLocal()
    game = session.get(Game, game_id)
    if game is None:
        return _error(404, "GAME_NOT_FOUND", f"No game with id '{game_id}'.")

    from_square = request.args.get("from")
    board = _load_board(game)
    return jsonify(chess_service.legal_moves(board, from_square=from_square))


@api_bp.get("/stats")
def get_stats():
    session = SessionLocal()
    finished = session.query(Game).filter(Game.status == "finished").all()
    player1_wins = sum(1 for g in finished if g.result == "player1")
    player2_wins = sum(1 for g in finished if g.result == "player2")
    draws = sum(1 for g in finished if g.result == "draw")
    return jsonify(
        {
            "player1_wins": player1_wins,
            "player2_wins": player2_wins,
            "draws": draws,
            "total_finished": len(finished),
        }
    )
