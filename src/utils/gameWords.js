// Game vocabulary: the box score, results, the court, and the teams and
// cities a game recap names. The Fightin' Words chart can hide any word or
// phrase with one of these in it, so what is left on each side is how the
// coverage talks about the league rather than the games (2026-09-30).
// Left in on purpose: fouls (part of the story being told), and the
// business of the league (draft, contract, trade, coach, rookie, salary).
const STATS = [
	"point", "points", "pts", "rebound", "rebounds", "rebounding", "rebounder", "boards",
	"assist", "assists", "steal", "steals", "block", "blocks", "blocked", "turnover", "turnovers",
	"score", "scored", "scores", "scoring", "scorer", "scorers", "shot", "shots", "shoot", "shooting",
	"shooter", "shot-making", "three", "threes", "3-pointer", "3-pointers", "three-pointer",
	"three-pointers", "3s", "field", "goal", "goals", "free", "throw", "throws", "minutes", "min",
	"percent", "pct", "averaging", "averaged", "average", "averages", "per", "career-high",
	"season-high", "double-double", "triple-double", "double-doubles", "triple-doubles", "stat",
	"stats", "efficient", "efficiency", "attempts", "made", "makes", "missed", "misses", "jumper",
	"layup", "layups", "dunk", "dunks", "basket", "baskets", "bucket", "buckets", "paint",
	"possession", "possessions", "offense", "offensive", "defense", "defensive", "transition",
	"pick-and-roll", "fast-break", "rotation", "bench", "starter", "starters", "starting", "lineup",
	"pointer", "pointers", "mvp", "all-star", "all-wnba", "team", "teams", "left", "seconds",
	// counts and ordinals spelled out: "four rebounds", "third quarter"
	"two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
	"first", "second", "third", "fourth", "fifth", "last"
];
const RESULTS = [
	"game", "games", "quarter", "quarters", "half", "halftime", "overtime", "ot", "lead", "leads",
	"led", "leading", "trailed", "trailing", "deficit", "run", "win", "wins", "won", "winning",
	"loss", "losses", "lost", "losing", "beat", "beats", "beating", "victory", "defeat", "defeated",
	"rally", "rallied", "streak", "straight", "consecutive", "season", "regular", "playoff",
	"playoffs", "postseason", "series", "standings", "seed", "clinch", "clinched",
	"matchup", "tipoff", "home", "road", "schedule", "final", "finals", "semifinals", "round",
	"night", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
];
const TEAMS = [
	"aces", "liberty", "lynx", "mercury", "storm", "wings", "dream", "sky", "sun", "fever",
	"mystics", "sparks", "valkyries", "tempo", "fire",
	"vegas", "minnesota", "phoenix", "seattle", "dallas", "atlanta", "chicago",
	"connecticut", "indiana", "toronto", "portland", "brooklyn", "barclays", "uncasville",
	"indianapolis", "arlington", "washington"
];
const GAME = new Set([...STATS, ...RESULTS, ...TEAMS]);
// place names of more than one word, matched whole ("state" and "new" alone
// are ordinary words). Washington is in TEAMS: in these articles it is the
// Mystics far more often than the capital, and the Post's own name is a stopword
const PLACES = /\b(las vegas|new york|los angeles|golden state)\b/;
// phrases that carry a game word but are about the league's business
const KEEP = /\b(free agen(cy|ts?)|dream come true|white house|first lady)\b/;

// a word or phrase is game vocabulary when any of its words is, or it
// carries a number ("20 points", "3-for-7")
export function isGameTerm(term) {
	const t = String(term).toLowerCase();
	if (KEEP.test(t)) return false;
	if (PLACES.test(t)) return true;
	return t.split(/\s+/).some((w) => GAME.has(w.replace(/['’]s$/, "")) || /\d/.test(w));
}
