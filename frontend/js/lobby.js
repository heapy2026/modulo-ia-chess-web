/**
 * Lobby controller (TECH_DESIGN §7): create-game form, active-games list,
 * finished-games history (winner only), and the statistics view. Also owns
 * the single piece of client-side routing this app has — switching between
 * the lobby and a single game via the `?game=<id>` query param — since it is
 * the entry point when no game is loaded.
 */

(function () {
  const lobbyViewEl = document.getElementById("lobby-view");
  const gameViewEl = document.getElementById("game-view");
  const gameHeaderControlsEl = document.getElementById("game-header-controls");
  const backToLobbyEl = document.getElementById("back-to-lobby");

  const createFormEl = document.getElementById("create-game-form");
  const colorSelectEl = document.getElementById("create-game-color");
  const aliasInputEl = document.getElementById("create-game-alias");

  const activeListEl = document.getElementById("active-games-list");
  const finishedListEl = document.getElementById("finished-games-list");

  const donutEl = document.getElementById("stats-donut");
  const donutTotalEl = document.getElementById("stats-total");
  const legendEl = document.getElementById("stats-legend");
  const tooltipEl = document.getElementById("chart-tooltip");

  const SVG_NS = "http://www.w3.org/2000/svg";
  const DONUT_CENTER = 80;
  const DONUT_RADIUS = 60;
  const DONUT_STROKE = 28;
  const DONUT_GAP_PX = 3; // surface gap between segments, in stroke-length px
  const DONUT_CIRCUMFERENCE = 2 * Math.PI * DONUT_RADIUS;

  // Fixed categorical order (never reassigned by value/rank), validated for
  // CVD + contrast against the app's dark panel surface (#20242b): see
  // frontend/css/style.css --stat-player1/--stat-player2/--stat-draw.
  const RESULT_CATEGORIES = [
    { key: "player1_wins", label: "Player 1 wins", varName: "--stat-player1" },
    { key: "player2_wins", label: "Player 2 wins", varName: "--stat-player2" },
    { key: "draws", label: "Draws", varName: "--stat-draw" },
  ];

  function formatCreatedAt(isoString) {
    const date = new Date(isoString);
    return Number.isNaN(date.getTime()) ? isoString : date.toLocaleString();
  }

  function resultLabel(result) {
    if (result === "player1") return "Player 1";
    if (result === "player2") return "Player 2";
    if (result === "draw") return "Draw";
    return "Unknown";
  }

  function turnLabel(summary) {
    const color = summary.turn_player === "player1" ? summary.player1_color : summary.player2_color;
    const colorLabel = color === "white" ? "White" : "Black";
    const playerLabel = summary.turn_player === "player1" ? "Player 1" : "Player 2";
    return `${colorLabel} to move — ${playerLabel}`;
  }

  function renderPlaceholder(listEl, text) {
    listEl.innerHTML = "";
    const li = document.createElement("li");
    li.className = "placeholder";
    li.textContent = text;
    listEl.appendChild(li);
  }

  function renderActiveGames(games) {
    activeListEl.innerHTML = "";
    if (games.length === 0) {
      renderPlaceholder(activeListEl, "No active games yet.");
      return;
    }

    games.forEach((game) => {
      const li = document.createElement("li");
      li.className = "game-list-entry";
      li.tabIndex = 0;

      const titleEl = document.createElement("span");
      titleEl.className = "game-list-title";
      titleEl.textContent = game.alias || `Game ${game.id}`;

      const metaEl = document.createElement("span");
      metaEl.className = "game-list-meta";
      metaEl.textContent = `${turnLabel(game)} · created ${formatCreatedAt(game.created_at)}`;

      li.append(titleEl, metaEl);
      li.addEventListener("click", () => openGame(game.id));
      li.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openGame(game.id);
        }
      });
      activeListEl.appendChild(li);
    });
  }

  function renderFinishedGames(games) {
    finishedListEl.innerHTML = "";
    if (games.length === 0) {
      renderPlaceholder(finishedListEl, "No finished games yet.");
      return;
    }

    games.forEach((game) => {
      const li = document.createElement("li");
      li.className = "game-list-entry finished";

      const titleEl = document.createElement("span");
      titleEl.className = "game-list-title";
      titleEl.textContent = game.alias || `Game ${game.id}`;

      const metaEl = document.createElement("span");
      metaEl.className = "game-list-meta";
      metaEl.textContent = `Winner: ${resultLabel(game.result)}`;

      li.append(titleEl, metaEl);
      finishedListEl.appendChild(li);
    });
  }

  function showChartTooltip(target, text) {
    tooltipEl.textContent = text;
    tooltipEl.classList.remove("hidden");
    const targetRect = target.getBoundingClientRect();
    const tooltipRect = tooltipEl.getBoundingClientRect();
    tooltipEl.style.left = `${targetRect.left + targetRect.width / 2 - tooltipRect.width / 2}px`;
    tooltipEl.style.top = `${targetRect.top - tooltipRect.height - 8}px`;
  }

  function hideChartTooltip() {
    tooltipEl.classList.add("hidden");
  }

  function donutArcPath(startAngle, endAngle) {
    const toXY = (angleDeg) => {
      const rad = ((angleDeg - 90) * Math.PI) / 180;
      return [DONUT_CENTER + DONUT_RADIUS * Math.cos(rad), DONUT_CENTER + DONUT_RADIUS * Math.sin(rad)];
    };
    const [startX, startY] = toXY(startAngle);
    const [endX, endY] = toXY(endAngle);
    const largeArc = endAngle - startAngle > 180 ? 1 : 0;
    return `M ${startX} ${startY} A ${DONUT_RADIUS} ${DONUT_RADIUS} 0 ${largeArc} 1 ${endX} ${endY}`;
  }

  function renderDonutSegment(category, count, percent, gapDeg) {
    const path = document.createElementNS(SVG_NS, "path");
    const sweepDeg = (percent / 100) * 360;
    const trimmedSweep = Math.max(sweepDeg - gapDeg, 0);
    path.setAttribute("d", donutArcPath(0, trimmedSweep || 0.001));
    path.setAttribute("class", "donut-segment");
    path.style.stroke = `var(${category.varName})`;
    path.setAttribute("stroke-width", DONUT_STROKE);
    path.setAttribute("fill", "none");
    path.setAttribute("stroke-linecap", "round");
    path.setAttribute("tabindex", "0");
    path.setAttribute("role", "img");
    const description = `${category.label}: ${count} (${percent.toFixed(1)}%)`;
    path.setAttribute("aria-label", description);

    const show = () => showChartTooltip(path, description);
    path.addEventListener("pointerenter", show);
    path.addEventListener("focus", show);
    path.addEventListener("pointerleave", hideChartTooltip);
    path.addEventListener("blur", hideChartTooltip);
    return path;
  }

  function renderLegend(stats, total) {
    legendEl.innerHTML = "";
    RESULT_CATEGORIES.forEach((category) => {
      const count = stats[category.key];
      const percent = total > 0 ? (count / total) * 100 : 0;

      const li = document.createElement("li");
      li.className = "stats-legend-entry";

      const swatchEl = document.createElement("span");
      swatchEl.className = "legend-swatch";
      swatchEl.style.background = `var(${category.varName})`;

      const labelEl = document.createElement("span");
      labelEl.className = "legend-label";
      labelEl.textContent = category.label;

      const valueEl = document.createElement("span");
      valueEl.className = "legend-value";
      valueEl.textContent = total > 0 ? `${count} (${percent.toFixed(0)}%)` : String(count);

      li.append(swatchEl, labelEl, valueEl);
      legendEl.appendChild(li);
    });
  }

  function renderStats(stats) {
    const total = stats.player1_wins + stats.player2_wins + stats.draws;
    donutTotalEl.textContent = total;
    donutEl.innerHTML = "";

    if (total === 0) {
      const emptyRing = document.createElementNS(SVG_NS, "circle");
      emptyRing.setAttribute("cx", DONUT_CENTER);
      emptyRing.setAttribute("cy", DONUT_CENTER);
      emptyRing.setAttribute("r", DONUT_RADIUS);
      emptyRing.setAttribute("fill", "none");
      emptyRing.setAttribute("class", "donut-empty-ring");
      emptyRing.setAttribute("stroke-width", DONUT_STROKE);
      donutEl.appendChild(emptyRing);
      renderLegend(stats, total);
      return;
    }

    const gapDeg = (DONUT_GAP_PX / DONUT_CIRCUMFERENCE) * 360;
    const group = document.createElementNS(SVG_NS, "g");
    let cumulativeAngle = 0;

    RESULT_CATEGORIES.forEach((category) => {
      const count = stats[category.key];
      const percent = (count / total) * 100;
      const sweepDeg = (percent / 100) * 360;
      if (sweepDeg > 0) {
        const segment = renderDonutSegment(category, count, percent, gapDeg);
        segment.setAttribute("transform", `rotate(${cumulativeAngle} ${DONUT_CENTER} ${DONUT_CENTER})`);
        group.appendChild(segment);
      }
      cumulativeAngle += sweepDeg;
    });

    donutEl.appendChild(group);
    renderLegend(stats, total);
  }

  async function refreshLobby() {
    const [active, finished, stats] = await Promise.all([
      api.listGames("in_progress"),
      api.listGames("finished"),
      api.getStats(),
    ]);
    renderActiveGames(active);
    renderFinishedGames(finished);
    renderStats(stats);
  }

  function setUrlGameParam(gameId) {
    const params = new URLSearchParams(window.location.search);
    if (gameId) {
      params.set("game", gameId);
    } else {
      params.delete("game");
    }
    const query = params.toString();
    window.history.replaceState(null, "", query ? `?${query}` : window.location.pathname);
  }

  function showLobby() {
    setUrlGameParam(null);
    gameViewEl.classList.add("hidden");
    gameHeaderControlsEl.classList.add("hidden");
    lobbyViewEl.classList.remove("hidden");
    refreshLobby();
  }

  function openGame(gameId) {
    setUrlGameParam(gameId);
    lobbyViewEl.classList.add("hidden");
    gameHeaderControlsEl.classList.remove("hidden");
    gameViewEl.classList.remove("hidden");
    window.GameController.open(gameId);
  }

  createFormEl.addEventListener("submit", async (event) => {
    event.preventDefault();
    const alias = aliasInputEl.value.trim() || null;
    const game = await api.createGame(colorSelectEl.value, alias);
    aliasInputEl.value = "";
    openGame(game.id);
  });

  backToLobbyEl.addEventListener("click", showLobby);

  function init() {
    const params = new URLSearchParams(window.location.search);
    const existingId = params.get("game");
    if (existingId) {
      gameHeaderControlsEl.classList.remove("hidden");
      gameViewEl.classList.remove("hidden");
      lobbyViewEl.classList.add("hidden");
      window.GameController.open(existingId);
    } else {
      showLobby();
    }
  }

  init();
})();
