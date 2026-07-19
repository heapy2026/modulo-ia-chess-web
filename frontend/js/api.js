/**
 * Fetch wrappers for the /api endpoints this phase's UI needs. Every state
 * response is the canonical Game-State DTO (TECH_DESIGN §3.1); errors surface
 * as {error:{code,message}} (§6.2) and are re-thrown as Error(message).
 */

async function apiRequest(url, { method = "GET", body } = {}) {
  const response = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error((data.error && data.error.message) || "Request failed.");
  }
  return data;
}

const api = {
  createGame(player1Color, alias) {
    return apiRequest("/api/games", {
      method: "POST",
      body: { player1_color: player1Color, alias: alias || null },
    });
  },

  getGame(id) {
    return apiRequest(`/api/games/${id}`);
  },

  submitMove(id, { from, to, promotion }) {
    return apiRequest(`/api/games/${id}/moves`, {
      method: "POST",
      body: { from, to, promotion: promotion || null },
    });
  },
};
