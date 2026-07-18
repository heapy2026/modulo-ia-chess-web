# PRD — Local Two-Player Web Chess

## 1. Overview

A browser-based chess game for **two people playing turn-by-turn on the same
computer** (hotseat / pass-and-play). There is no online multiplayer, no
matchmaking and no user accounts. Because the experience is fully local, the
backend does **not** implement authentication or user identity.

The application supports **multiple concurrent games**, each with its own
identifier, plus a history of finished games with win statistics.

## 2. Goals

- Provide a correct, rules-complete chess experience validated server-side.
- Make the current turn, legal moves, checks and game endings unmistakably clear.
- Let two people manage several games at once and revisit results afterward.

## 3. Non-Goals

- Online / remote play, spectators, or real-time sync between devices.
- User accounts, login, or authentication.
- AI opponent / engine analysis.
- Clocks / time controls.
- Move takebacks (undo) or in-game editing of positions.

## 4. Personas

- **Two local players** sharing one keyboard and screen. They are referred to
  throughout as **Player 1** and **Player 2**. These are fixed labels used for
  statistics; the *color* each one plays is chosen per game (see 5.1).

## 5. Functional Requirements

### 5.1 Game creation

- The user can create a new game at any time.
- On creation the user chooses **which color each player takes** (Player 1 =
  White or Player 1 = Black; the other player gets the remaining color).
- The user may optionally give the game an **alias** (a human-friendly name) to
  recognize it in the active-games list. The alias is not required and does not
  need to be unique.
- Each game receives a server-generated **unique identifier** (short UUID).
- A new game starts from the standard chess initial position with White to move.

### 5.2 Playing a move

- The board shows both players' pieces from White's perspective (bottom = White).
- The UI clearly indicates **whose turn it is** (color + which Player label).
- Selecting one of the side-to-move's pieces **highlights all its legal moves**.
- Clicking a highlighted target square performs the move.
- All move legality is **validated on the backend** using `python-chess`. The
  frontend highlighting is a convenience; the server is the source of truth.
- If the user attempts an **illegal move**, a **clear, explicit message** is
  shown and the board state is unchanged.
- **Pawn promotion:** when a pawn reaches the last rank, the player is prompted
  to **choose the promotion piece** (Queen, Rook, Bishop, or Knight). The move
  is only submitted once a piece is chosen.
- **Special moves** must all be supported through `python-chess`: castling
  (king- and queen-side), en passant, and promotion.

### 5.3 Check, checkmate and draw notifications

- When a move leaves a king **in check**, the UI notifies the player clearly.
- When a move produces **checkmate**, the UI announces the winner and the game
  becomes **finished**.
- The game must also detect and announce **all draw conditions** supported by
  `python-chess`:
  - Stalemate
  - Threefold repetition
  - Fifty-move rule
  - Insufficient material
- On any terminal condition the game transitions to **finished** and no further
  moves are accepted.

### 5.4 Move history (chat-style panel)

- A panel on the **right side** of the board shows the **move history** of the
  current game in a **chat-like** layout.
- Each entry shows the move in **SAN** (Standard Algebraic Notation), grouped or
  labeled by move number and side.
- The panel updates immediately after each accepted move and auto-scrolls to the
  latest move.

### 5.5 Multiple concurrent games

- Multiple games can exist **simultaneously**, each independently playable.
- The user can view a list of **active (in-progress) games**, showing at least:
  identifier, alias (if any), color assignment, whose turn it is, and created time.
- Selecting an active game loads its current board and move history so play can
  continue.

### 5.6 Finished-games history and statistics

- A **history of finished games** lists, for each game, **only who won**
  (Player 1, Player 2, or Draw) — no full move list is required in this view.
- **Statistics** are shown: number of games won by **Player 1**, number won by
  **Player 2**, and number of **draws**.

## 6. UX Requirements

- **Turn indicator:** always visible; states whose move it is (color + Player).
- **Legal-move highlighting:** visible affordance on selecting a piece.
- **Invalid-move feedback:** a clear, transient, human-readable message.
- **Check / checkmate / draw banners:** prominent and unambiguous.
- **Piece art:** modern **pixel-art** style, drawn as **SVG** pieces.
- Layout: board on the left/center, chat-style move history on the right.

## 7. Technical Constraints

- **Backend:** Python + **Flask**; **`python-chess`** for all rule validation;
  **SQLite** via **SQLAlchemy** for persistence.
- **Frontend:** vanilla **HTML + CSS + JavaScript** (no framework); pieces as SVG.
- **Backend testing:** unit tests written with **`pytest`** are a required
  deliverable, not optional polish. Every testable backend function (rule
  logic, model helpers, DTO assembly, etc.) must have a unit test; HTTP/API
  endpoints are out of scope for this unit-test requirement — see
  TECH_DESIGN §10.
- **All code, documents and comments in English.**
- No authentication layer (local game).

## 8. Assumptions & Defaults (not explicitly requested, chosen here)

- Board orientation is **fixed to White at the bottom** for both players
  (no auto-flip on turn), to keep the hotseat UI stable.
- **Game state is authoritative on the server.** The canonical representation is
  the game's move list / FEN; the frontend renders from server responses.
- Aliases are **optional and non-unique**.
- There is **no undo** and **no resign/draw-offer** flow in v1 (only natural
  game endings). Abandoning a game simply leaves it "active".
- Deleting games is **out of scope** for v1.

## 9. Acceptance Criteria (per feature)

| # | Feature | Done when… |
|---|---------|-----------|
| 1 | Create game | Creating returns a unique id; color choice + optional alias persist; new game shows starting position, White to move. |
| 2 | Turn indicator | Indicator always reflects the side to move and the correct Player label. |
| 3 | Legal-move highlight | Selecting a side-to-move piece highlights exactly its legal destinations. |
| 4 | Move submission | A legal move updates board + history; the backend rejects illegal moves with a clear message and no state change. |
| 5 | Promotion | Reaching last rank prompts a piece choice; chosen piece appears on the board. |
| 6 | Check/checkmate | Check is announced; checkmate ends the game and records the winner. |
| 7 | Draws | Stalemate, threefold, fifty-move, and insufficient material each end the game as a draw. |
| 8 | History panel | Chat-style SAN history matches the actual game and auto-scrolls. |
| 9 | Active games | The active list shows all in-progress games and can reopen any of them. |
| 10 | Finished history | Finished list shows winner-only per game. |
| 11 | Statistics | P1 wins, P2 wins, and draw counts are correct after games finish. |

## 10. Out of Scope (v1)

Online play, accounts/auth, AI, clocks, undo, resign/draw offers, game deletion,
board flipping, and PGN import/export.
