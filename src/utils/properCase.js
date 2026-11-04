// Team names and their cities in capitals wherever a chart prints a word:
// the word lists are lowercased for counting ("aces", "indiana fever"), and
// only the people and places the network knows come back capitalised. The
// nicknames that are also ordinary words (sun, storm, sky, fire, dream, wings)
// are almost always the teams in this coverage — except in the words tied
// to a player ("Carrington fires back"), where a chart can keep them as words.
const TEAMS = [
	"aces",
	"fever",
	"sky",
	"liberty",
	"lynx",
	"mercury",
	"storm",
	"sparks",
	"dream",
	"wings",
	"sun",
	"mystics",
	"valkyries",
	"tempo",
	"fire"
];
const CITIES = [
	"las vegas",
	"vegas",
	"indiana",
	"chicago",
	"new york",
	"minnesota",
	"phoenix",
	"seattle",
	"los angeles",
	"atlanta",
	"dallas",
	"connecticut",
	"washington",
	"golden state",
	"toronto",
	"portland",
	"indianapolis"
];
const RX = new RegExp(
	"(^|[^a-z])(" +
		[...CITIES, ...TEAMS].sort((a, b) => b.length - a.length).join("|") +
		")(?![a-z])",
	"g"
);

// the nicknames that are also ordinary words
const WORDLIKE = new Set([
	"sky",
	"storm",
	"sparks",
	"dream",
	"wings",
	"sun",
	"fire",
	"tempo",
	"liberty",
	"mercury"
]);

// a nickname that is also a verb, followed by its particle, is the verb:
// "fire off" (a tweet), "storm off", "sparks up"
const PARTICLE = /^\s+(off|up|back|out|away|down|at|on|over|through)\b/;

// nicknamesAsWords: leave the word-like nicknames in lowercase
export function properCase(word, { nicknamesAsWords = false } = {}) {
	if (typeof word !== "string") return word;
	return word.replace(RX, (m, before, name, offset, whole) => {
		if (PARTICLE.test(whole.slice(offset + m.length))) return m;
		if (nicknamesAsWords && WORDLIKE.has(name)) return m;
		return (
			before + name.replace(/(^|\s)([a-z])/g, (x, s, c) => s + c.toUpperCase())
		);
	});
}
