# Technical Design — Local Two-Player Web Chess

## 1. Architecture Overview

A classic **thin-client / authoritative-server** design.

```
+---------------------------+           HTTP / JSON            +----------------------------+
|        Frontend           |  <----------------------------> |          Backend           |
|  HTML + CSS + vanilla JS  |                                 |          Flask             |
|                           |   GET/POST /api/games/...       |                            |
|  - Board renderer (SVG)   |                                 |  - REST API (blueprint)    |
|  - Turn / status UI       |                                 |  - Rules engine wrapper    |
|  - Chat-style history     |                                 |    (python-chess)          |
|  - Active/finished lists  |                                 |  - SQLAlchemy models       |
+---------------------------+                                 +-------------+--------------+
                                                                            |
                                                                            v
                                                                    +---------------+
                                                                    |    SQLite     |
                                                                    |  (games.db)   |
                                                                    +---------------+
```

**Key principle:** the **server is the single source of truth** for every game.
The frontend never validates chess rules for correctness — it may *pre-highlight*
legal moves using data the server provides, but every move is submitted to the
backend, validated with `python-chess`, and the frontend re-renders from the
server's response. This keeps the client simple and impossible to desync.

## 2. Technology Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Web framework | Flask | Lightweight, matches requirement. |
| Rules engine | `python-chess` | Full legal-move gen, SAN, check/mate, all draw types, FEN. |
| ORM | SQLAlchemy | Requirement; clean model mapping. |
| Database | SQLite (single file) | Zero-config local persistence. |
| Frontend | HTML/CSS/vanilla JS | Requirement; no build step. |
| Piece art | Inline SVG (pixel-art) | Crisp, themeable, self-contained. |
| Backend testing | `pytest` | Requirement; unit tests for testable backend functions (rule logic, model/DTO helpers), excluding HTTP endpoints. |

## 3. How Backend and Frontend Communicate

- Transport: **HTTP with JSON** bodies and responses. No websockets (turn-based,
  single machine — polling/refresh on demand is sufficient).
- The frontend holds only a **current `game_id`** and renders whatever the
  server returns. After every action it receives a **canonical game-state DTO**
  and repaints.
- **Errors** (including illegal moves) return a non-2xx status with a JSON body
  `{ "error": { "code": ..., "message": ... } }`. The UI shows `message`
  verbatim as the "invalid move" notice.

### 3.1 Canonical Game-State DTO

Every state-returning endpoint returns the same shape so the frontend has one
render path:

```json
{
  "id": "a1b2c3d4",
  "alias": "Friday match",
  "player1_color": "white",
  "player2_color": "black",
  "status": "in_progress",            // in_progress | finished
  "result": null,                      // null | "player1" | "player2" | "draw"
  "termination": null,                 // null | checkmate | stalemate | threefold_repetition | fifty_moves | insufficient_material
  "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
  "turn": "white",                     // side to move
  "turn_player": "player1",            // which Player label is to move (derived from color mapping)
  "in_check": false,
  "legal_moves": [                      // legal moves for the side to move, precomputed for highlighting
    { "from": "e2", "to": "e4", "san": "e4", "promotion": false },
    { "from": "g1", "to": "f3", "san": "Nf3", "promotion": false }
  ],
  "move_history": [                     // full SAN history for the chat panel
    { "ply": 1, "move_number": 1, "color": "white", "san": "e4" },
    { "ply": 2, "move_number": 1, "color": "black", "san": "e5" }
  ],
  "created_at": "2026-07-15T12:00:00Z",
  "updated_at": "2026-07-15T12:03:10Z"
}
```

Notes:
- `legal_moves` is derived from `python-chess` on each request, so the frontend
  never computes chess logic. Promotion moves are flagged so the UI knows to
  prompt for a piece; a promotion square may appear multiple times (one per
  promotion piece) or once with `promotion: true` — the design uses **once with
  `promotion: true`**, and the client asks the user which piece, then submits.

## 4. Game Identity & Persistence While Active

### 4.1 Identity

- Each game gets a **server-generated short UUID** (`id`, e.g. first 8 hex chars
  of `uuid4`) at creation. This id is the primary key and the value the frontend
  passes back on every call.
- The optional **alias** is a display label only; it is never used for lookup.

### 4.2 What we persist and how state is reconstructed

We persist the **authoritative move list**, not just a snapshot. The board is
always **replayed from the moves** through `python-chess`, which guarantees the
stored state is always legal and lets us recompute SAN, check, and draw
conditions deterministically.

