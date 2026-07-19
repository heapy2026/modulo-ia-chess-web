/**
 * Current-game controller (TECH_DESIGN §7 interaction loop): loads a game,
 * renders it, and drives the select -> highlight -> submit -> repaint cycle.
 * The server is the single source of truth; this module never decides move
 * legality itself, only filters the DTO's precomputed `legal_moves`.
 */

(function () {
  const boardEl = document.getElementById("board");
  const turnIndicatorEl = document.getElementById("turn-indicator");
  const bannerEl = document.getElementById("banner");
  const invalidMoveEl = document.getElementById("invalid-move-message");
  const promotionModalEl = document.getElementById("promotion-modal");

  let currentGame = null;
  let selectedSquare = null;
  let pendingPromotion = null; // { from, to }
  let invalidMoveTimer = null;

  function isWhitePiece(piece) {
    return piece === piece.toUpperCase();
  }

  function isPieceOfSideToMove(piece, turn) {
    return (turn === "white") === isWhitePiece(piece);
  }

  function render() {
    const dto = currentGame;
    const highlights = selectedSquare
      ? dto.legal_moves.filter((move) => move.from === selectedSquare).map((move) => move.to)
      : [];

    renderBoard(boardEl, dto.fen, {
      selected: selectedSquare,
      highlights,
      onSquareClick: dto.status === "finished" ? null : handleSquareClick,
    });

    renderTurnIndicator(dto);
    renderBanner(dto);
  }

  function renderTurnIndicator(dto) {
    const colorLabel = dto.turn === "white" ? "White" : "Black";
    const playerLabel = dto.turn_player === "player1" ? "Player 1" : "Player 2";
    turnIndicatorEl.textContent = `${colorLabel} — ${playerLabel}`;
  }

  function formatTermination(termination) {
    return (termination || "").replace(/_/g, " ");
  }

  function renderBanner(dto) {
    if (dto.status === "finished") {
      const text =
        dto.result === "draw"
          ? `Draw — ${formatTermination(dto.termination)}`
          : `${dto.result === "player1" ? "Player 1" : "Player 2"} wins — ${formatTermination(dto.termination)}`;
      bannerEl.textContent = text;
      bannerEl.className = "banner finished";
    } else if (dto.in_check) {
      bannerEl.textContent = "Check!";
      bannerEl.className = "banner check";
    } else {
      bannerEl.textContent = "";
      bannerEl.className = "banner hidden";
    }
  }

  function showInvalidMove(message) {
    invalidMoveEl.textContent = message;
    invalidMoveEl.classList.remove("hidden");
    clearTimeout(invalidMoveTimer);
    invalidMoveTimer = setTimeout(clearInvalidMove, 4000);
  }

  function clearInvalidMove() {
    invalidMoveEl.textContent = "";
    invalidMoveEl.classList.add("hidden");
    clearTimeout(invalidMoveTimer);
  }

  function showPromotionModal() {
    promotionModalEl.classList.remove("hidden");
  }

  function hidePromotionModal() {
    promotionModalEl.classList.add("hidden");
  }

  promotionModalEl.addEventListener("click", (event) => {
    const piece = event.target.dataset.piece;
    if (!piece || !pendingPromotion) return;
    const { from, to } = pendingPromotion;
    pendingPromotion = null;
    hidePromotionModal();
    submitMove(from, to, piece);
  });

  function handleSquareClick(square, piece) {
    const dto = currentGame;
    const isOwnPiece = Boolean(piece) && isPieceOfSideToMove(piece, dto.turn);

    if (selectedSquare) {
      if (square === selectedSquare) {
        selectedSquare = null;
        render();
        return;
      }

      const move = dto.legal_moves.find((m) => m.from === selectedSquare && m.to === square);
      if (move) {
        const from = selectedSquare;
        selectedSquare = null;
        if (move.promotion) {
          pendingPromotion = { from, to: square };
          render();
          showPromotionModal();
        } else {
          submitMove(from, square, null);
        }
        return;
      }

      if (isOwnPiece) {
        selectedSquare = square;
        render();
        return;
      }

      // Not a pre-highlighted destination: submit anyway and let the server
      // be the final arbiter (TECH_DESIGN §1 — highlighting is a convenience,
      // not client-side validation). This also surfaces genuine 422s.
      const from = selectedSquare;
      selectedSquare = null;
      submitMove(from, square, null);
      return;
    }

    selectedSquare = isOwnPiece ? square : null;
    render();
  }

  async function submitMove(from, to, promotion) {
    try {
      currentGame = await api.submitMove(currentGame.id, { from, to, promotion });
      clearInvalidMove();
    } catch (err) {
      showInvalidMove(err.message);
    }
    render();
  }

  async function init() {
    const params = new URLSearchParams(window.location.search);
    const existingId = params.get("game");

    if (existingId) {
      currentGame = await api.getGame(existingId);
    } else {
      currentGame = await api.createGame("white", null);
      params.set("game", currentGame.id);
      window.history.replaceState(null, "", `?${params.toString()}`);
    }

    render();
  }

  init();
})();
