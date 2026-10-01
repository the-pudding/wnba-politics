// Turn the per-player verb/adjective contrasts into the shape WordQuadrant
// expects, so the story has one Fightin' Words chart rather than two that look
// like different claims.
//
// The quadrant wants points of {word, z, n, nf, no}: a signed score, a pooled
// frequency for the x-axis, and the per-side counts for the hover. Our data
// stores each side's list separately with an unsigned score, so the sign is put
// back on and the two lists are merged.
import { inOutlet, outletName } from "$utils/outlets.js";
import DATA from "$data/player_words.json";
const data = DATA;
import phrases from "$data/player_phrases.json";
// hand-picked tooltip examples, keyed "player | relation | word"
import overrides from "$data/example_overrides.json";

const RELATION = {
	subject: "what she does",
	object: "what is done to her",
	describe: "how she is described",
	play: "how her play is described",
	all: "every word attached to her",
	phrases: "two-word phrases in sentences about her",
	// each relation's two-word phrases (notebook 09, 2026-09-30)
	subject2: "what she does, in two-word phrases",
	object2: "what is done to her, in two-word phrases",
	describe2: "how she is described, in two-word phrases",
	play2: "how her play is described, in two-word phrases",
	all2: "every two-word phrase attached to her"
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

// the single outlets a player's relation can be set against on its own
// (notebook 09 stores one contrast per outlet that clears the same floor)
// `alt`: another player_words.json to read instead (TEMPORARY: the no-college rerun)
export function playerWordsOutlets(who, rel, alt = null) {
	return (alt ?? data).players?.[who]?.vsByOutletKeys?.[rel] ?? [];
}

// the file holding a player's single-outlet comparisons (notebooks/site_data.py)
export function playerOutletFile(who) {
	return `player_outlet/${who.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}.json`;
}

// `outlet`: one comparison outlet's name, or null for everyone pooled. The
// pooled groups ship in the bundle; a single outlet's block comes from the
// player's fetched file, passed in as `byOutlet`
export function playerWordsSource({ who, rel, vs, pair, outlet = null, byOutlet = null, alt = null }) {
	const data = alt ?? DATA;
	// the pooled comparison's examples, borrowed by a single-outlet view whose
	// own words ship without any
	let borrowed = null;
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
			bottom: "other outlets",
			topShort: "in Fox News",
			bottomShort: "in the other outlets"
		};
	} else {
		const person = data.players?.[who];
		if (!person) return null;
		const singleBlock = person.vsByOutlet?.[rel]?.[outlet] ?? byOutlet?.[rel]?.[outlet];
		if (vs === "outlets" && outlet && singleBlock) {
			const single = singleBlock;
			borrowed = new Map();
			for (const side of ["clark", "others"])
				for (const entry of person.vsOutlets?.[rel]?.[side] ?? [])
					if (entry.eg && !borrowed.has(entry.word)) borrowed.set(entry.word, entry);
			block = {
				scored: single.scored,
				counts: single.counts,
				top: `${who} in Fox News`,
				bottom: outletName(outlet),
				topShort: "in Fox News",
				bottomShort: inOutlet(outlet)
			};
		} else if (vs === "outlets" && person.vsOutlets?.[rel]) {
			block = {
				scored: person.vsOutlets[rel],
				counts: person.vsCounts?.[rel],
				top: `${who} in Fox News`,
				bottom: "other outlets",
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
			// a single-outlet word borrows the pooled example only when that
			// example is Fox's or the chosen outlet's own
			const pooled = borrowed?.get(entry.word);
			const lent =
				pooled && (!pooled.ego || pooled.ego === "Fox News" || pooled.ego === outlet)
					? pooled
					: null;
			if (n > 0)
				points.push({
					word: entry.word,
					z: Math.abs(entry.z) * sign,
					n,
					nf,
					no,
					eg: own?.eg ?? entry.eg ?? lent?.eg,
					egw: own?.egw ?? entry.egw ?? lent?.egw,
					// the outlet the example is from ("ESPN", "The Athletic"); a
					// hand-picked override names its own, else it is Fox's
					ego: own?.ego ?? (own?.eg ? "Fox News" : (entry.ego ?? lent?.ego))
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