Two complementary representations are stored:

- **`Game.moves`** — the ordered list of moves in **UCI** (e.g. `e2e4`, `e7e8q`).
  This is the true source of state. Loading a game = create `chess.Board()` and
  push every UCI move in order.
- **`Game.fen`** — a cached FEN of the current position, updated on each move.
  Used as a fast read for the board render and as a sanity cross-check; it can
  always be regenerated from `moves`.

A game is "active" simply because `status == 'in_progress'`. There is no
in-memory session; **any request re-hydrates the board from the DB**, so
multiple concurrent games coexist naturally and survive server restarts.

### 4.3 Move application flow (server)

1. Load `Game` by `id`; reject if `status == 'finished'`.
2. Rebuild `board` by replaying `moves` (or load from FEN + validate).
3. Parse the requested move (`from`, `to`, optional `promotion`) into a
   `chess.Move`.
4. If `move not in board.legal_moves` → return **422** with a clear message; DB
   unchanged.
5. Compute SAN **before** pushing (SAN needs pre-move context), push the move.
6. Append UCI to `moves`, update `fen`, append a `Move` history row.
7. Evaluate terminal conditions in order: checkmate → stalemate → insufficient
   material → threefold repetition → fifty-move. If terminal, set `status`,
   `result`, `termination`, `finished_at`.
8. Commit, return the canonical DTO.

## 5. Data Model (SQLAlchemy)

### `games`
| Column | Type | Notes |
|--------|------|-------|
| `id` | String (PK) | Short UUID. |
| `alias` | String, nullable | Optional display name. |
| `player1_color` | String | `'white'` or `'black'`. |
| `player2_color` | String | Complement of `player1_color`. |
| `status` | String | `'in_progress'` \| `'finished'`. |
| `result` | String, nullable | `'player1'` \| `'player2'` \| `'draw'`. |
| `termination` | String, nullable | reason (checkmate, stalemate, …). |
| `fen` | String | Cached current position. |
| `created_at` | DateTime | UTC. |
| `updated_at` | DateTime | UTC, bumped on each move. |
| `finished_at` | DateTime, nullable | Set when finished. |

### `moves`
| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer (PK) | Autoincrement. |
| `game_id` | String (FK → games.id) | Indexed. |
| `ply` | Integer | 1-based half-move index. |
| `move_number` | Integer | Full-move number. |
| `color` | String | `'white'` \| `'black'`. |
| `uci` | String | Authoritative move (e.g. `e7e8q`). |
| `san` | String | For the history panel. |

`Game.result` = `'player1' / 'player2'` is derived from the **winning color**
mapped through `player1_color` / `player2_color`. Statistics are computed by
counting `games.result` where `status == 'finished'`.

## 6. REST API

Base path: `/api`. All responses JSON. State endpoints return the DTO in §3.1.

| Method | Path | Purpose | Body | Returns |
|--------|------|---------|------|---------|
| `POST` | `/api/games` | Create a new game. | `{ "player1_color": "white"\|"black", "alias": "optional" }` | Game DTO (201). |
| `GET` | `/api/games` | List games, filterable. | query `?status=in_progress\|finished` | Array of summaries. |
| `GET` | `/api/games/{id}` | Full current state of one game. | — | Game DTO. |
| `POST` | `/api/games/{id}/moves` | Submit a move. | `{ "from": "e2", "to": "e4", "promotion": "q"\|null }` | Updated Game DTO, or 422 `{error}`. |
| `GET` | `/api/games/{id}/legal-moves` | Legal moves (optionally for one square). | query `?from=e2` | Array of legal-move objects. |
| `GET` | `/api/stats` | Aggregate statistics. | — | `{ "player1_wins": n, "player2_wins": n, "draws": n, "total_finished": n }` |

### 6.1 Summary object (for list views)

`GET /api/games` returns lightweight summaries (not the full DTO) so the active
and finished lists render fast:

```json
{
  "id": "a1b2c3d4",
  "alias": "Friday match",
  "status": "in_progress",
  "result": null,
  "turn_player": "player1",
  "player1_color": "white",
  "player2_color": "black",
  "created_at": "2026-07-15T12:00:00Z"
}
```

- **Active list** consumes `?status=in_progress` (shows turn, alias, id, time).
- **Finished history** consumes `?status=finished` and displays **only the
  winner** (`result`), per the PRD.

### 6.2 Error contract

```json
{ "error": { "code": "ILLEGAL_MOVE", "message": "e2 to e5 is not a legal move." } }
```

