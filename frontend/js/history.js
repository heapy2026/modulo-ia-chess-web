/**
 * History panel renderer (PRD §5.4): chat-style SAN list built from the DTO's
 * `move_history`, White bubbles on the left / Black bubbles on the right,
 * grouped and labeled by move number and side, auto-scrolling to the latest.
 */

function renderHistory(container, moveHistory) {
  container.innerHTML = "";

  if (!moveHistory || moveHistory.length === 0) {
    const li = document.createElement("li");
    li.className = "placeholder";
    li.textContent = "Move history will appear here.";
    container.appendChild(li);
    return;
  }

  moveHistory.forEach((entry) => {
    const li = document.createElement("li");
    li.className = `history-entry ${entry.color}`;

    const numberEl = document.createElement("span");
    numberEl.className = "history-number";
    numberEl.textContent = `${entry.move_number}${entry.color === "white" ? "." : "..."}`;

    const sanEl = document.createElement("span");
    sanEl.className = "history-san";
    sanEl.textContent = entry.san;

    li.append(numberEl, sanEl);
    container.appendChild(li);
  });

  const scrollParent = container.closest(".history-panel") || container;
  scrollParent.scrollTop = scrollParent.scrollHeight;
}
