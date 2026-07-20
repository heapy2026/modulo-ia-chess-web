/**
 * Pixel-art piece definitions (PRD §6: "Piece art: modern pixel-art style, SVG").
 *
 * Each piece is a fixed-size grid of filled/empty cells. Shared base rows give
 * every piece a common pedestal; the upper rows are the distinguishing shape.
 * getPieceSvg(color, type) renders the grid as an inline <svg> string.
 */

const PIECE_GRID_WIDTH = 11;
const PIECE_GRID_HEIGHT = 13;

// Rows 9-12: shared pedestal for every piece.
const PIECE_BASE_ROWS = [
  "...XXXXX...",
  "..XXXXXXX..",
  ".XXXXXXXXX.",
  "XXXXXXXXXXX",
];

const PIECE_TOP_ROWS = {
  p: [
    "....XXX....",
    "...XXXXX...",
    "...XXXXX...",
    "....XXX....",
    "....XXX....",
    "...XXXXX...",
    "..XXXXXXX..",
    "..XXXXXXX..",
    "..XXXXXXX..",
  ],
  n: [
    "......XXX..",
    ".....XXXXX.",
    "....XXXXXXX",
    "...XXXXXXXX",
    "..XXXXXXXXX",
    ".XXXXXXXXXX",
    "XXXXXXXXXXX",
    "..XXXXXXX..",
    "..XXXXXXX..",
  ],
  b: [
    ".....X.....",
    "....XXX....",
    "...XXXXX...",
    "...XX.XX...",
    "..XXXXXXX..",
    "..XXXXXXX..",
    "..XXXXXXX..",
    "..XXXXXXX..",
    "..XXXXXXX..",
  ],
  r: [
    "X.X.X.X.X.X",
    "XXXXXXXXXXX",
    ".XXXXXXXXX.",
    ".XXXXXXXXX.",
    "..XXXXXXX..",
    "..XXXXXXX..",
    "..XXXXXXX..",
    "..XXXXXXX..",
    "..XXXXXXX..",
  ],
  q: [
    "..X.X.X.X..",
    ".X.X.X.X.X.",
    "..XXXXXXX..",
    ".XXXXXXXXX.",
    ".X.X.X.X.X.",
    ".XXXXXXXXX.",
    "..XXXXXXX..",
    "..XXXXXXX..",
    "..XXXXXXX..",
  ],
  k: [
    "....XXX....",
    ".....X.....",
    "....XXX....",
    ".....X.....",
    "...XXXXX...",
    "..XXXXXXX..",
    ".XXXXXXXXX.",
    ".XXXXXXXXX.",
    "..XXXXXXX..",
  ],
};

const PIECE_COLORS = {
  white: "#f5f2e8",
  black: "#2b2b2b",
};

function getPieceGrid(type) {
  return [...PIECE_TOP_ROWS[type], ...PIECE_BASE_ROWS];
}

// Merge each row's runs of filled cells into single rects so adjacent pixels
// don't get a seam between them — keeps edges crisp instead of hatched.
function getPieceRowSpans(grid) {
  const spans = [];
  grid.forEach((row, rowIndex) => {
    let runStart = null;
    for (let colIndex = 0; colIndex <= row.length; colIndex++) {
      const filled = row[colIndex] === "X";
      if (filled && runStart === null) {
        runStart = colIndex;
      } else if (!filled && runStart !== null) {
        spans.push({ x: runStart, y: rowIndex, width: colIndex - runStart });
        runStart = null;
      }
    }
  });
  return spans;
}

function getPieceSvg(color, type) {
  const grid = getPieceGrid(type);
  const fill = PIECE_COLORS[color];
  const rects = getPieceRowSpans(grid)
    .map((span) => `<rect x="${span.x}" y="${span.y}" width="${span.width}" height="1" />`)
    .join("");
  return (
    `<svg class="piece piece-${color}" viewBox="0 0 ${PIECE_GRID_WIDTH} ${PIECE_GRID_HEIGHT}" ` +
    `xmlns="http://www.w3.org/2000/svg" shape-rendering="crispEdges" fill="${fill}">` +
    `<g>${rects}</g></svg>`
  );
}
