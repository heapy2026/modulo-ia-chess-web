"""python-chess wrapper: replay, legal moves, apply move, SAN, terminal-condition
detection, and Game-State DTO assembly (TECH_DESIGN.md #3.1, #4.3).

This is the only module that imports python-chess; routes and models stay
engine-agnostic.
"""

import re

import chess

PROMOTION_PIECES = {"q": chess.QUEEN, "r": chess.ROOK, "b": chess.BISHOP, "n": chess.KNIGHT}

TERMINATION_CHECKMATE = "checkmate"
TERMINATION_STALEMATE = "stalemate"
TERMINATION_INSUFFICIENT_MATERIAL = "insufficient_material"
TERMINATION_THREEFOLD_REPETITION = "threefold_repetition"
TERMINATION_FIFTY_MOVES = "fifty_moves"

_PROMOTION_SUFFIX_RE = re.compile(r"=[QRBN]")


class IllegalMoveError(Exception):
    """Raised when a requested move is not legal in the current position."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


def new_board():
    """Return a board in the standard starting position."""
    return chess.Board()


def replay_moves(uci_moves):
    """Rebuild a board by pushing an ordered list of UCI moves from the start."""
    board = chess.Board()
    for uci in uci_moves:
        board.push_uci(uci)
    return board


def legal_moves(board, from_square=None):
    """Legal moves for the side to move, as {from, to, san, promotion}.

    A promoting move to a given square is listed once (promotion=True) rather
    than once per promotion piece, per TECH_DESIGN.md #3.1.
    """
    moves = []
    for move in board.legal_moves:
        from_sq = chess.square_name(move.from_square)
        if from_square is not None and from_sq != from_square:
            continue
        is_promotion = move.promotion is not None
        if is_promotion and move.promotion != chess.QUEEN:
            continue
        san = board.san(move)
        if is_promotion:
            san = _PROMOTION_SUFFIX_RE.sub("", san)
        moves.append(
            {
                "from": from_sq,
                "to": chess.square_name(move.to_square),
                "san": san,
                "promotion": is_promotion,
            }
        )
    return moves


def apply_move(board, from_square, to_square, promotion=None):
    """Validate and push a move onto `board`. Returns {"uci", "san"}.

    SAN is computed before pushing, since SAN needs pre-move context.
    Raises IllegalMoveError if the move is not legal in the current position.
    """
    move = _build_move(board, from_square, to_square, promotion)
    if move not in board.legal_moves:
        raise IllegalMoveError(f"{from_square} to {to_square} is not a legal move.")
    san = board.san(move)
    board.push(move)
    return {"uci": move.uci(), "san": san}


def _build_move(board, from_square, to_square, promotion):
    try:
        from_sq = chess.parse_square(from_square)
        to_sq = chess.parse_square(to_square)
    except ValueError as exc:
        raise IllegalMoveError(str(exc)) from exc
    promo_piece = PROMOTION_PIECES.get(promotion) if promotion else None
    return chess.Move(from_sq, to_sq, promotion=promo_piece)


def detect_terminal(board):
    """Evaluate terminal conditions in the order TECH_DESIGN.md #4.3 specifies:
    checkmate -> stalemate -> insufficient material -> threefold repetition ->
    fifty-move rule.

    Returns {"is_over", "termination", "winner_color", "in_check"}. `winner_color`
    is "white"/"black" for checkmate, None for a draw or an ongoing game.
    """
    in_check = board.is_check()

    if board.is_checkmate():
        winner_color = "black" if board.turn == chess.WHITE else "white"
        return {
            "is_over": True,
            "termination": TERMINATION_CHECKMATE,
            "winner_color": winner_color,
            "in_check": in_check,
        }
    if board.is_stalemate():
        return {
            "is_over": True,
            "termination": TERMINATION_STALEMATE,
            "winner_color": None,
            "in_check": in_check,
        }
    if board.is_insufficient_material():
        return {
            "is_over": True,
            "termination": TERMINATION_INSUFFICIENT_MATERIAL,
            "winner_color": None,
            "in_check": in_check,
        }
    if board.is_repetition(3):
        return {
            "is_over": True,
            "termination": TERMINATION_THREEFOLD_REPETITION,
            "winner_color": None,
            "in_check": in_check,
        }
    if board.halfmove_clock >= 100:
        return {
            "is_over": True,
            "termination": TERMINATION_FIFTY_MOVES,
            "winner_color": None,
            "in_check": in_check,
        }
    return {"is_over": False, "termination": None, "winner_color": None, "in_check": in_check}


def build_dto(game, board):
    """Assemble the canonical Game-State DTO (TECH_DESIGN.md #3.1) from a `Game`
    row plus its replayed board. `status`/`result`/`termination` are read
    straight off `game`, since they were already decided (via detect_terminal)
    when the last move was applied; everything else is derived from `board`.
    """
    turn_color = "white" if board.turn == chess.WHITE else "black"
    return {
        "id": game.id,
        "alias": game.alias,
        "player1_color": game.player1_color,
        "player2_color": game.player2_color,
        "status": game.status,
        "result": game.result,
        "termination": game.termination,
        "fen": board.fen(),
        "turn": turn_color,
        "turn_player": game.player_label_for_color(turn_color),
        "in_check": board.is_check(),
        "legal_moves": legal_moves(board),
        "move_history": [
            {
                "ply": move.ply,
                "move_number": move.move_number,
                "color": move.color,
                "san": move.san,
            }
            for move in game.moves
        ],
        "created_at": game.created_at.isoformat(),
        "updated_at": game.updated_at.isoformat(),
    }
