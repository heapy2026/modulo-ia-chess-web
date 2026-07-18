# TODO — Build Order (simplest → most complex)

Tasks are ordered so each builds on the previous one. Check items off as you go.
Every task lists a concrete **Verify** step.

## Phase 0 — Project scaffolding

- [ ] **0.1 Repo layout.** Create `backend/`, `frontend/`, keep `docs/`.
  *Verify:* folders exist; `docs/` has PRD, TECH_DESIGN, TODO.
- [ ] **0.2 Python env + deps.** `requirements.txt` with `flask`, `python-chess`,
  `SQLAlchemy`, `pytest`; create a virtualenv and install.
  *Verify:* `python -c "import flask, chess, sqlalchemy, pytest"` runs with no
  error.
- [ ] **0.3 Flask "hello".** `app.py` app factory serving `GET /api/health`
  → `{"status":"ok"}`.
  *Verify:* `curl localhost:5000/api/health` returns the JSON.
- [ ] **0.4 Test scaffolding.** Create `tests/` with `conftest.py` (empty or
  shared fixtures) per TECH_DESIGN §8/§10.
  *Verify:* `pytest` runs from the repo root with zero errors (zero tests
  collected is fine at this point).

## Phase 1 — Persistence layer

- [ ] **1.1 DB setup.** `db.py` with SQLAlchemy engine/session against
  `games.db`.
  *Verify:* running the app creates `games.db` on disk.
- [ ] **1.2 Models.** `Game` and `Move` models per TECH_DESIGN §5; create tables
  on startup.
  *Verify:* open `games.db` (or a shell) and confirm `games`/`moves` tables and
  columns exist.

## Phase 2 — Rules engine wrapper (no HTTP yet)

- [ ] **2.1 New board + FEN.** `chess_service` can create a starting board and
  return its FEN.
  *Verify:* `pytest` unit test in `tests/test_chess_service.py` asserts the
  standard start FEN.
- [ ] **2.2 Replay moves.** Given a UCI move list, rebuild the board.
  *Verify:* `pytest` unit test: replay `["e2e4","e7e5"]` → expected FEN.
- [ ] **2.3 Legal-move listing.** Return legal moves as
  `{from,to,san,promotion}` for the side to move (and filtered by a `from`
  square).
  *Verify:* `pytest` unit test: 20 legal moves from start; `from=e2` yields
  `e3,e4`.
- [ ] **2.4 Apply a move + SAN.** Validate, compute SAN pre-push, push, return
  new state; reject illegal moves with an error.
  *Verify:* `pytest` unit test: legal move returns SAN `e4`; illegal move
  raises the expected error.
- [ ] **2.5 Terminal detection.** Detect and label checkmate, stalemate,
  threefold repetition, fifty-move, insufficient material; also expose
  `in_check`.
  *Verify:* `pytest` unit tests per condition (e.g. fool's mate → `checkmate`;
  known stalemate FEN → `stalemate`).
- [ ] **2.6 Promotion.** Support all four promotion pieces via the `promotion`
  field.
  *Verify:* `pytest` unit test: `e7e8` with `promotion="n"` yields a knight;
  SAN `=N`.
- [ ] **2.7 DTO assembly.** Build the canonical Game-State DTO (§3.1) from a
  `Game` + replayed board.
  *Verify:* `pytest` unit test in `tests/test_chess_service.py` asserts the
  DTO has all required keys with correct values for a known board state.

## Phase 3 — REST API

- [ ] **3.1 Create game.** `POST /api/games` with `player1_color` + optional
  `alias`; generate id; persist; return DTO.
  *Verify:* `curl -X POST` returns 201 with an id, correct colors, start FEN,
  `turn_player`.
- [ ] **3.2 Get game.** `GET /api/games/{id}` returns the full DTO (§3.1),
  including `legal_moves` and `move_history`.
  *Verify:* fetch the created game; DTO matches; unknown id → 404.
- [ ] **3.3 Submit move.** `POST /api/games/{id}/moves`; on legal move persist +
  return updated DTO; illegal → 422 with clear message; finished game → 409.
  *Verify:* play `e2e4`; history has `e4`, turn flips. Send `e2e5` → 422 with
  message.
- [ ] **3.4 Legal-moves endpoint.** `GET /api/games/{id}/legal-moves?from=e2`.
  *Verify:* returns `e3,e4` from the start position.
