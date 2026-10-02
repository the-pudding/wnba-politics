// The words each topic counts, as a chart's caption lists them: the term
// groups from data/topic_terms.csv (the same unions as notebooks/topics.py),
// regular expressions spelled out for a reader. Shared by the outlet charts.
import termRows from "../../data/topic_terms.csv";

// each entry is one list: a label and the term groups it pools
const TOPIC_GROUPS = {
	polrace: [["Race", ["race / racism"]]],
	lgbtq: [["LGBTQ+", ["LGBTQ / sexuality", "transgender / trans"]]],
	fouls: [["Foul words", ["fouls"]]],
	protect: [["“Protect”", ["protect"]]]
};
// the fouls topic is pinned in notebooks/topics.py (the sheet's rows are not
// used), so its list names those words directly
const PINNED_WORDS = { fouls: ["hip-check", "poke / poked", "punch / punched", "throat"], protect: ["protect / protects"] };

// a few terms are regular expressions; these read better spelled out
const PRETTY = {
	racis: "racism / racist",
	"hip-?check": "hip-check",
	"\\bpunch": "punch / punched",
	"\\bthroat\\b": "throat",
	"\\bpoke[ds]?\\b": "poke / poked",
	"\\beye\\b": "eye",
	"\\bflagrant\\b": "flagrant",
	"\\bfouls?\\b": "foul / fouls",
	"lgbt?\\b": "LGBT",
	"lgbtq?\\b": "LGBTQ",
	"\\bblm\\b": "BLM",
	"non-?binary": "nonbinary",
	"trans wom[ae]n": "trans woman / women",
	"gender eligib": "gender eligibility",
	"biological (?:male|man|men|wom[ae]n|female)":
		"“biological” male / female / woman",
	"\\b(?:black|white) (?:wom[ae]n|player|players|athlete|athletes|star|stars|community)\\b":
		"“Black” or “white” + women / players / athletes / stars / community"
};
const readable = (term) =>
	PRETTY[term] ??
	term
		// lookarounds like (?!- ) only guard a match; they are not words
		.replace(/\(\?<?[=!][^)]*\)/g, "")
		.replace(/\\b/g, "")
		.replace(/\(\?:([^)]+)\)/g, (_, alts) => alts.split("|").join(" / "))
		.replace(/\[ae\]/g, "a")
		.replace(/\\/g, "");
// the list as a reader wants it: a phrase that only adds to a word already
// listed goes ("openly gay" under "gay", "trans women" under "trans"), and
// "trans" sits beside "transgender"
function tidyWords(words) {
	const single = new Set(words.filter((w) => !/\s/.test(w)).map((w) => w.toLowerCase()));
	let out = words.filter(
		(w) => !/\s/.test(w) || !w.toLowerCase().split(/\s+/).some((part) => single.has(part))
	);
	const t = out.indexOf("trans"), tg = out.indexOf("transgender");
	if (t > -1 && tg > -1 && t !== tg + 1) {
		out.splice(t, 1);
		out.splice(out.indexOf("transgender") + 1, 0, "trans");
	}
	return out;
}

export function wordGroupsFor(topic, second) {
	return [...(TOPIC_GROUPS[topic] ?? []), ...(second ? (TOPIC_GROUPS[second] ?? []) : [])].map(([label, groups]) => ({
		label,
		// a term listed in more than one of the pooled groups shows once
		words:
			groups.length === 1 && PINNED_WORDS[groups[0]]
				? PINNED_WORDS[groups[0]]
				: tidyWords([...new Set(termRows.filter((r) => groups.includes(r.topic)).map((r) => readable(r.term)))])
	}));
}
