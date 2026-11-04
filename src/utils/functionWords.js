// Function words: articles, pronouns, prepositions, helping verbs and the like.
// They are counted and scored with everything else (the prior keeps them in
// check, Monroe et al. 2008), but the Fightin' Words charts don't show them: a
// word on this list, or a phrase that starts or ends with one ("the media",
// "on x", "points and"), is left off. A phrase with one inside stays ("points
// and rebounds").
// The list is notebook 06's STOPWORDS, plus more pronouns and prepositions,
// contractions, and the pieces of "7 p.m. ET" and "15 th".
const WORDS = `
a an the and or but if then than that this these those of in on at to for with
from by as is are was were be been being it its it's his her she he they them their our your you
i we us not no do does did has have had will would can could should may might must about after
before over under again more most other some such only own same so too very s t don now new
what which who whom when where why how all any both each few nor said says say
re ve ll didn don doesn isn wasn aren won wouldn couldn shouldn hasn haven hadn shes hes
theyre youre weve ive got get gets getting just also even still back one two per like
first second last
me my mine myself her hers herself him himself its itself our ours ourselves your yours
their theirs themselves into onto out up down off through during while until against
there here
don't doesn't didn't isn't wasn't aren't weren't won't can't couldn't wouldn't shouldn't
hasn't haven't hadn't i'm i've i'll i'd you're you've you'll we're we've they're they've
she's he's that's there's what's who's let's it'll
p m et th
`;
const FUNCTION_WORDS = new Set(WORDS.split(/\s+/).filter(Boolean));

export function isFunctionTerm(term) {
	const words = String(term).toLowerCase().replace(/[’]/g, "'").split(/\s+/);
	return (
		FUNCTION_WORDS.has(words[0]) || FUNCTION_WORDS.has(words[words.length - 1])
	);
}