| Situation | Status | code |
|-----------|--------|------|
| Illegal move | 422 | `ILLEGAL_MOVE` |
| Move on finished game | 409 | `GAME_FINISHED` |
| Malformed body | 400 | `BAD_REQUEST` |
| Unknown game id | 404 | `GAME_NOT_FOUND` |

## 7. Frontend Structure

```
frontend/
  index.html          # single page: board + right-side chat history + lists/modals
  css/style.css       # layout, pixel-art board theme, status banners
  js/
    api.js            # fetch wrappers for each endpoint
    board.js          # render board from FEN, place SVG pieces, handle clicks
    pieces.js         # SVG pixel-art piece definitions (by color+type)
    game.js           # current-game controller: select piece -> highlight ->
                       # submit move -> re-render; promotion prompt; banners
    lobby.js          # create game, active list, finished history, stats
  assets/             # (if any static SVG needed)
```

**Interaction loop (single game):**
1. Load game DTO → render board from `fen`, render history, set turn indicator.
2. User clicks a piece of the side to move → filter `legal_moves` by `from` →
   highlight destinations.
3. User clicks a destination:
   - If that move is flagged `promotion` → show promotion chooser → submit with
     `promotion`.
   - Else submit `{from, to}`.
4. On 2xx → repaint from returned DTO; if `in_check` show check banner; if
   `status == 'finished'` show result banner and lock the board.
5. On 4xx → show `error.message` as the invalid-move notice; leave board as-is.

## 8. Backend Structure

```
backend/
  app.py              # Flask app factory, blueprint registration, DB init
  models.py           # SQLAlchemy Game + Move models
  chess_service.py    # python-chess wrapper: replay, legal moves, apply move,
                       # SAN, terminal-condition detection, DTO assembly
  routes.py           # /api blueprint (endpoints in §6)
  db.py               # SQLAlchemy engine/session setup, games.db
  config.py           # paths, settings
tests/
  test_chess_service.py   # unit tests for chess_service.py functions
  test_models.py          # unit tests for any Game/Move model helpers
  conftest.py              # shared pytest fixtures (e.g. a fresh chess.Board)
requirements.txt      # flask, python-chess, SQLAlchemy, pytest
```

`chess_service.py` is the only module that imports `python-chess`; routes and
models stay engine-agnostic, which keeps rule logic in one testable place.

## 9. Sequence: submitting a move

```
User click        Frontend (game.js)        Backend (routes -> chess_service)      DB
   |  select piece      |                              |                            |
   |------------------->| highlight legal_moves        |                            |
   |  click target      |                              |                            |
   |------------------->| POST /games/{id}/moves ----->| load game ---------------->|
   |                    |                              | replay moves -> board      |
   |                    |                              | validate move (legal?)     |
   |                    |                              | push, compute SAN          |
   |                    |                              | detect end conditions      |
   |                    |                              | persist move + fen ------->|
   |                    |<---- 200 Game DTO -----------|                            |
   |<-- repaint + banner|                              |                            |
```

## 10. Testing Strategy

- **Unit tests are required for every testable backend function** — any
  function with a clear input/output contract that does not require an HTTP
  request/response cycle. This includes, but is not limited to:
  - **`chess_service`:** legal/illegal moves, castling, en passant, promotion
    (all four pieces), checkmate, stalemate, threefold repetition, fifty-move
    rule, insufficient material, SAN correctness, DTO assembly.
  - **`models`:** any helper/derived logic on `Game`/`Move` (e.g. mapping a
    winning color to `player1`/`player2`, computing `turn_player`).
  - Any other pure/testable helper added to the backend (e.g. in `config.py`
    or `db.py`) as the project grows.
- **Framework:** `pytest`. Test files live in `tests/`, named `test_*.py`,
  mirroring the module they cover (e.g. `chess_service.py` →
  `tests/test_chess_service.py`). Shared fixtures go in `tests/conftest.py`.
- **Out of scope for this requirement:** the HTTP layer (`routes.py` /
  `/api/...` endpoints). No API-level test suite is required; only functions
  callable directly in Python are covered.
- **Run with:** `pytest` (whole suite) or `pytest tests/test_x.py::test_name`
  (single test) — see CLAUDE.md for the exact commands.
- **Manual/E2E:** browser click-through of a full game per §7 loop, verifying
  turn indicator, highlighting, invalid-move message, check/mate/draw banners,
  chat history, active list, finished history, and stats. This remains manual
  and covers the HTTP/API + UI integration that unit tests skip.
```
