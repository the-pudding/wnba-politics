<script>
	// Mirrored horizontal bars for a fightin'-words contrast
	import { base } from "$app/paths";
	import { LOGO_WIDTH, LOGO_RATIO } from "$utils/outlets.js";
	import { properCase } from "$utils/properCase.js";
	let {
		source = null,
		highlight = null,
		// unlit: words to leave dark while every other bar is lit (a step that
		// lights nearly the whole chart); nothing moves
		unlit = null,
		// inPlace: the highlighted words light where they are, and one off the
		// page is not pulled up onto it
		inPlace = false,
		top = 12,
		// more: rank the list further than `top`, a page of `top` at a time
		// with Previous / Next under the bars, the frame the same height
		// (it scrolled before)
		more = 0,
		// pager: show Previous / Next (a scrolly keeps it for its explore step)
		pager = true,
		example = null,
		// labels: "on" (the word on its bar), "beside" (a column of words down
		// the middle, the bars growing outward from it), "outside" (the bars
		// grow from the middle, the words in a column past their ends) or
		// "tip" (each word hugging the end of its bar, scores in the tooltip)
		labels = "on",
		// scale: "linear" (bar length is the score), "sqrt" (square-root, so a
		// runaway word does not squash the rest) or "cap" (the longest bar is
		// cut with a break mark at 1.2× the next longest)
		scale = "linear",
		// caps: true — words in capitals; "title" — first letter capitalised
		caps = false,
		// nicknamesAsWords: "fire", "sun", "storm" … stay lowercase (a player's
		// words, where they are mostly verbs and words, not the teams)
		nicknamesAsWords = false,
		// scores: true — the score printed past each bar (it is always in the
		// tooltip)
		scores = false,
		onhover = null,
		fill = false,
		// the name of the bottom side in the tooltip's counts ("others", "ESPN")
		otherName = "Others",
		// the top side's short name ("Fox", or "conservative media" for the pair)
		topName = "Fox",
		// note: the line under the chart — left out for the stock one, written
		// for your own (HTML allowed), present but blank for none
		note = undefined,
		// noteKind: "source" sets the note as a source line (small, left, over
		// a thin rule), as the main chart's caption is
		noteKind = "",
		// the Doc's words for the pager and the hover counts (fill.js slots)
		previous = "",
		next = "",
		range = "",
		// hoverCounts: {top} {bottom} {topUses} {bottomUses} {topShare}
		// {bottomShare} (share of articles) {topCount} {bottomCount} {items}
		// {score} {strength}, and with article counts {rank} {topLabel}
		// {bottomLabel} {topItems} {bottomItems} (each side's size) {topTimes}
		// {bottomTimes} ("1,235 uses") {difference}, {bottomAll} ("Others
		// (combined)", or the one outlet's name); "|" starts a new line and
		// **…** is bold
		hoverCounts = "",
		// the how-often line: hoverRatio ({times}, also {who} {verb}
		// {unit}), hoverEven (about the same rate); ratioUnit, what the rate is
		// per ("for its size")
		hoverRatio = "",
		// with each side's article counts the line compares articles instead:
		// hoverShareRatio (Used in {times} as many {items}), hoverShareEven
		hoverShareRatio = "",
		hoverShareEven = "",
		hoverEven = "",
		ratioUnit = "",
		// hoverStrength: the three words for how sure a score is, least sure first, by commas
		hoverStrength = "",
		// each side's total ({ top, bottom }), so the tooltip can show a word's
		// uses as a percentage; without it, source.counts ({ clark, others })
		totals = null
	} = $props();
	const noteMode = $derived(note === undefined || note === null ? "stock" : String(note).trim() ? "custom" : "none");

	import { fill as fillIn, or } from "$utils/fill.js";
	const FOX = "var(--color-fox-navy)";
	const OTHERS = "var(--color-outlets)";
	const INK = "var(--color-ink)";
	const WEAK_Z = 1.96; // below this a word's lean is within noise
	const WEAK = "var(--wnba-tan-dark)"; // those words' colour in the tooltip, whichever side
	const WEAK_BAR = "#f6efe6"; // their bars, close to the page so the words seem to float
	const WEAK_TEXT = "#000"; // and their words
	const WEAK_TEXT_FADED = "#cdc4b8"; // those words when a step highlights others
	const LOADING = "Loading words…"; // while a comparison's words are still on their way
	// the heads at the bars' outer edges; on a narrow chart each breaks before "to".
	// Below 800px of screen the shorter wording
	let screenW = $state(1024);
	let shortHeads = $derived(screenW < 800);
	let EDGE_OTHERS = $derived(shortHeads ? "← More distinctive others" : "← More distinctive to other outlets");
	let EDGE_FOX = $derived(shortHeads ? "More distinctive Fox →" : "More distinctive to Fox News →");
	// the hover counts when each side's article counts are known: how many
	// times as many articles use it, and each side's share (the Doc's
	// hoverCounts takes over once it has {topShare})
	const SHARE_COUNTS = "{ratio}: | {topLabel} {topShare} · {bottomLabel} {bottomShare}";
	// a player's chart: how often for its size, then the uses on each side
	const USES_COUNTS = "{ratio} | Uses: {top} {topUses} · {bottomAll} {bottomUses}";
	// and the line under the word: its score, and how sure the difference is
	// (**…** is bold)
	const SHARE_HEAD = "**Distinctiveness: {score}** ({strength})";

	let lit = $derived(new Set((highlight ?? []).map((w) => w.toLowerCase())));
	let anyLit = $derived(lit.size > 0);
	let off = $derived(new Set((unlit ?? []).map((w) => w.toLowerCase())));
	// the bars hold their places: no highlighted word is brought up the list
	let still = $derived(off.size > 0 || inPlace === true || String(inPlace) === "true");
	const isOn = (word) => (off.size ? !off.has(word.toLowerCase()) : !anyLit || lit.has(word.toLowerCase()));

	// pixel-true: the frame is measured, the drawing fills it
	let el = $state(null);
	let frame = $state({ w: 0 });
	let narrow = $derived(frame.w > 0 && frame.w < 640);
	let WIDTH = $derived(frame.w || 900);
	// fill: the scrolly asks the rows to stretch down the viewport, so a
	// chart with fifteen bars uses the screen instead of a strip of it
	let avail = $state(0);
	// room left under the bars for what sits below them (the pager, the note),
	// measured, so a two-line note under a pager is never cut off the screen
	let belowEl = $state(null);
	let pagerEl = $state(null);
	// (.below is a flow-root, so its height counts the note's margins; 6 is the pager's margin)
	const reserve = () => 24 + (belowEl?.offsetHeight ?? 0) + (pagerEl ? pagerEl.offsetHeight + 6 : 0);
	$effect(() => {
		if (!fill || !el) return;
		rows;
		// measured against the sticky frame, not the viewport, so it holds
		// whether or not the chart is pinned on screen right now
		const measure = () => {
			const sticky = el.closest(".sticky");
			const er = el.getBoundingClientRect();
			// the screen that is actually visible: on a phone 100vh runs under the
			// browser's toolbar, so the sticky frame can be taller than the screen
			const screenH = window.visualViewport?.height ?? window.innerHeight;
			if (sticky) {
				const sr = sticky.getBoundingClientRect();
				const pinnedAt = parseFloat(getComputedStyle(sticky).top) || 0;
				const frameH = Math.min(sr.height, screenH - pinnedAt);
				avail = frameH - (er.top - sr.top) - reserve();
			} else {
				avail = screenH - er.top - reserve();
			}
		};
		measure();
		window.addEventListener("resize", measure);
		window.visualViewport?.addEventListener("resize", measure);
		// the controls above the chart come and go with the step
		const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(measure) : null;
		ro?.observe(el.parentElement ?? el);
		if (belowEl) ro?.observe(belowEl);
		return () => {
			window.removeEventListener("resize", measure);
			window.visualViewport?.removeEventListener("resize", measure);
			ro?.disconnect();
		};
	});
	const TOP = 34;
	const HEAD_LINE = 13; // the edge heads' second line, on a narrow chart
	const BOTTOM = 10;
	// ROW_SQUEEZE: thinner rows, only for a step whose highlighted words
	// can't all fit on a short screen otherwise
	const ROW_MIN = 26,
		ROW_SQUEEZE = 20;
	// in the scrolly the rows keep one height (ROW_COMFY) rather than stretching
	// to fill a tall screen; they only close up when a short screen can't fit them
	let ROW = $derived(
		fill && avail > 0
			? Math.max(
					viewRows * ROW_MIN > avail - TOP - BOTTOM ? ROW_SQUEEZE : ROW_MIN,
					Math.min(ROW_COMFY, (avail - TOP - BOTTOM) / viewRows)
				)
			: ROW_MIN
	);
	let height = $derived(TOP + rows * ROW + BOTTOM);
	// each side's strongest words, highlighted ones kept even when they rank lower
	const side = (sign) =>
		(source?.points ?? [])
			.filter((p) => Math.sign(p.z) === sign)
			.sort((a, b) => Math.abs(b.z) - Math.abs(a.z));
	let fox = $derived(pick(side(1), 1));
	let others = $derived(pick(side(-1), -1));
	// no words yet (their file is still loading): the heads and the note keep the
	// full width instead of closing up around an empty middle
	let empty = $derived(!fox.length && !others.length);
	// with room to spare the chart shows more words rather than taller bars:
	// as many rows as fit at a comfortable height, up to a ceiling. On a short
	// screen it shows fewer words, so the note under the bars stays on screen
	// MAX_BARS: the most bars on each side in one view, however tall the screen or
	// whatever `top` the Doc asks for (highlighted words included)
	const MAX_BARS = 20;
	const ROW_COMFY = 32,
		TOP_MAX = MAX_BARS,
		TOP_MIN = 6;
	// the most rows that fit at all, highlighted words included
	let fitRows = $derived(
		fill && avail > 0 ? Math.max(TOP_MIN, Math.floor((avail - TOP - BOTTOM) / ROW_MIN)) : Infinity
	);
	let topN = $derived.by(() => {
		if (!fill || avail <= 0) return Math.min(top, MAX_BARS);
		const comfy = Math.floor((avail - TOP - BOTTOM) / ROW_COMFY);
		return Math.max(TOP_MIN, Math.min(TOP_MAX, Math.max(comfy, Math.min(top, fitRows))));
	});
	let paged = $derived(more > topN);
	let page = $state(0);
	// the words ranked on each side, up to `more`, and how many pages they fill
	let ranked = $derived(Math.min(more, Math.max(side(1).length, side(-1).length)));
	let pages = $derived(paged ? Math.max(1, Math.ceil(ranked / topN)) : 1);
	// a highlighted word that isn't on the page showing: it stays at its real
	// rank, but the page gives up its last rows for a "⋯" and a row for it
	// ("#38"), so the reader sees it without the order being changed
	//. The page keeps its height.
	let pins = $derived.by(() => {
		const none = { 1: [], [-1]: [], rows: 0, keep: topN };
		if (!paged || !anyLit || still) return none;
		const ranked = { 1: side(1).map((p, i) => ({ ...p, rank: i + 1 })), [-1]: side(-1).map((p, i) => ({ ...p, rank: i + 1 })) };
		let keep = topN, out = none;
		// the rows given up can uncover more highlighted words: settle it
		for (let pass = 0; pass < 4; pass++) {
			const res = { rows: 0, keep };
			for (const s of [1, -1]) {
				const shown = new Set(ranked[s].slice(page * topN, page * topN + keep).map((p) => p.word.toLowerCase()));
				res[s] = ranked[s].filter((p) => lit.has(p.word.toLowerCase()) && !shown.has(p.word.toLowerCase())).map((p) => ({ ...p, pin: true }));
			}
			res.rows = Math.max(res[1].length, res[-1].length);
			const next = res.rows ? Math.max(1, topN - res.rows - 1) : topN;
			out = res;
			if (next === keep) break;
			keep = next;
		}
		out.keep = keep;
		return out;
	});
	function pick(list, sign = 0) {
		if (paged)
			return [
				...list.slice(0, more).slice(page * topN, page * topN + pins.keep),
				...(sign ? pins[sign] : [])
			];
		// highlighted words ranked lower join the bottom; on a short screen
		// they take the place of the last unhighlighted ones
		const isLit = (p) => !still && lit.has(p.word.toLowerCase());
		let keep = topN;
		while (keep > 1 && keep + list.slice(keep).filter(isLit).length > Math.min(fitRows, MAX_BARS)) keep--;
		return [...list.slice(0, keep), ...list.slice(keep).filter(isLit)];
	}
	// every page is a full page tall, so the chart does not jump
	let rows = $derived(paged ? topN : Math.max(fox.length, others.length, 1));
	let viewRows = $derived(rows);
	// a new comparison starts back on the first page
	$effect(() => {
		source;
		page = 0;
	});
	$effect(() => {
		if (page > pages - 1) page = pages - 1;
	});

	let GAP = $derived(narrow ? 4 : 10); // either side of the middle
	let beside = $derived(String(labels).trim().toLowerCase() === "beside");
	let outside = $derived(String(labels).trim().toLowerCase() === "outside");
	let tip_ = $derived(String(labels).trim().toLowerCase() === "tip");
	let mid = $derived(WIDTH / 2);
	// a column head can carry the outlet's wordmark on its outer side ("← [logo]
	// in ESPN", "in Fox News [logo] →"): source.topLogo /
	// source.bottomLogo name a file in static/logos
	// a logo's height in the head: a long wordmark (the Times, the Post) a
	// little shorter so it does not dwarf the words; its width from its shape
	const logoHeight = (file) => ((LOGO_RATIO[file] ?? 3) > 5 ? 12 : 15);
	const logoWidth = (file) =>
		file
			? LOGO_RATIO[file]
				? LOGO_RATIO[file] * logoHeight(file)
				: ((LOGO_WIDTH[file] ?? 40) * 15) / (file.endsWith(".png") ? 15 : 12)
			: 0;
	let topIn = $state(null);
	let topInWidth = $state(80);
	let bottomIn = $state(null);
	let bottomInWidth = $state(60);
	$effect(() => {
		source?.bottomLogo;
		source?.bottomShort;
		if (bottomIn) bottomInWidth = bottomIn.getComputedTextLength();
	});
	$effect(() => {
		source?.topLogo;
		source?.topShort;
		if (topIn) topInWidth = topIn.getComputedTextLength();
	});
	// a phone gets the square-root scale unless the Doc asked for another, so
	// the bars spread across the little width they have
	const scaleMode = $derived.by(() => {
		const m = String(scale).trim().toLowerCase();
		return narrow && (!m || m === "linear") ? "sqrt" : m;
	});
	let showScores = $derived(scores === true || String(scores) === "true");
	// paged, every page keeps the first page's scale: word 43's bar stays
	// shorter than word 1's instead of filling the width again
	let zs = $derived(
		(paged ? [...side(1).slice(0, more), ...side(-1).slice(0, more)] : [...fox, ...others])
			.map((p) => Math.abs(p.z))
			.sort((a, b) => b - a)
	);
	let capZ = $derived(scaleMode === "cap" && zs.length > 1 ? zs[1] * 1.2 : Infinity);
	let maxZ = $derived(Math.max(1, Math.min(zs[0] ?? 1, capZ)));
	const shape = (z) => (scaleMode === "sqrt" ? Math.sqrt(z) : z);
	// team names always in capitals (utils/properCase.js), then the caps setting
	const wordCase = (w) =>
		caps === true || String(caps) === "true"
			? w.toUpperCase()
			: String(caps).toLowerCase() === "title"
				? w.replace(/(^|[\s-])([a-z])/g, (m, a, b) => a + b.toUpperCase())
				: properCase(w, { nicknamesAsWords });
	// bar length: leaves room past the end for a word that does not fit inside
	// outside: the bars keep the middle, the words take the outer column, with
	// room for the score between them
	// the room kept past the longest bar: for a score, a word beyond a short
	// bar, or just a margin
	let span = $derived(
		mid - GAP - LABEL -
			(showScores
				? narrow ? 60 : beside || outside ? 44 : 110
				: beside || outside || tip_
					? narrow ? 6 : 30
					: narrow ? 8 : 80)
	);
	// with the words at the bar tips, no score is drawn on the chart
	let len = $derived((z) => (shape(Math.min(Math.abs(z), capZ)) / shape(maxZ)) * span);
	const capped = (z) => Math.abs(z) > capZ;
	const yOf = (i) => TOP + i * ROW + ROW / 2;

	$effect(() => {
		if (!el) return;
		const measure = () => (frame = { w: Math.round(el.clientWidth) });
		measure();
		const ro = new ResizeObserver(measure);
		ro.observe(el);
		return () => ro.disconnect();
	});

	// the word goes inside its bar when it fits, else just past the bar's end
	let WORD_PX = $derived(narrow ? 12 : 13.5);
	let measureCtx = null;
	let chartFont = null;
	function textWidth(word) {
		if (typeof document === "undefined") return word.length * WORD_PX * 0.6;
		if (!measureCtx)
			measureCtx = document.createElement("canvas").getContext("2d");
		// a canvas cannot read a CSS variable: resolve the chart face once
		// (an unreadable font string would silently fall back to 10px sans)
		if (!chartFont)
			chartFont =
				getComputedStyle(document.documentElement).getPropertyValue("--font-chart").trim() ||
				'"Helvetica Neue", Helvetica, Arial, sans-serif';
		measureCtx.font = `700 ${WORD_PX}px ${chartFont}`;
		return measureCtx.measureText(word).width;
	}
	// the edge heads on one line when both fit (measured as drawn: 12px
	// capitals, against the measure's bold words), else two lines each
	const headWidth = (t) => (textWidth(t.toUpperCase()) * 12) / WORD_PX;
	// (below 460px of screen they always take two lines)
	let edgeOneLine = $derived(screenW >= 460 && headWidth(EDGE_OTHERS) + headWidth(EDGE_FOX) + 24 < WIDTH);
	let headExtra = $derived(source?.topHead && !edgeOneLine ? HEAD_LINE : 0);
	// the word column, when the words sit beside the bars: as wide as the
	// longest word shown, within reason
	let LABEL = $derived(
		beside || outside
			? Math.min(narrow ? 110 : 180, Math.max(narrow ? 70 : 100,
					...[...fox, ...others].map((p) => textWidth(p.word) + 14)))
			: 0
	);
	const fmt = (z) => Math.abs(z).toFixed(1);
	// the tooltip in plain words: how much more often one side uses the word for
	// its size (its rate per article, headline or word about her), and how sure
	// the score lets us be that the gap is not chance, at the usual 95%, 99% and
	// 99.9% cut-offs
	const STRENGTH_CUTS = [1.96, 3.29];
	// the ratio needs this many uses on each side (one stray use makes "16×");
	// a word only one side uses gets no ratio line
	const MIN_RATIO_USES = 5;
	const STRENGTH_WORDS = "could be chance, strong, very strong";
	const strengthOf = (z) => {
		const words = or(hoverStrength, STRENGTH_WORDS).split(",").map((w) => w.trim());
		return words[STRENGTH_CUTS.filter((cut) => Math.abs(z) >= cut).length] ?? words[words.length - 1];
	};
	const capital = (name) => String(name).charAt(0).toUpperCase() + String(name).slice(1);
	// "Others", "sports outlets", "other players" take "use"; "Fox", "ESPN" take "uses"
	const verbOf = (name) => (/^others?\b|outlets$|players$/i.test(String(name).trim()) ? "use" : "uses");
	function ratioOf(p) {
		// the two sides' sizes: the main chart passes its article or headline
		// counts; a player's chart has the words tied to her on each side
		const sizes =
			source?.sizes ?? (source?.counts ? { top: source.counts.clark, bottom: source.counts.others } : null);
		if (!sizes?.top || !sizes?.bottom) return "";
		const unit = sizes.unit ?? or(ratioUnit, "for its size");
		const sayWho = (who) => ({ who: capital(who), verb: verbOf(who), unit });
		// with article counts, the share of each side's articles that use it, so
		// the line agrees with the percentages under it; otherwise its uses
		const shared = p.af != null && p.ao != null;
		const [mine, theirs] = shared ? [p.af, p.ao] : [p.nf, p.no];
		if (Math.min(mine, theirs) < MIN_RATIO_USES) return "";
		const topRate = mine / sizes.top;
		const bottomRate = theirs / sizes.bottom;
		const times = Math.max(topRate, bottomRate) / Math.min(topRate, bottomRate);
		const items = sizes.items ?? "articles";
		if (times < 1.1)
			return shared
				? fillIn(or(hoverShareEven, "Used in about as many {items}"), { items })
				: fillIn(or(hoverEven, "About as often"), { unit });
		return fillIn(shared ? or(hoverShareRatio, "Used in {times} as many {items}") : or(hoverRatio, "{times} as often"), {
			items,
			...sayWho(topRate >= bottomRate ? topName : otherName),
			times: (times < 10 ? times.toFixed(1) : Math.round(times).toLocaleString("en-US")) + "×"
		});
	}
	// a word's count with thousands commas ("1,234"); anything not a number as it came
	const count = (n) =>
		n != null && n !== "" && Number.isFinite(+n) ? (+n).toLocaleString("en-US") : n;
	// a side's size, short: "940", "3.4k", "6k"
	const short = (n) => (n >= 1000 ? `${(n / 1000).toFixed(1).replace(/\.0$/, "")}k` : count(n));
	// a word's uses as a share of its side's total ("1.2%"); the raw count
	// when there is no total to divide by
	let sideTotals = $derived({
		top: +(totals?.top ?? source?.counts?.clark) || 0,
		bottom: +(totals?.bottom ?? source?.counts?.others) || 0
	});
	function pct(n, total) {
		if (!total || n == null || !Number.isFinite(+n)) return count(n);
		const p = (100 * +n) / total;
		if (p === 0) return "0%";
		if (p < 0.1) return "<0.1%";
		return (p < 10 ? p.toFixed(1) : Math.round(p)) + "%";
	}
	// the width the bars reach, both sides (the longest bar and its word), so
	// the note under the chart wraps to the drawing rather than the frame
	// how far the bars (and their words) reach from the middle, either side,
	// over every page, so the heads and the caption hold still as the reader
	// pages through (the longest bar is on the first page)
	let barsReach = $derived.by(() => {
		if (empty) return WIDTH / 2;
		let reach = 0;
		const all = paged ? [...side(1).slice(0, more), ...side(-1).slice(0, more)] : [...fox, ...others];
		for (const p of all) reach = Math.max(reach, LABEL + Math.max(len(p.z), textWidth(wordCase(p.word)) + 14));
		return Math.min(WIDTH / 2, GAP + reach);
	});
	// and no wider than 520px, so it reads as a caption, not a banner
	let plotWidth = $derived(Math.round(Math.min(WIDTH, 520, 2 * barsReach)));

	// the example on hover, as on the scatter: the word's sentence with the
	// form it took marked
	let hovered = $state(null);
	// a tap shows a bar's card and nothing on touch hides it: a click anywhere
	// outside the bars takes it away
	function clickAway(event) {
		if (!event.target.closest?.(".word-bars .bar")) hovered = null;
	}
	const escapeHtml = (s) =>
		s.replace(
			/[&<>"']/g,
			(c) =>
				({
					"&": "&amp;",
					"<": "&lt;",
					">": "&gt;",
					'"': "&quot;",
					"'": "&#39;"
				})[c]
		);
	// the stored example is the sentence with its neighbours on either side, so
	// the word it is an example of sits in the middle: when the word occurs more
	// than once ("the 2023 draft … No. 1 draft pick Caitlin Clark"), the
	// occurrence nearest the middle is the one meant
	function nearestMatch(text, rx) {
		const g = new RegExp(rx.source, rx.flags.includes("g") ? rx.flags : rx.flags + "g");
		let best = null;
		for (const m of text.matchAll(g)) {
			if (!best || Math.abs(m.index - text.length / 2) < Math.abs(best.index - text.length / 2)) best = m;
		}
		return best;
	}
	const esc = (w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	const wordRx = (word, form) => {
		const stem = esc(word.length > 4 ? word.slice(0, -1) : word);
		return new RegExp(`\\b(?:${esc(form ?? word)}|${stem}\\w*)\\b`, "i");
	};
	// the word the example is for: where the notebook says it starts (`at`),
	// else the occurrence nearest the middle
	function findWord(text, rx, at) {
		if (at != null) {
			const here = new RegExp(rx.source, rx.flags.replace("g", "") + "y");
			here.lastIndex = at;
			const m = here.exec(text);
			if (m) return m;
		}
		return nearestMatch(text, rx);
	}
	// a window of the passage around the word, and where the word is in it
	function excerpt(sentence, word, form, at) {
		const MAX = 170;
		const m = findWord(sentence, wordRx(word, form), at);
		if (sentence.length <= MAX) return [sentence, m?.index];
		const from = m ? m.index : 0;
		const start = Math.max(0, Math.min(from - 90, sentence.length - MAX));
		let cut = sentence.slice(start, start + MAX);
		let shift = start;
		if (start > 0) {
			const trimmed = cut.replace(/^\S*\s/, "");
			shift += cut.length - trimmed.length - 1;
			cut = "…" + trimmed;
		}
		if (start + MAX < sentence.length) cut = cut.replace(/\s\S*$/, "") + "…";
		return [cut, m ? m.index - shift : undefined];
	}
	// the word in its example: in bold, with a rule in the side's colour under it
	// a phrase ("nifty assist", "foul out") marks each of its words: the stored
	// form is the first, and the others are found close by, before or after it
	// ("fouled her out")
	const NEAR = 60;
	function markWord(sentence, word, form, color, at) {
		const [cut, where] = excerpt(sentence, word, form, at);
		const m = findWord(cut, wordRx(word, form), where);
		if (!m) return escapeHtml(cut);
		const marks = [[m.index, m.index + m[0].length]];
		for (const part of word.split(/\s+/).slice(1)) {
			const from = Math.max(0, m.index - NEAR);
			const near = nearestTo(cut.slice(from, m.index + m[0].length + NEAR), wordRx(part), m.index - from);
			if (near) marks.push([from + near.index, from + near.index + near[0].length]);
		}
		marks.sort((a, b) => a[0] - b[0]);
		let html = "", last = 0;
		for (const [s, e] of marks) {
			if (s < last) continue;
			html += escapeHtml(cut.slice(last, s)) +
				`<mark style="background:none;box-shadow:inset 0 -2px 0 ${color};font-weight:700;` +
				`color:inherit;padding:0 1px;">${escapeHtml(cut.slice(s, e))}</mark>`;
			last = e;
		}
		return html + escapeHtml(cut.slice(last));
	}
	// the match closest to a point in the text, not counting one at the point itself
	function nearestTo(text, rx, point) {
		const g = new RegExp(rx.source, rx.flags.includes("g") ? rx.flags : rx.flags + "g");
		let best = null;
		for (const m of text.matchAll(g)) {
			if (m.index === point) continue;
			if (!best || Math.abs(m.index - point) < Math.abs(best.index - point)) best = m;
		}
		return best;
	}
	let tip = $derived.by(() => {
		if (!hovered) return null;
		for (const [list, sign] of [
			[fox, 1],
			[others, -1]
		]) {
			const i = list.findIndex((p) => p.word === hovered);
			if (i < 0) continue;
			const p = list[i];
			const w = Math.max(len(p.z), textWidth(p.word) + 14);
			// the card is anchored to the bar itself: over its middle, an arrow
			// pointing down at it; below the bar only when the screen has no
			// room above, and slid sideways to stay inside the frame
			const x = sign > 0 ? mid + GAP + w / 2 : mid - GAP - w / 2;
			// the example, with the outlet it came from (a player chart's
			// stored example says so itself; otherwise the side is enough)
			const eg = p.eg
				? { s: p.eg, w: p.egw, a: p.ega, o: p.ego ?? (sign > 0 ? (topName === "Fox" ? "Fox News" : topName) : "the other outlets") }
				: (example?.(p.word, p.z) ?? null);
			return { p, sign, y: yOf(i), x, eg };
		}
		return null;
	});
	// the card's own size, measured once it renders, places it
	let cardW = $state(320);
	let cardH = $state(120);
	const ARROW = 9; // the pointer's height, and the gap it makes
	let tipBox = $derived.by(() => {
		if (!tip) return null;
		const left = Math.max(0, Math.min(WIDTH - cardW, tip.x - cardW / 2));
		// room above is measured on the screen, not in the frame: the chart
		// sits in a sticky box, so the frame's top may be off the screen
		const frameTop = el?.getBoundingClientRect().top ?? 0;
		const above = frameTop + tip.y - ROW / 2 - ARROW - cardH >= 4;
		return {
			left,
			top: above ? tip.y - ROW / 2 - ARROW - cardH : tip.y + ROW / 2 + ARROW,
			above,
			// the arrow stays on the bar even when the card has been slid
			arrow: Math.max(14, Math.min(cardW - 14, tip.x - left))
		};
	});
</script>

<svelte:window onclick={clickAway} bind:innerWidth={screenW} />

<div class="word-bars" bind:this={el}>
	{#if source}
		<!-- the column heads -->
		<svg width={WIDTH} height={TOP - 24 + headExtra} viewBox="0 0 {WIDTH} {TOP - 24 + headExtra}" 
			role="presentation"
			aria-label="Diverging bar chart showing words that are distinctive to {topName} and to {otherName}">
			{#if source.topHead}
				<!-- heads at the bars' outer edges, saying what each side means:
				     "← Other outlets use more" · "Fox News uses more →" -->
				{#if edgeOneLine}
					<text class="head edge others" x={0} y="10" text-anchor="start">{EDGE_OTHERS}</text>
					<text class="head edge fox" x={WIDTH} y="10" text-anchor="end">{EDGE_FOX}</text>
				{:else}
					<!-- too narrow for both on one line: each breaks before "to" (the short
					     wording, with no "to", before its last word), the arrow on the first line -->
					{@const split = (t) => { const bare = t.replace(/\s*[←→]\s*/g, ""); const to = bare.indexOf(" to "); const i = to > 0 ? to : bare.lastIndexOf(" "); return i > 0 ? [bare.slice(0, i), bare.slice(i + 1)] : [bare, ""]; }}
					<text class="head edge narrow others" x={mid - barsReach} y="11" text-anchor="start"
						><tspan x={mid - barsReach}>← {split(EDGE_OTHERS)[0]}</tspan><tspan x={mid - barsReach} dy={HEAD_LINE}>{split(EDGE_OTHERS)[1]}</tspan></text
					>
					<text class="head edge narrow fox" x={mid + barsReach} y="11" text-anchor="end"
						><tspan x={mid + barsReach}>{split(EDGE_FOX)[0]} →</tspan><tspan x={mid + barsReach} dy={HEAD_LINE}>{split(EDGE_FOX)[1]}</tspan></text
					>
				{/if}
			{:else if source.bottomLogo}
				<!-- mirrored: "← [logo] in ESPN", the wordmark on the outer side -->
				{@const w = logoWidth(source.bottomLogo)}
				<text class="head others" x={mid - GAP} y="16" text-anchor="end" bind:this={bottomIn}
					>{source.bottomShort}</text
				>
				<image
					href="{base}/logos/{source.bottomLogo}"
					x={mid - GAP - bottomInWidth - 6 - w}
					y={16 - logoHeight(source.bottomLogo) + 2 - (15 - logoHeight(source.bottomLogo)) / 2}
					width={w}
					height={logoHeight(source.bottomLogo)}
					preserveAspectRatio="xMaxYMid meet"
				><title>{source.bottomShort}</title></image>
				<text class="head others" x={mid - GAP - bottomInWidth - 6 - w - 6} y="16" text-anchor="end">←</text>
			{:else}
				<text class="head others" x={mid - GAP} y="16" text-anchor="end"
					>← {source.bottomShort ?? "everyone else"}</text
				>
			{/if}
			{#if source.topHead}
				<!-- drawn above, with the other side's -->
			{:else if source.topLogo}
				{@const w = logoWidth(source.topLogo)}
				<text class="head fox" x={mid + GAP} y="16" text-anchor="start" bind:this={topIn}>{source.topShort}</text>
				<image
					href="{base}/logos/{source.topLogo}"
					x={mid + GAP + topInWidth + 6}
					y={16 - logoHeight(source.topLogo) + 2 - (15 - logoHeight(source.topLogo)) / 2}
					width={w}
					height={logoHeight(source.topLogo)}
					preserveAspectRatio="xMinYMid meet"
				><title>{source.topShort}</title></image>
				<text class="head fox" x={mid + GAP + topInWidth + 6 + w + 6} y="16" text-anchor="start">→</text>
			{:else}
				<text class="head fox" x={mid + GAP} y="16" text-anchor="start"
					>{source.topShort ?? "in Fox News"} →</text
				>
			{/if}
		</svg>
		<svg
			width={WIDTH}
			height={height - TOP + 6}
			viewBox="0 {TOP - 6} {WIDTH} {height - TOP + 6}"
			onmouseleave={() => (hovered = null)}
			role="presentation"
		>
			{#if empty}
				<text class="loading" x={mid} y={TOP + 40} text-anchor="middle">{LOADING}</text>
			{:else}
				<line class="axis" x1={mid} x2={mid} y1={TOP - 6} y2={height - BOTTOM} />
			{/if}

			{#each [[fox, 1], [others, -1]] as [list, sign]}
				{#if pins.rows && pins[sign].length}
					<!-- the gap between the page and the pinned words -->
					<text class="pin-gap" x={mid + sign * (GAP + LABEL + 10)} y={yOf(pins.keep) + 4} text-anchor={sign > 0 ? "start" : "end"}>⋯</text>
				{/if}
				{#each list as p, i (p.word)}
					{@const y = yOf(p.pin ? i + 1 : i)}
					{@const w = len(p.z)}
					{@const on = isOn(p.word)}
					{@const weak = Math.abs(p.z) < WEAK_Z}
					{@const color = weak ? WEAK_BAR : sign > 0 ? FOX : OTHERS}
					<!-- a label too long for its half (three-word phrases on a phone)
					     shrinks just enough to fit, down to 9px -->
					{@const room = mid - GAP - (beside || outside ? 0 : LABEL) - 18}
					{@const tw0 = textWidth(wordCase(p.word))}
					{@const fs = tw0 > room ? Math.max(9, (WORD_PX * room) / tw0) : WORD_PX}
					{@const tw = (tw0 * fs) / WORD_PX}
					{@const over = tw + 14 - w}
					<!-- a word that overhangs its bar by a hair slides in by that much -->
					{@const nudge = !beside && !outside && !tip_ && over > 0 && over <= 7 ? over : 0}
					{@const inside = !beside && !outside && !tip_ && over <= 7}
					{@const foot = sign > 0 ? mid + GAP + (outside ? 0 : LABEL) : mid - GAP - (outside ? 0 : LABEL)}
					{@const end = sign > 0 ? foot + w : foot - w}
					{@const reach =
						beside || outside
							? end
							: sign > 0
								? Math.max(end, foot + tw + 14)
								: Math.min(end, foot - tw - 14)}
					<g
						class="bar"
						class:dim={!on}
						class:weak
						class:hovered={hovered === p.word}
						onmouseenter={() => {
							hovered = p.word;
							onhover?.(p.word);
						}}
						onmouseleave={() => (hovered = null)}
						role="presentation"
					>
						<rect
							class="fill"
							x={sign > 0 ? foot : end}
							y={y - ROW * 0.36}
							width={w}
							height={ROW * 0.72}
							rx="3"
							fill={color}
						/>
						<!-- the word, white; past its bar's end it gets an outline in the
						     bar's colour so it still reads as the bar's label -->
						<text
							class="word"
							class:halo={!inside && !beside && !outside && !tip_}
							x={outside ? mid + sign * (GAP + span + 40) : beside ? mid + sign * GAP : tip_ ? end + sign * 7 : foot + sign * (7 - nudge)}
							y={y + 4.5}
							text-anchor={sign > 0 ? "start" : "end"}
							fill={!weak ? "#fff" : on || hovered === p.word ? WEAK_TEXT : WEAK_TEXT_FADED}
							style:--halo={weak ? "transparent" : color}
							font-size={fs}>{wordCase(p.word)}</text
						>
						{#if p.pin && (sign > 0 ? WIDTH - reach - 6 : reach - 6) >= String(p.rank).length * 7.5 + 10}
							<text class="pin-rank" x={reach + sign * 6} y={y + 4} text-anchor={sign > 0 ? "start" : "end"}>#{p.rank}</text>
						{/if}
						{#if capped(p.z)}
							<!-- a break mark: the bar runs past the frame's scale -->
							<path
								class="break"
								d="M{end - sign * 9},{y - ROW * 0.36 - 2} l{sign * 4},{ROW * 0.36} l{-sign * 4},{ROW * 0.36 + 2}"
							/>
						{/if}
						<!-- its score, past the bar or the word, whichever is longer
						     (with words at the tips the score stays in the tooltip) -->
						{#if showScores && !tip_}
						<text
							class="score"
							x={reach + sign * 6}
							y={y + 4}
							text-anchor={sign > 0 ? "start" : "end"}>{fmt(p.z)}</text
						>
						{/if}
					</g>
				{/each}
			{/each}
		</svg>
		<!-- always laid out where a chart can page, so it keeps its height; shown only when there are pages -->
		{#if more > 0}
		{@const showPager = paged && pages > 1 && pager}
		<div class="pager" class:off={!showPager} aria-hidden={!showPager} bind:this={pagerEl}>
			<button type="button" disabled={page === 0} onclick={() => (page -= 1)}>{or(previous, "← Previous")}</button>
			<span class="pager-range"
				>{fillIn(or(range, "{from}–{to} of {total}"), { from: page * topN + 1, to: Math.min(ranked, (page + 1) * topN), total: ranked })}</span
			>
			<button type="button" disabled={page >= pages - 1} onclick={() => (page += 1)}>{or(next, "Next →")}</button>
		</div>
		{/if}

		{#if tip}
			{@const color = Math.abs(tip.p.z) < WEAK_Z ? WEAK : tip.sign > 0 ? FOX : OTHERS}
			{@const shared = tip.p.af != null && tip.p.ao != null}
			{@const difference = capital(strengthOf(tip.p.z)) + (Math.abs(tip.p.z) >= STRENGTH_CUTS[0] ? " difference" : "")}
			<!-- the bold line: how sure the difference is -->
			<!-- its place on its side -->
			{@const rank = side(tip.sign).findIndex((p) => p.word === tip.p.word) + 1}
			{@const ratio = fillIn(SHARE_HEAD, { difference, strength: strengthOf(tip.p.z), score: fmt(tip.p.z) })}
			<!-- a "|" in the Doc's hover counts starts a new line -->
			<!-- with each side's article counts, the share of articles that use
			     it; otherwise (a player's chart) how often, then the uses. For
			     now the Doc's wording only takes over once it has those slots
			     ({topShare}, or {topUses}) -->
			{@const template = shared
				? (String(hoverCounts).includes("{topShare}") ? hoverCounts : SHARE_COUNTS)
				: (String(hoverCounts).includes("{topUses}") ? hoverCounts : USES_COUNTS)}
			{@const countLines = fillIn(template, {
				top: capital(topName),
				bottom: capital(otherName),
				topLabel: source?.sizes?.topLabel ?? capital(topName),
				bottomLabel: source?.sizes?.bottomLabel ?? capital(otherName),
				topItems: short(sideTotals.top),
				bottomItems: short(sideTotals.bottom),
				rank: count(rank),
				items: source?.sizes?.items ?? "articles",
				// the other side by name: "Others (combined)" when it pools several
				// outlets or players, the outlet's own name when it is one
				bottomAll: /other/i.test(String(source?.bottomLabel ?? "other"))
					? `${capital(otherName)} (combined)`
					: capital(source.bottomLabel),
				topUses: count(tip.p.nf),
				bottomUses: count(tip.p.no),
				topTimes: `${count(tip.p.nf)} ${+tip.p.nf === 1 ? "use" : "uses"}`,
				bottomTimes: `${count(tip.p.no)} ${+tip.p.no === 1 ? "use" : "uses"}`,
				topShare: shared ? pct(tip.p.af, sideTotals.top) : "",
				bottomShare: shared ? pct(tip.p.ao, sideTotals.bottom) : "",
				topCount: pct(shared ? tip.p.af : tip.p.nf, sideTotals.top),
				bottomCount: pct(shared ? tip.p.ao : tip.p.no, sideTotals.bottom),
				score: fmt(tip.p.z),
				strength: strengthOf(tip.p.z),
				// "Very strong difference"; the weakest word stands alone ("Could be chance")
				difference,
				// "Used in 3.5× as many articles"
				// (too few uses for a ratio: "Share of articles")
				ratio: shared ? ratioOf(tip.p) || `Share of ${source?.sizes?.items ?? "articles"}` : ratioOf(tip.p)
			})
				.split(/\s*\|\s*/)
				.filter((line) => line.trim())}
			<div
				class="tip-card"
				bind:clientWidth={cardW}
				bind:clientHeight={cardH}
				class:below={!tipBox.above}
				style="left:{tipBox.left}px; top:{tipBox.top}px; --arrow:{tipBox.arrow}px"
			>
				<!-- the side's colour in a swatch and on the quote's rule; the words in ink -->
				<span class="tip-head">{properCase(tip.p.word, { nicknamesAsWords })}</span>
				{#if ratio}<span class="tip-ratio"
						>{#each ratio.split("**") as part, j}{#if j % 2}<strong>{part}</strong>{:else}{part}{/if}{/each}</span
					>{/if}
				<span class="tip-count"
					>{#each countLines as line, i}<span class="tip-count-line"
							>{#each line.split("**") as part, j}{#if j % 2}<strong>{part}</strong>{:else}{part}{/if}{/each}{#if tip.p.pin && !shared && i === countLines.length - 1} · #{tip.p.rank}{/if}</span
						>{/each}</span
				>
				{#if tip.eg}
					<p style="border-left-color:{color}">
						{#if tip.eg.o}<span class="tip-source">{tip.eg.o}</span>{/if}
						{@html markWord(tip.eg.s, tip.p.word, tip.eg.w, color, tip.eg.a)}
					</p>
				{/if}
			</div>
		{/if}

		<!-- what sits under the bars, measured as one, so the bars leave it room -->
		<div class="below" bind:this={belowEl}>
			{#if noteMode === "custom"}
				<!-- a source line spans the bars, edge to edge with the heads above -->
				<p class="note" class:source={noteKind === "source"}>{@html note}</p>
			{:else if noteMode === "stock"}
				<p class="note">
					Bars are each word's fightin'-words score. Tan bars score under {WEAK_Z},
					within noise. Hover a bar for an example.
				</p>
			{/if}
		</div>
	{/if}
</div>

<style>
	.loading {
		fill: var(--wnba-tan-dark);
		font-family: var(--font-sans);
		font-size: 14px;
	}
	.word-bars {
		width: 100%;
		max-width: 720px;
		margin: 0 auto 5rem auto;
		position: relative;
	}
	svg {
		display: block;
		overflow: visible;
	}
	/* Previous / Next: small underlined links, so they don't pull the eye off the bars */
	.pager {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
		margin-top: 6px;
		font-family: var(--font-chart);
		font-size: 12px;
		color: var(--color-fg);
	}
	/* kept in place but unseen (and out of the tab order) when there's one page;
	   it fades and rises in as the player chart's "Compared with" line does,
	   then a highlighter swipes across it and off again (menu-swipe) */
	.pager {
		width: fit-content;
		max-width: 100%;
		margin: 6px auto 0;
		padding: 1px 4px;
		background-image: linear-gradient(
			rgba(255, 230, 0, 0.55),
			rgba(255, 230, 0, 0.55)
		);
		background-repeat: no-repeat;
		background-size: 0% 100%;
		background-position: left;
		transition:
			opacity 450ms ease,
			transform 450ms cubic-bezier(0.22, 0.8, 0.3, 1),
			visibility 0s;
	}
	.pager.off {
		opacity: 0;
		transform: translateY(8px);
		visibility: hidden;
		/* stays visible until the fade out ends */
		transition:
			opacity 450ms ease,
			transform 450ms cubic-bezier(0.22, 0.8, 0.3, 1),
			visibility 0s linear 450ms;
	}
	.pager:not(.off) {
		animation: menu-swipe 1.6s ease 400ms both;
	}
	@keyframes menu-swipe {
		40% {
			background-size: 100% 100%;
			background-position: left;
		}
		65% {
			background-size: 100% 100%;
			background-position: right;
		}
		100% {
			background-size: 0% 100%;
			background-position: right;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.pager,
		.pager.off {
			transition: none;
		}
		.pager:not(.off) {
			animation: none;
		}
	}
	.pager button {
		appearance: none;
		border: 0;
		background: none;
		padding: 2px 0;
		color: var(--color-fg);
		font: inherit;
		text-decoration: underline;
		text-underline-offset: 2px;
		cursor: pointer;
	}
	.pager button:disabled {
		opacity: 0.3;
		text-decoration: none;
		cursor: not-allowed;
	}
	.pager-range {
		font-variant-numeric: tabular-nums;
		color: var(--wnba-tan-dark);
	}
	.head {
		font-family: var(--font-chart);
		text-transform: uppercase !important;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}
	.head.fox {
		fill: var(--color-fox-navy);
		text-transform: uppercase;
		font-size: 12px;
	}
	/* the edge heads: sentence case, a little larger */
	.head.edge {
		text-transform: uppercase;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0;
		text-transform: none;
	}
	.head.edge.narrow {
		text-transform: uppercase;
		font-size: 12px;
	}
	.head.others {
		fill: var(--color-outlets);
		text-transform: uppercase;
		font-size: 12px;
	}
	.pin-gap {
		font-size: 16px;
		font-weight: 700;
		fill: rgba(42, 21, 3, 0.5);
	}
	.pin-rank {
		font-family: var(--font-sans);
		font-size: 12px;
		font-weight: 700;
		fill: rgba(42, 21, 3, 0.6);
	}
	.axis {
		stroke: var(--wnba-tan-dark);
		stroke-width: 1.5;
	}
	.break {
		fill: none;
		stroke: var(--color-paper, var(--color-paper));
		stroke-width: 3;
	}
	.bar .fill {
		opacity: 0.88;
		transition: opacity 250ms ease;
	}
	/* a bar outside the step's words fades, but its label stays legible */
	.bar.dim .fill {
		opacity: 0.22;
		filter: none;
	}
	.bar.dim .word,
	.bar.dim .score {
		opacity: 0.55;
	}
	.bar:hover .fill {
		opacity: 1;
	}
	/* a word within noise floats on a pale bar, which fades less than the dark
	   bars do because it starts so close to the page */
	.bar.weak .fill {
		opacity: 1;
	}
	.bar.weak.dim .fill {
		opacity: 0.5;
	}
	.bar.weak.dim .word {
		opacity: 1;
	}
	.bar.weak:hover .fill,
	.bar.weak.hovered .fill {
		fill: var(--wnba-tan-mid);
		opacity: 1;
	}
	/* the hovered (or tapped) bar's words at full strength, faded bar or not */
	.bar:hover .word,
	.bar:hover .score,
	.bar:hover .pin-rank,
	.bar.hovered .word,
	.bar.hovered .score,
	.bar.hovered .pin-rank {
		opacity: 1;
	}
	.word {
		font-family: var(--font-chart);
		font-weight: 700;
		pointer-events: none;
	}
	/* a word that runs past its bar keeps its white, with an outline in the
	   bar's own colour around the letters */
	.word.halo {
		paint-order: stroke;
		stroke: var(--halo);
		stroke-width: 3.5px;
		stroke-linejoin: round;
	}
	.score {
		font-family: var(--font-chart);
		font-size: 11px;
		font-weight: 600;
		fill: rgba(42, 21, 3, 0.6);
		pointer-events: none;
	}
	.tip-card {
		position: absolute;
		z-index: 8;
		pointer-events: none;
		width: 300px;
		max-width: 80vw;
		background: var(--color-white);
		border: 1px solid var(--color-rule);
		border-radius: 4px;
		padding: 0.75rem 1rem;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
		color: var(--color-fg);
		font-size: 12.5px;
		pointer-events: none;
	}
	/* the shared tooltip (variables.css) */
	.tip-head {
		display: block;
		font-size: 18px;
		font: var(--tip-title);
	}
	.tip-ratio {
		display: block;
		font: var(--tip-small);
		color: var(--color-fg);
		margin: 2px 0 0;
	}
	.tip-card .swatch {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 2px;
		margin-right: 7px;
		vertical-align: 1px;
	}
	.tip-source {
		display: block;
		font: var(--tip-small);
		color: var(--wnba-tan-dark);
		margin-top: 4px;
	}
	.tip-count {
		display: block;
		font: var(--tip-small);
		color: var(--wnba-tan-dark);
		margin: 3px 0 0;
	}
	.tip-count-line {
		display: block;
	}
	.tip-card p {
		margin: 9px 0 0;
		padding: 1px 0 1px 9px;
		border-left: 3px solid var(--tip-rule);
		font: var(--tip-quote);
		color: var(--color-fg);
		font-style: italic;
	}
	/* the pointer: a paper triangle with the same hairline, at the bar */
	/* .tip-card::after,
	.tip-card::before {
		content: "";
		position: absolute;
		left: var(--arrow, 50%);
		transform: translateX(-50%);
		border: 8px solid transparent;
	}
	.tip-card::before {
		bottom: -17px;
		border-top-color: var(--tip-border);
	}
	.tip-card::after {
		bottom: -15px;
		border-top-color: var(--tip-bg);
	}
	.tip-card.below::before {
		bottom: auto;
		top: -17px;
		border-top-color: transparent;
		border-bottom-color: var(--tip-border);
	}
	.tip-card.below::after {
		bottom: auto;
		top: -15px;
		border-top-color: transparent;
		border-bottom-color: var(--tip-bg);
	} */
	/* a flow-root keeps the note's margins inside, so its measured height is all of it */
	.below {
		display: flow-root;
	}
	.note {
		margin: 6px auto 0;
		padding-bottom: 2rem;
		font-size: 12px;
		color: var(--wnba-tan-dark);
		text-align: center;
	}
	.note.source {
		font-family: var(--font-sans);
		margin-top: 2rem;
		padding-top: 8px;
		border-top: 1px solid var(--color-rule);
		text-align: left;
		line-height: 1.5;
	}
</style>
