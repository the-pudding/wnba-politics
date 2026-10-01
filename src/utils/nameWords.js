// People's names in a Fightin' Words list: the site's roster (players, coaches,
// media, politicians in data/people.json) plus the names that turn up in the
// chart's top words without being on it. The chart can hide any word or
// phrase with a name in it, to show what is said rather than who it is
// said about (2026-09-30).
import roster from "$data/people.json";

// surnames and first names that are also ordinary words ("white privilege",
// "young", "sky", "hill") only count as a name in the full name
const ORDINARY = new Set([
	"white", "cloud", "freedom", "bird", "young", "plum", "hill", "swift", "silver", "brink",
	"hull", "bout", "rice", "boston", "sky", "sun", "storm", "james", "thomas", "smith", "harris",
	"taylor", "sunny", "clay", "dawn", "kim", "joe", "paul", "lia", "stephen", "parker", "carter"
]);
// not on the roster but in the chart's top 150 words and phrases, capitalised
// mid-sentence in the articles at least 85% of the time (checked 2026-09-30)
const EXTRA = [
	"azzi fudd", "olivia miles", "lauren betts", "juju watkins", "kate martin", "christie sides",
	"natalie nakase", "sandy brondello", "noelle quinn", "pat summitt", "lisa bluder", "pat mcafee",
	"aaliyah edwards", "allisha gray", "chelsea gray", "ariel atkins", "bridget carleton",
	"charles barkley", "christine brennan", "dearica hamby", "elena delle donne", "delle donne",
	"skylar diggins", "dominique malonga", "gregg doyel", "elle duncan", "ezi magbegor",
	"gabby williams", "jackie young", "jessica shepard", "jonquel jones", "jordin canada",
	"kayla mcbride", "kayla thornton", "kiki iriafen", "leonie fiebich", "jewell loyd",
	"natisha hiedeman", "nneka ogwumike", "arike ogunbowale", "rhyne howard", "rickea jackson",
	"satou sabally", "shakira austin", "sonia citron", "brittney sykes", "tiffany hayes",
	"veronica burton", "kahleah copper", "courtney williams", "courtney vandersloot",
	"trump", "biden", "obama", "vance", "desantis", "newsom", "loeffler", "watters", "hannity",
	"whitlock", "gaines", "kirk", "rapinoe", "engelbert", "hammon", "reeve", "wallen",
	"mulkey", "staley", "auriemma", "david"
];
const FULL = new Set([...Object.keys(roster), ...EXTRA].map((n) => n.toLowerCase()));
const TOKENS = new Set();
for (const name of FULL)
	for (const part of name.replace(/[.]/g, "").split(/\s+/))
		if (part.length > 2 && !ORDINARY.has(part)) TOKENS.add(part.replace(/['’]/g, ""));

export function isNameTerm(term) {
	const t = String(term).toLowerCase().replace(/[’]/g, "'");
	for (const name of FULL) if (name.includes(" ") && t.includes(name)) return true;
	return t.split(/\s+/).some((w) => TOKENS.has(w.replace(/'s$/, "").replace(/['.]/g, "")));
}
