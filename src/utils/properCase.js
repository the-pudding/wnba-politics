// Team names and their cities in capitals wherever a chart prints a word:
// the word lists are lowercased for counting ("aces", "indiana fever"), and
// only the people and places the network knows come back capitalised. The
// nicknames that are also ordinary words (sun, storm, sky, fire, dream, wings)
// are almost always the teams in this coverage. (2026-09-29)
const TEAMS = [
	"aces", "fever", "sky", "liberty", "lynx", "mercury", "storm", "sparks", "dream",
	"wings", "sun", "mystics", "valkyries", "tempo", "fire"
];
const CITIES = [
	"las vegas", "vegas", "indiana", "chicago", "new york", "minnesota", "phoenix", "seattle",
	"los angeles", "atlanta", "dallas", "connecticut", "washington", "golden state", "toronto",
	"portland", "indianapolis"
];
const RX = new RegExp(
	"(^|[^a-z])(" + [...CITIES, ...TEAMS].sort((a, b) => b.length - a.length).join("|") + ")(?![a-z])",
	"g"
);

export function properCase(word) {
	if (typeof word !== "string") return word;
	return word.replace(RX, (m, before, name) =>
		before + name.replace(/(^|\s)([a-z])/g, (x, s, c) => s + c.toUpperCase())
	);
}
