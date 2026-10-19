// Chyrons come in capitals ("REESE CRITICIZED FOR GESTURES AT CAITLIN CLARK"):
// set them in sentence case for a tooltip, with the site's people, the teams
// and their cities, and the usual acronyms capitalised again
import roster from "$data/people.json";
import { properCase } from "$utils/properCase.js";

const ACRONYMS = [
	"wnba", "nba", "ncaa", "espn", "cnn", "msnbc", "abc", "cbs", "nbc", "gop", "dei",
	"lgbtq", "lgbtq+", "usa", "u.s.", "nfl", "ufc", "mvp", "tv", "ai", "dc", "lsu",
	"uconn", "ucla", "usc", "ok", "nyt", "nwsl"
];
// places and days the chyrons name, lowercased by the counting
const PROPER = [
	"russia", "russian", "russians", "moscow", "ukraine", "america", "american", "americans",
	"texas", "iowa", "florida", "louisiana", "georgia", "carolina", "south", "olympics",
	"olympic", "paris", "tokyo", "congress", "senate", "white house", "black lives matter",
	"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
	"democrats", "republicans", "democratic", "republican", "christmas", "juneteenth"
];
const FIXED = new Map(ACRONYMS.map((a) => [a, a === "uconn" ? "UConn" : a.toUpperCase()]));
for (const w of PROPER) if (!w.includes(" ")) FIXED.set(w, w[0].toUpperCase() + w.slice(1));
// each part of a roster name, as the roster spells it ("dijonai" → "DiJonai")
for (const name of Object.keys(roster))
	for (const part of name.split(/\s+/))
		if (part.length > 2 && !FIXED.has(part.toLowerCase())) FIXED.set(part.toLowerCase(), part);
// surnames that are also ordinary words stay lowercase unless the full name is there
const ORDINARY = new Set([
	"bird", "cloud", "young", "white", "gray", "hill", "sun", "sky", "storm", "freedom"
]);
for (const w of ORDINARY) FIXED.delete(w);
const FULL = [
	...Object.keys(roster).filter((n) => n.split(/\s+/).some((p) => ORDINARY.has(p.toLowerCase()))),
	...PROPER.filter((w) => w.includes(" ")).map((w) => w.replace(/(^|\s)([a-z])/g, (x, s, c) => s + c.toUpperCase()))
];
const FULL_RX = FULL.length
	? new RegExp(`\\b(${FULL.map((n) => n.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})\\b`, "g")
	: null;
const fullFor = new Map(FULL.map((n) => [n.toLowerCase(), n]));

export function headlineCase(text) {
	if (typeof text !== "string" || !text) return text;
	let out = text.toLowerCase();
	// full names first, while every word is still lowercase ("sue bird")
	if (FULL_RX) out = out.replace(FULL_RX, (m) => fullFor.get(m) ?? m);
	// word by word; "u.s." and "lgbtq+" keep their marks, "griner's" its "'s"
	out = out.replace(/(?<![A-Za-z])[a-z]+(?:\.[a-z]+)*\.?\+?/g, (w) => {
		const fixed = FIXED.get(w) ?? FIXED.get(w.replace(/[.+]$/, ""));
		return fixed ? fixed + w.slice(fixed.length) : w;
	});
	out = properCase(out)
		// "i" alone is always "I"
		.replace(/\bi\b(?!\.)/g, "I")
		// a capital to open the line, each " / " segment and a "REPORT:"-style
		// lead; not after a period, which is mostly where a chyron's lines were
		// joined ("BRITTNEY GRINER. DETAINED IN RUSSIA")
		.replace(/(^[^A-Za-z]*|[:/!?]\s+["“]?)([a-z])/g, (m, lead, c) => lead + c.toUpperCase());
	return out;
}
