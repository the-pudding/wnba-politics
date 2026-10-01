// Robustness checks kept off the published page: with ?checks in the address
// (localhost:5173/?checks), the charts show their check controls again — the
// with/without college toggles (Fightin' Words, player words, dot plot) and
// Fightin' Words' "Leave out" (game words, names). Set on the client only, so
// the server render never shows them (2026-10-01).
export const checks = $state({ on: false });

if (typeof window !== "undefined")
	checks.on = new URLSearchParams(window.location.search).has("checks");