- [ ] **3.5 List games.** `GET /api/games?status=in_progress|finished` returns
  summaries (§6.1).
  *Verify:* create two games; list shows both; filter by status works.
- [ ] **3.6 Stats.** `GET /api/stats` returns P1/P2 wins and draws over finished
  games.
  *Verify:* drive a game to checkmate via the API; stats reflect one win for the
  correct player.
- [ ] **3.7 Error contract.** Uniform `{error:{code,message}}` with the statuses
  in §6.2.
  *Verify:* trigger each error and confirm status + code.

## Phase 4 — Frontend: board & single-game play

- [ ] **4.1 Static serving + page shell.** `index.html` with board container and
  right-side history panel; Flask serves the frontend.
  *Verify:* opening the app shows the empty layout in the browser.
- [ ] **4.2 SVG pixel-art pieces.** `pieces.js` with all 12 piece SVGs
  (color × type).
  *Verify:* a test render shows all pieces crisply on light/dark squares.
- [ ] **4.3 Render board from FEN.** `board.js` draws the 8×8 board and places
  pieces from a DTO's `fen`.
  *Verify:* loading a game renders the standard starting position correctly.
- [ ] **4.4 Turn indicator.** Show whose turn it is (color + Player label) from
  `turn` / `turn_player`.
  *Verify:* indicator reads "White — Player 1" at start; flips after a move.
- [ ] **4.5 Select + highlight.** Clicking a side-to-move piece highlights its
  legal destinations (from DTO `legal_moves`).
  *Verify:* clicking `e2` pawn highlights `e3`/`e4`; clicking an opponent piece
  highlights nothing.
- [ ] **4.6 Submit move + repaint.** Click a highlighted square → POST move →
  repaint from returned DTO; auto-clear selection.
  *Verify:* a full legal move updates the board and the turn indicator.
- [ ] **4.7 Invalid-move message.** On 422, show `error.message` clearly; board
  unchanged.
  *Verify:* force an illegal move path; message appears; position unchanged.
- [ ] **4.8 Promotion chooser.** When target move is `promotion`, prompt Q/R/B/N
  and submit the choice.
  *Verify:* march a pawn to the last rank; choosing "Knight" places a knight.
- [ ] **4.9 Check / checkmate / draw banners.** Show a check notice; on
  `finished`, announce winner or draw type and lock the board.
  *Verify:* reproduce a check (banner) and a fool's mate (winner banner + locked
  board); a stalemate FEN game shows a draw banner.

## Phase 5 — Move history panel (chat style)

- [ ] **5.1 Render history.** Chat-style list from DTO `move_history` (move
  number, side, SAN); auto-scroll to latest.
  *Verify:* after several moves the panel matches the game and scrolls to the
  newest entry.

## Phase 6 — Lobby: multiple games, history & stats

- [ ] **6.1 Create-game UI.** Form/modal to pick Player 1's color + optional
  alias; on submit, open the new game.
  *Verify:* creating a game with alias "Test" opens it and it appears in the
  active list.
- [ ] **6.2 Active games list.** Show all `in_progress` games (id, alias, whose
  turn, created); clicking one opens it.
  *Verify:* two concurrent games both appear; switching between them preserves
  each board/history.
- [ ] **6.3 Finished-games history.** List finished games showing **only the
  winner** (P1 / P2 / Draw).
  *Verify:* a finished game appears with the correct winner and no move list.
- [ ] **6.4 Statistics view.** Show P1 wins, P2 wins, draws from `/api/stats`.
  *Verify:* counts match the finished-games outcomes.

## Phase 7 — Polish & verification

- [ ] **7.1 Full manual E2E.** Play a complete game start→checkmate in the
  browser, exercising highlight, invalid move, promotion, check/mate, history,
  lists, and stats.
  *Verify:* the TECH_DESIGN §10 manual checklist passes end-to-end.
- [ ] **7.2 Restart persistence.** Restart the server mid-game; reopen the game.
  *Verify:* the board and history are fully restored from the DB.
- [ ] **7.3 README.** How to install, run, and play.
  *Verify:* a fresh clone can be run following only the README.

---

### Suggested milestones
- **M1 (Phases 0–2):** rules engine proven by unit tests.
- **M2 (Phase 3):** full API playable via `curl`.
- **M3 (Phases 4–5):** one game fully playable in the browser.
- **M4 (Phases 6–7):** multiple games, history, stats, and polish.
