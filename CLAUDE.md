# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

Greenfield. As of this writing the repo contains **only design docs** under
`docs/` — no code exists yet. `docs/PRD.md`, `docs/TECH_DESIGN.md`, and
`docs/TODO.md` are the authoritative spec; build against them and keep them in
sync when decisions change. `docs/TODO.md` defines the intended build order
(Phase 0 → 7) with a `Verify` step per task.

## What this is

A local **hotseat** (two players, same computer, turn-by-turn) chess game.
There is **no online play, no accounts, and no authentication** — this is a
deliberate constraint, not a missing feature. Do not add an auth/user layer.

## Stack & commands

Backend: Flask + `python-chess` (all rule validation) + SQLAlchemy over SQLite.
Frontend: vanilla HTML/CSS/JS, no framework, no build step; pieces are inline
pixel-art SVGs. Planned layout: `backend/`, `frontend/`, `docs/`.

Once scaffolded (see `docs/TODO.md` Phase 0), the expected commands are:

```bash
pip install -r requirements.txt        # flask, python-chess, SQLAlchemy, pytest
python backend/app.py                  # runs Flask; serves the API and frontend
pytest                                 # run the test suite
pytest tests/test_chess_service.py::test_name   # run a single test
curl localhost:5000/api/health         # smoke check
```

Confirm the actual command names against the code before relying on them — the
above reflect the design, and the scaffolding may name entry points differently.

## Git branching

- `main` is the principal branch. It stays as-is (no project work) while the
  build is in progress.
- All development happens on `develop`. Every phase's work is committed there,
  one commit per completed phase, only after the user has reviewed the code and
  confirmed it's good.

## Workflow

The `implement-phase` skill (`.claude/skills/implement-phase/`) is the intended
way to advance the build: it verifies the real starting point against the code
(never trusting TODO checkboxes alone), implements one whole phase with tests,
checks the boxes off, and — after the user reviews and confirms the code — commits
the phase to `develop`. Use it when asked to continue/implement the next phase.

## Architecture (the parts that span multiple files)

Read `docs/TECH_DESIGN.md` for the full contract. The load-bearing ideas:

- **Server is the single source of truth.** The frontend never validates chess
  rules for correctness. It may *pre-highlight* legal moves using data the
  server sends, but every move is POSTed, validated with `python-chess`, and the
  UI **repaints from the server's response**. This makes client desync
  impossible and keeps `board.js`/`game.js` free of chess logic.

- **State is the move list, not a snapshot.** A game persists its ordered **UCI
  move list** (`moves` table) as the authoritative state; the board is always
  **replayed** through `python-chess` on each request (there is no in-memory
  session — any request re-hydrates from the DB, so restarts and concurrent
  games just work). `Game.fen` is a *cached* convenience, always regenerable
  from the moves.

- **One canonical Game-State DTO.** Every state-returning endpoint returns the
  same JSON shape (see TECH_DESIGN §3.1: `fen`, `turn`, `turn_player`,
  `in_check`, `legal_moves`, `move_history`, `status`, `result`, `termination`).
  The frontend has a single render path that consumes it. When you add a field,
  add it to the DTO, not to a one-off response.

- **`chess_service.py` is the only module that imports `python-chess`.** Routes
  and models stay engine-agnostic; all rule logic (replay, legal-move listing,
  SAN, terminal detection, DTO assembly) lives there and is where unit tests
  focus.

- **Player 1 / Player 2 are fixed statistic labels; color is per-game.** Colors
  are chosen at game creation (`player1_color` / `player2_color`). A win is
  recorded by the winning *color* mapped through that assignment into
  `result` = `player1` | `player2` | `draw`. Stats are just counts over finished
  `games.result`.

## Product rules that are easy to get wrong

- Detect and announce **all** draw types, not just checkmate: stalemate,
  threefold repetition, fifty-move rule, insufficient material. Evaluate
  terminal conditions after every move (order in TECH_DESIGN §4.3).
- **Promotion prompts the user** for the piece (Q/R/B/N); moves carry a
  `promotion` field. Do not auto-queen.
- Illegal moves return **422** with `{error:{code,message}}`; the UI shows
  `message` verbatim and leaves the board unchanged. Full error contract in
  TECH_DESIGN §6.2.
- Board orientation is **fixed White-at-bottom** for both players (no auto-flip).

## Conventions

- **All code, comments, and docs in English** (per the project requirement),
  even though collaboration with the user happens in Spanish.
