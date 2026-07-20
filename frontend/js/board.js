/**
 * Board renderer: draws the 8x8 grid and places pieces from a FEN string.
 * Board orientation is fixed White-at-bottom (PRD §8), so rank 8 is the top
 * row and rank 1 is the bottom row, which matches FEN's row order directly.
 */

const BOARD_FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];

function parseFenPlacement(fen) {
  const placement = fen.split(" ")[0];
  return placement.split("/").map((row) => {
    const cells = [];
    for (const ch of row) {
      if (/[1-8]/.test(ch)) {
        for (let i = 0; i < Number(ch); i++) cells.push(null);
      } else {
        cells.push(ch);
      }
    }
    return cells;
  });
}

function squareNameAt(rankIndex, fileIndex) {
  const rank = 8 - rankIndex;
  return `${BOARD_FILES[fileIndex]}${rank}`;
}

/**
 * @param {HTMLElement} container
 * @param {string} fen
 * @param {{selected?: string|null, highlights?: string[], onSquareClick?: (square: string, piece: string|null) => void}} options
 */
function renderBoard(container, fen, options = {}) {
  const { selected = null, highlights = [], onSquareClick = null } = options;
  const rows = parseFenPlacement(fen);

  container.innerHTML = "";
  rows.forEach((row, rankIndex) => {
    row.forEach((piece, fileIndex) => {
      const square = squareNameAt(rankIndex, fileIndex);
      const isLight = (rankIndex + fileIndex) % 2 === 0;

      const squareEl = document.createElement("div");
      squareEl.className = `square ${isLight ? "light" : "dark"}`;
      squareEl.dataset.square = square;
      if (square === selected) squareEl.classList.add("selected");
      if (highlights.includes(square)) squareEl.classList.add("highlight");

      if (piece) {
        const color = piece === piece.toUpperCase() ? "white" : "black";
        const type = piece.toLowerCase();
        squareEl.insertAdjacentHTML("beforeend", getPieceSvg(color, type));
      }

      if (onSquareClick) {
        squareEl.addEventListener("click", () => onSquareClick(square, piece));
      }

      container.appendChild(squareEl);
    });
  });
}
