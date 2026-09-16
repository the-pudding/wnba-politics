// Turn the per-player verb/adjective contrasts into the shape WordQuadrant
// expects, so the story has one Fightin' Words chart rather than two that look
// like different claims.
//
// The quadrant wants points of {word, z, n, nf, no}: a signed score, a pooled
// frequency for the x-axis, and the per-side counts for the hover. Our data
// stores each side's list separately with an unsigned score, so the sign is put
// back on and the two lists are merged.
import data from "$data/player_words.json";
import phrases from "$data/player_phrases.json";
// hand-picked tooltip examples, keyed "player | relation | word"
import overrides from "$data/example_overrides.json";

const RELATION = {
	subject: "what she does",
	object: "what is done to her",
	describe: "how she is described",
	play: "how her play is described",
	all: "every word attached to her",
	phrases: "two-word phrases in sentences about her"
};

// the players with a phrases comparison (notebooks/player_phrases.py)
export function playerPhrasesPeople() {
	return Object.keys(phrases);
}

// the players a reader can pick: those with a Fox-versus-outlets comparison,
// in the data's order (most attachments first)
export function playerWordsPeople() {
	return (data.order ?? []).filter((name) => data.players?.[name]?.vsOutlets);
}

export function playerWordsSource({ who, rel, vs, pair }) {
	let block = null;
	if (vs === "pair" && pair && data.pairs?.[pair]) {
		const entry = data.pairs[pair];
		block = {
			scored: entry.relations?.[rel],
			counts: entry.counts?.[rel],
			top: entry.left,
			bottom: entry.right,
			// surnames, for the tooltip's count line
			topShort: "about " + entry.left.split(" ").pop(),
			bottomShort: "about " + entry.right.split(" ").pop()
		};
	} else if (rel === "phrases") {
		const entry = phrases[who];
		if (!entry) return null;
		block = {
			scored: entry.scored,
			counts: entry.counts,
			top: `${who} in Fox News`,
			bottom: "everyone else writing about her",
			topShort: "in Fox News",
			bottomShort: "in the other outlets"
		};
	} else {
		const person = data.players?.[who];
		if (!person) return null;
		if (vs === "outlets" && person.vsOutlets?.[rel]) {
			block = {
				scored: person.vsOutlets[rel],
				counts: person.vsCounts?.[rel],
				top: `${who} in Fox News`,
				bottom: "everyone else writing about her",
				topShort: "in Fox News",
				bottomShort: "in the other outlets"
			};
		} else {
			block = {
				scored: person.relations?.[rel],
				counts: person.counts?.[rel],
				top: `${who} in Fox News`,
				bottom: "every other player",
				topShort: "about " + who.split(" ").pop(),
				bottomShort: "about the other players"
			};
		}
	}
	if (!block?.scored) return null;

	const points = [];
	for (const [side, sign] of [
		["clark", 1],
		["others", -1]
	]) {
		for (const entry of block.scored[side] ?? []) {
			const nf = entry.clark ?? 0;
			const no = entry.others ?? 0;
			const n = nf + no;
			const own = overrides[`${who} | ${rel} | ${entry.word}`];
			if (n > 0)
				points.push({
					word: entry.word,
					z: Math.abs(entry.z) * sign,
					n,
					nf,
					no,
					eg: own?.eg ?? entry.eg,
					egw: own?.egw ?? entry.egw
				});
		}
	}

	return {
		points,
		topLabel: block.top,
		bottomLabel: block.bottom,
		topShort: block.topShort,
		bottomShort: block.bottomShort,
		relation: RELATION[rel] ?? rel,
		counts: block.counts
	};
}
