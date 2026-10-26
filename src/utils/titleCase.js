// Headlines in one style. Fox writes some in Title Case ("Angel Reese Embarrasses
// Herself With Cringe Video") and some in sentence case; every one comes out in Title
// Case, with the short words below lowercase inside a headline. Otherwise it only adds
// capitals, so names, brands and acronyms come through as written.

// short words that stay lowercase inside a headline ("off", "out" and "up" are left
// out: they're usually part of the verb, "Shows Off", "Calls Out")
const SMALL = [
	"a",
	"an",
	"the",
	"and",
	"but",
	"or",
	"nor",
	"of",
	"to",
	"in",
	"on",
	"at",
	"for",
	"by",
	"as",
	"vs",
	"vs.",
	"via",
	"per",
	"from",
	"with",
	"into"
];

// a capital on a lowercase word; a word with a capital already (iPhone, McBride) stays
const capital = (word) =>
	/[A-Z]/.test(word)
		? word
		: word.replace(/^([^a-z]*)([a-z])/, (m, lead, c) => lead + c.toUpperCase());

export function titleCase(headline) {
	let start = true; // the first word, the first after a colon, dash or question, or in quotes
	return headline
		.split(" ")
		.map((word) => {
			const bare = word.replace(/^[^A-Za-z]+|[^A-Za-z.]+$/g, "");
			const acronym = bare.length > 1 && bare === bare.toUpperCase(); // "ON", not "A"
			const small = SMALL.includes(bare.toLowerCase()) && !acronym;
			const out =
				!start && small && !/^["“‘']/.test(word)
					? word.toLowerCase()
					: word.split("-").map(capital).join("-");
			start = /[:?!—–]$/.test(word) || word === "-";
			return out;
		})
		.join(" ");
}
