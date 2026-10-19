<script>
	// Fightin' Words plot (Monroe, Colaresi & Quinn)
	import { scaleLinear, scaleLog, scaleSqrt } from "d3-scale";
	import WordBars from "$components/WordBars.svelte";
	import { base } from "$app/paths";
	import fw from "$data/fighting_words.json";
	const data = fw.grid;
	// story-word examples ship inline
	const litExamples = fw.lit;
	// the bundle carries the pooled comparisons only (stats as [z, n, fox, other]
	// under `s`); article words and phrases, and each single outlet's numbers,
	// are fetched from static/data when first shown (notebooks/site_data.py).
	// The single-outlet pills are an evaluation tool: the dev server only.
	const DEV = import.meta.env.DEV;
	const slug = (label) =>
		label
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-|-$/g, "");
	let articleWords = $state(null);
	let articleBigrams = $state(null);
	let articleTrigrams = $state(null);
	let outletStats = $state({});
	const fetching = new Set();
	async function ensureFile(key, url, assign) {
		if (fetching.has(key)) return;
		fetching.add(key);
		try {
			assign(await (await fetch(url)).json());
		} catch {
			assign([]);
		}
	}

	const FOX = "var(--color-fox-navy)"; // Fox's chart colour, set once in variables.css
	const OTHER = "var(--color-outlets)"; // the other outlets' purple
	const SIGNIFICANT = 1.96;
	const SANS = "var(--font-chart)";

	// crude greedy wrap: SVG text has no box to flow inside
	function wrap(sentence, perLine = 48, lines = 3) {
		const words = sentence.split(" ");
		const out = [];
		let line = "";
		for (const word of words) {
			if ((line + " " + word).trim().length > perLine) {
				out.push(line.trim());
				line = word;
			} else line += " " + word;
			if (out.length === lines) break;
		}
		if (out.length < lines && line.trim()) out.push(line.trim());
		return out
			.slice(0, lines)
			.map((l, i) =>
				i === lines - 1 && words.join(" ").length > perLine * lines
					? l + "…"
					: l
			);
	}

	// the logos drawn under "use this more ↓" for each comparison pool
	// the logos each comparison group stands for (the footnote), and the one
	// logo each outlet's pill shows
	import LogoSelect from "$components/helpers/LogoSelect.svelte";
	import { properCase } from "$utils/properCase.js";
	import { isGameTerm } from "$utils/gameWords.js";
	import { isNameTerm } from "$utils/nameWords.js";
	import { checks } from "$utils/checks.svelte.js";
	import {
		COMPARISON,
		SPORTS,
		NEWS,
		GROUPS,
		AGGREGATES,
		LOGO as PILL_LOGO,
		LOGO_WIDTH,
		inOutlet,
		outletName
	} from "$utils/outlets.js";
	// the wordmarks drawn under the chart for whatever Fox is set against: an
	// outlet's own, or a group's members (all 13 would not fit: none for "all")
	const LOGOS = {
		"sports outlets": SPORTS.map((o) => PILL_LOGO[o]),
		"news outlets": NEWS.map((o) => PILL_LOGO[o]),
		...Object.fromEntries(COMPARISON.map((o) => [o, [PILL_LOGO[o]]]))
	};
	const PILL_NAME = { "sports outlets": "sports", "news outlets": "news" };
	// the dropdown's name for an outlet or a pool
	const outletOption = (outlet) =>
		outlet === ALL_OUTLETS
			? or(allOutlets, "six other outlets")
			: (PILL_NAME[outlet] ?? outlet).replace(/^./, (c) => c.toUpperCase());
	const pooledIn = (group, outlet) => (GROUPS[group] ?? []).includes(outlet);

	// `source` ({points, topLabel, bottomLabel}) lets another dataset borrow the chart
	let {
		highlight = null,
		bare = false,
		controls = true,
		// pager: Previous / Next under the bars (a scrolly holds it back until
		// its last card, 2026-10-02)
		pager: showPager = true,
		mode = null,
		source = null,
		// chart: "scatter" (the quadrant) or "bars" (mirrored top words)
		chart = "scatter",
		// labels, scale, caps: see WordBars
		labels = "on",
		scale = "linear",
		caps = false,
		scores = false,
		// ngrams: 2 — two-word phrases instead of words (whole articles only)
		ngrams = 1,
		// fill: stretch the bar rows down the viewport (the scrolly sets it)
		fill = false,
		// note: the line under the bars (see WordBars)
		note = undefined,
		// the Doc's words, each optional, {slots} filled in (utils/fill.js):
		//   heading: How Fox News writes about the WNBA ({unit} works too)
		//   comparedWith: compared with    allOutlets: six other outlets
		//   tabWords, tabTwo, tabThree, search,
		//   rankFox: Fox #{rank}   rankOthers: Others #{rank}   rankEven: Even
		//   foxHead, othersHead, caption ({fox} {others} {them}),
		//   previous, next, range, hoverCounts (see WordBars)
		heading: headingText = "",
		comparedWith = "",
		allOutlets = "",
		tabWords = "",
		tabTwo = "",
		tabThree = "",
		search = "",
		rankFox = "",
		rankOthers = "",
		rankEven = "",
		foxHead = "",
		othersHead = "",
		caption: captionText = "",
		previous = "",
		next = "",
		range = "",
		hoverCounts = "",
		...rest
	} = $props();
	import { fill as fillIn, or } from "$utils/fill.js";
	// words, two-word or three-word phrases: the Doc's `ngrams` sets it, the
	// Show dropdown flips it (three-word phrases added 2026-09-30)
	let gram = $state(1);
	$effect(() => {
		const n = String(ngrams).trim();
		gram = n === "3" ? 3 : n === "2" ? 2 : 1;
	});
	// the article mode's key in the data and the example stores
	let bodyKey = $derived(
		gram === 3 ? "trigrams" : gram === 2 ? "bigrams" : "articles"
	);

	// the outlet pills, as on the dot plot: "all", then one logo per outlet
	const ALL_OUTLETS = "all outlets";

	// the words lit on the chart: a step's list, plus whatever the explore
	// step's search box finds or keeps
	let HIGHLIGHT = $derived(
		new Set([...(highlight ?? []).map((w) => w.toLowerCase()), ...searchLit])
	);
	let beating = $derived(HIGHLIGHT.size > 0);

	const ALL = "all coverage";
	let text = $state(mode ?? "headlines");
	let against = $state(data.outlets[0]);
	let player = $state(ALL);
	const topName = "Fox";
	const bottomName = "others";

	let bodyMode = $derived(
		text === "articles" && player === ALL && !!data.hasArticles
	);
	// while a file is still loading, keep showing what is on screen rather than
	// flashing an empty chart (the words/phrases switch used to blank it)
	let lastWords = [];
	// A check, shown only with ?checks in the address (utils/checks.svelte.js):
	// with or without college coverage, that the words hold on WNBA coverage
	// alone. The no-college files come from a rerun of notebook 06 with college
	// articles dropped from every outlet (static/data/nocollege/, 2026-09-30).
	let college = $state("with");
	let noCollege = $derived(college === "without" && player === ALL);
	let nc = $state({
		head: null,
		articles: null,
		bigrams: null,
		trigrams: null
	});
	$effect(() => {
		if (!noCollege) return;
		if (!nc.head)
			ensureFile(
				"nc-head",
				`${base}/data/nocollege/fw_headlines.json`,
				(v) => (nc = { ...nc, head: v })
			);
		if (!nc.articles)
			ensureFile(
				"nc-articles",
				`${base}/data/nocollege/fw_articles.json`,
				(v) => (nc = { ...nc, articles: v })
			);
		if (!nc.bigrams)
			ensureFile(
				"nc-bigrams",
				`${base}/data/nocollege/fw_bigrams.json`,
				(v) => (nc = { ...nc, bigrams: v })
			);
		if (!nc.trigrams)
			ensureFile(
				"nc-trigrams",
				`${base}/data/nocollege/fw_trigrams.json`,
				(v) => (nc = { ...nc, trigrams: v })
			);
	});
	// A check, shown only with ?checks: "Leave out" game words (the box score, results, teams and cities), so
	// what is left is how the coverage talks about the league rather than the
	// games, and/or people's names, so what is left is what is said rather than
	// who it is said about (src/utils/gameWords.js, nameWords.js; 2026-09-30)
	let leaveOut = $state("none");
	let hideGame = $derived(leaveOut === "game" || leaveOut === "both");
	let hideNames = $derived(leaveOut === "names" || leaveOut === "both");
	let words = $derived.by(() => {
		const next = noCollege
			? bodyMode
				? nc[bodyKey]
				: nc.head?.words
			: bodyMode
				? gram === 3
					? articleTrigrams
					: gram === 2
						? articleBigrams
						: articleWords
				: player === ALL
					? data.words
					: (data.byPlayer?.[player] ?? []);
		if (next) lastWords = next;
		return next ?? lastWords;
	});
	// both article files load together as soon as articles are shown, so the
	// words/phrases switch has nothing left to fetch
	$effect(() => {
		if (!bodyMode) return;
		if (!articleWords)
			ensureFile(
				"articles",
				`${base}/data/fw_articles.json`,
				(v) => (articleWords = v)
			);
		if (!articleBigrams)
			ensureFile(
				"bigrams",
				`${base}/data/fw_bigrams.json`,
				(v) => (articleBigrams = v)
			);
		if (!articleTrigrams)
			ensureFile(
				"trigrams",
				`${base}/data/fw_trigrams.json`,
				(v) => (articleTrigrams = v)
			);
	});
	// a single outlet's numbers, one file per outlet, fetched on its pill
	// the pools, the pair and the comparison outlets ship in the bundle; other pills are dev-only
	const POOLED = [...AGGREGATES, ...COMPARISON];
	let single = $derived(!POOLED.includes(against));
	$effect(() => {
		if (single && !outletStats[against])
			ensureFile(
				against,
				`${base}/data/fw_outlet/${slug(against)}.json`,
				(v) => (outletStats = { ...outletStats, [against]: v })
			);
	});
	// the stats of a word in the current comparison: [z, n, fox, other]
	let modeKey = $derived(bodyMode ? bodyKey : "headlines");
	function statOf(entry) {
		if (!single) return entry.s?.[against];
		const table = outletStats[against];
		if (!table) return undefined;
		return player === ALL
			? table[modeKey]?.[entry.word]
			: table.players?.[player]?.[entry.word];
	}
	// over articles, "all outlets" is literally the same corpus as "Yahoo + ESPN" — dedupe
	let articleOutlets = $derived.by(() => {
		const seen = new Map();
		for (const name of data.articleOutlets ?? []) {
			const key = JSON.stringify(data.articleOutletN?.[name] ?? {});
			// a later duplicate replaces "all outlets" only
			if (!seen.has(key) || seen.get(key) === "all outlets")
				seen.set(key, name);
		}
		return [...seen.values()];
	});
	let outletsHere = $derived(
		(bodyMode
			? articleOutlets
			: player === ALL
				? [...data.outlets, ...(data.outletsExtra ?? [])]
				: Object.keys(data.playerN?.[player] ?? {}).sort()
		).filter((o) => DEV || POOLED.includes(o))
	);
	let sample = $derived(
		(noCollege
			? (bodyMode ? nc.head?.articleOutletN : nc.head?.outletN)?.[against]
			: bodyMode
				? data.articleOutletN?.[against]
				: player === ALL
					? data.outletN?.[against]
					: data.playerN?.[player]?.[against]) ?? null
	);
	let floor = $derived(player === ALL ? 5 : 3);
	// the line under the bars, in the topic graphics' source-line style
	// (2026-10-02): what was compared, then how it was scored
	let caption = $derived.by(() => {
		if (!sample) return note;
		const them =
			against === ALL_OUTLETS ? "the other outlets" : outletName(against);
		const what = bodyMode
			? "WNBA articles"
			: player === ALL
				? "WNBA headlines"
				: `headlines naming ${player}`;
		const sqrt = String(scale).toLowerCase() === "sqrt" || mobile;
		const vars = {
			fox: sample.fox.toLocaleString(),
			others: sample.other.toLocaleString(),
			them
		};
		if (String(captionText).trim()) return fillIn(captionText, vars);
		return (
			`Fox News: ${sample.fox.toLocaleString()} ${what}; ${them}: ${sample.other.toLocaleString()}, April 2023 on${noCollege ? ", college coverage left out" : ""}. ` +
			`Words ranked by weighted log-odds with an informative prior (Monroe et al. 2008); ` +
			`bar length is ${sqrt ? "the square root of the z-score, so one runaway word doesn’t flatten the rest" : "the z-score"}. ` +
			`Faded bars are within noise (|z| under 1.96). Hover a bar for an example.`
		);
	});

	// the unit tabs' names, which the heading borrows
	const unitName = (n) =>
		n === 3
			? or(tabThree, "Three-word phrases")
			: n === 2
				? or(tabTwo, "Two-word phrases")
				: or(tabWords, "Words");

	// --- the explore step's search box (as on the ternary) -----------------
	// the search, as in the redesign demo (2026-10-02): typing only suggests,
	// each suggestion tagged with its side and rank; picking one lights it (a
	// word off the page is pinned under it at its rank) and a line under the
	// chart says how the two sides use it, with an example
	let query = $state("");
	let found = $state(null);
	let q = $derived(query.trim().toLowerCase());
	let vocabulary = $derived(
		[...points]
			.map((pt) => ({ term: pt.word.toLowerCase(), n: pt.n, z: pt.z }))
			.sort((a, b) => b.n - a.n)
	);
	let exact = $derived(
		q ? (vocabulary.find((t) => t.term === q) ?? null) : null
	);
	// each word's rank on its own side, by the strength of its score
	let rankOf = $derived.by(() => {
		const m = new Map();
		for (const sign of [1, -1])
			points
				.filter((pt) => Math.sign(pt.z) === sign)
				.sort((a, b) => Math.abs(b.z) - Math.abs(a.z))
				.forEach((pt, i) => m.set(pt.word.toLowerCase(), i + 1));
		return m;
	});
	let suggestions = $derived.by(() => {
		if (!q) return [];
		const starts = vocabulary.filter((t) => t.term.startsWith(q));
		const inside = vocabulary.filter(
			(t) => !t.term.startsWith(q) && t.term.includes(q)
		);
		return [...starts, ...inside].slice(0, 8);
	});
	let searchLit = $derived(found ? [found] : []);
	let open = $state(false);
	let cursor = $state(-1);
	const choose = (word) => {
		found = word;
		query = properCase(word);
		open = false;
		cursor = -1;
		if (!source) ensureExamples();
	};
	// clearing the box lets the word go
	$effect(() => {
		if (!q) found = null;
	});
	function onKey(e) {
		if (e.key === "ArrowDown") {
			cursor = Math.min(cursor + 1, suggestions.length - 1);
			e.preventDefault();
		} else if (e.key === "ArrowUp") {
			cursor = Math.max(cursor - 1, -1);
			e.preventDefault();
		} else if (e.key === "Enter") {
			const word =
				cursor >= 0
					? suggestions[cursor]?.term
					: (exact?.term ?? suggestions[0]?.term);
			if (word) choose(word);
			e.preventDefault();
		} else if (e.key === "Escape") {
			query = "";
			cursor = -1;
		}
	}

	let points = $derived(
		source
			? source.points
			: words
					.filter(
						(entry) =>
							!(hideGame && isGameTerm(entry.word)) &&
							!(hideNames && isNameTerm(entry.word))
					)
					.map((entry) => [entry, statOf(entry)])
					.filter(([, s]) => s && s[1] >= floor)
					.map(([entry, s]) => ({
						word: entry.word,
						z: s[0],
						n: s[1],
						nf: s[2] ?? 0,
						no: s[3] ?? 0
					}))
	);

	$effect(() => {
		if (!outletsHere.includes(against)) against = outletsHere[0];
	});

	let viewportWidth = $state(
		typeof window === "undefined" ? 1200 : window.innerWidth
	);
	let mobile = $derived(viewportWidth < 640);
	let WIDTH = $derived(mobile ? 480 : 880);
	let HEIGHT = $derived(mobile ? 620 : 560);
	let PAD = $derived(
		mobile
			? { top: 26, right: 22, bottom: 52, left: 44 }
			: { top: 26, right: 40, bottom: 48, left: 52 }
	);

	// the domain must survive an empty or single-valued set
	let xScale = $derived(
		scaleLog()
			.domain([
				Math.max(3, Math.min(1e9, ...points.map((p) => p.n))),
				Math.max(30, ...points.map((p) => p.n))
			])
			.range([PAD.left, WIDTH - PAD.right])
	);
	let reach = $derived(Math.max(5, ...points.map((p) => Math.abs(p.z))));
	let yScale = $derived(
		scaleLinear()
			.domain([-reach, reach])
			.range([HEIGHT - PAD.bottom, PAD.top])
	);
	let sizeScale = $derived(scaleSqrt().domain([0, reach]).range([1.4, 6]));

	// real label widths, measured in the chart's own font once it is on the page
	let rootEl = $state(null);
	let measureCtx = null;
	function textWidth(word, size, weight) {
		if (typeof document === "undefined" || !rootEl)
			return word.length * size * 0.5;
		if (!measureCtx)
			measureCtx = document.createElement("canvas").getContext("2d");
		measureCtx.font = `${weight} ${size}px ${getComputedStyle(rootEl).fontFamily}`;
		return measureCtx.measureText(word).width;
	}

	let labelled = $derived.by(() => {
		rootEl; // re-run once the font can be measured
		// a player chart has few enough words to label them all: the weak ones
		// (near the middle: both sides use the word about equally) in a lighter
		// hand, so the strong ones still read first. The big archive chart
		// labels only what clears the threshold.
		const strong = source
			? points
			: points.filter((p) => Math.abs(p.z) > SIGNIFICANT);
		const isLit = (p) =>
			HIGHLIGHT.has(p.word.toLowerCase()) || HIGHLIGHT.has(p.word);
		const ranked = [
			...strong.filter(isLit).sort((a, b) => Math.abs(b.z) - Math.abs(a.z)),
			...strong
				.filter((p) => !isLit(p))
				.sort((a, b) => Math.abs(b.z) - Math.abs(a.z))
		];
		const placed = [];
		// the more words a step names, the smaller their labels: a dozen at
		// full size, forty at about two thirds
		const litSize = (full) =>
			Math.round(
				full * Math.max(0.68, 1 - Math.max(0, HIGHLIGHT.size - 12) * 0.011) * 2
			) / 2;
		// a label's box, for the clash test
		const boxFor = (point, px, py, side, size, weight, rowH) => {
			// plus the paint-order halo on each side
			const w = textWidth(point.word, size, weight) + 18;
			return {
				x0: side < 0 ? px - 6 - w : px + 6,
				x1: side < 0 ? px - 6 : px + 6 + w,
				y0: py - rowH / 2,
				y1: py + rowH / 2
			};
		};
		const clashes = (box) =>
			placed.some(
				(o) =>
					box.x0 < o.box.x1 &&
					o.box.x0 < box.x1 &&
					box.y0 < o.box.y1 &&
					o.box.y0 < box.y1
			);
		for (const point of ranked) {
			const lit = isLit(point);
			if (beating && !lit) continue;
			if (!source && placed.length > 34 && !lit) continue;
			// the archive chart: a word nobody named needs a real score to earn
			// a label, so a lone weak word at the edge does not get one just
			// because it has room
			if (!source && !lit && Math.abs(point.z) < 8) continue;
			const px = xScale(point.n),
				py = yScale(point.z);
			const weak = Boolean(source) && Math.abs(point.z) <= SIGNIFICANT;
			// the label's font, as the stylesheet sets it (.big for player charts)
			const size = source
				? weak
					? 17
					: lit
						? 28
						: 24
				: mobile
					? lit
						? litSize(18.5)
						: 15.5
					: lit
						? litSize(22)
						: 18;
			const weight = lit ? 800 : weak ? 500 : 600;
			const rowH = size * 1.3;
			// try beside the dot, then the other side, then a row up or down,
			// before giving up; a player chart tries harder, since every word
			// there gets a label
			const nearRight = px > WIDTH - PAD.right - 70;
			const sides = nearRight ? [-1, 1] : [1, -1];
			// a named word on the archive chart searches a long way for room:
			// the step's words must all show
			// a label may move a row or two to find room, no further: a word
			// that finds none is left unlabelled (its dot still lights)
			const shifts = source
				? [0, -0.8, 0.8, -1.6, 1.6, -2.4, 2.4, -3.2, 3.2]
				: [0, -0.8, 0.8, -1.6, 1.6];
			let spot = null;
			for (const dy of shifts) {
				for (const side of sides) {
					const box = boxFor(
						point,
						px,
						py + dy * rowH,
						side,
						size,
						weight,
						rowH
					);
					if (box.x0 < PAD.left || box.x1 > WIDTH - PAD.right + 4) continue;
					// never outside the drawing: a label pushed off the top or bottom is no label
					if (box.y0 < 2 || box.y1 > HEIGHT - PAD.bottom + 6) continue;
					if (!clashes(box)) {
						spot = { side, dy, box };
						break;
					}
				}
				if (spot) break;
			}
			if (!spot) continue;
			placed.push({
				...point,
				size,
				px,
				py: py + spot.dy * rowH,
				// where the dot is, and whether the label had to leave it
				dotY: py,
				moved: Math.abs(spot.dy) >= 1.6,
				lit,
				flip: spot.side < 0,
				weak,
				box: spot.box
			});
		}
		return placed;
	});

	let hovered = $state(null);
	let tip = $state(null);
	function showTip(event, point) {
		hovered = point.word;
		if (!source) ensureExamples();
		const box = event.currentTarget
			.closest(".fightin-words")
			?.getBoundingClientRect();
		tip = {
			...point,
			px: xScale(point.n),
			py: yScale(point.z),
			cx: box ? event.clientX - box.left : 0,
			cy: box ? event.clientY - box.top : 0,
			boxW: box ? box.width : 0,
			boxH: box ? box.height : 0
		};
	}
	const hideTip = () => {
		hovered = null;
		tip = null;
	};

	let fullExamples = $state(null);
	async function ensureExamples() {
		if (fullExamples) return;
		try {
			fullExamples = (await import("$data/fighting_words_examples.json"))
				.default;
		} catch {
			fullExamples = {};
		}
	}
	// against one outlet, that outlet's side quotes that outlet
	// (notebooks/06 → static/data/fw_examples_by_outlet.json), fetched once
	let outletExamples = $state(null);
	let outletExamplesLoading = false;
	async function ensureOutletExamples() {
		if (outletExamples || outletExamplesLoading) return;
		outletExamplesLoading = true;
		try {
			outletExamples = await (
				await fetch(`${base}/data/fw_examples_by_outlet.json`)
			).json();
		} catch {
			outletExamples = {};
		} finally {
			outletExamplesLoading = false;
		}
	}
	$effect(() => {
		if (against !== ALL_OUTLETS) ensureOutletExamples();
	});
	// the example for a word on the comparison side: the chosen outlet's own
	// sentence, or for a pooled group one of its members' sentences. A word on
	// that side never borrows a sentence from an outlet outside the comparison
	// (a Breitbart word once showed a CBS Sports quote), so with no sentence
	// found the card shows none. Fox's side and "all outlets" use the shared store.
	function exampleFor(mode, word, z) {
		if (z < 0 && against !== ALL_OUTLETS) {
			const members = AGGREGATES.includes(against)
				? (GROUPS[against] ?? [])
				: [against];
			for (const outlet of members) {
				const own = outletExamples?.[outlet]?.[mode]?.[word];
				if (own) return own;
			}
			return outletExamples ? null : undefined;
		}
		return litExamples[mode]?.[word] ?? fullExamples?.[mode]?.[word];
	}

	// the bars take the same points, with short side names for their heads
	let barSource = $derived(
		source ?? {
			points,
			topShort: "in Fox News",
			bottomShort:
				against === ALL_OUTLETS
					? "in the other outlets"
					: AGGREGATES.includes(against)
						? `in the ${against}`
						: inOutlet(against),
			// only Fox's head carries its wordmark; the other side is named in words
			topLogo: PILL_LOGO["Fox News"] ?? "fox-news.svg",
			// the heads at the bars' outer edges, saying what each side means
			topHead: or(foxHead, "Fox News uses more"),
			bottomHead:
				against === ALL_OUTLETS
					? or(othersHead, "Other outlets use more")
					: (() => {
							const n = AGGREGATES.includes(against)
								? `the ${against}`
								: outletName(against);
							return (
								n.charAt(0).toUpperCase() +
								n.slice(1) +
								(/s$/.test(n) && !/news$/i.test(n) ? " use more" : " uses more")
							);
						})()
		}
	);
	// a bar's example on hover, from the same stores as the scatter's card
	function barExample(word, z = 0) {
		const mode = bodyMode ? bodyKey : "headlines";
		const hit = exampleFor(mode, word, z);
		return hit?.[0] ? { s: hit[0], w: hit[1], o: hit[2] ?? null } : null;
	}

	let cardEx = $derived.by(() => {
		if (!tip) return null;
		if (source)
			return tip.eg
				? { s: tip.eg, w: tip.egw, a: tip.ega, o: tip.ego ?? null }
				: null;
		const mode = bodyMode ? bodyKey : "headlines";
		const hit = exampleFor(mode, tip.word, tip.z ?? 0);
		return { s: hit?.[0] ?? null, w: hit?.[1] ?? null, o: hit?.[2] ?? null };
	});

	// a beat swap can leave a stale tip captioned with the new side labels
	$effect(() => {
		source;
		hideTip();
	});

	const colorOf = (z) =>
		Math.abs(z) < SIGNIFICANT ? "rgba(42,21,3,0.28)" : z > 0 ? FOX : OTHER;

	const escapeHtml = (t) =>
		t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
	// the exact seen form wins ("held"); lemma prefix is the fallback ("hold" → "holding")
	const escRx = (t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	const wordRx = (word, form) =>
		form
			? new RegExp("\\b" + escRx(form) + "\\b", "i")
			: new RegExp("\\b" + escRx(word) + "\\w*", "i");

	// window around the word; irregular inflections may not match — fall back to the opening
	// the occurrence nearest the middle of the stored passage is the one meant
	// (the passage is the example sentence with a neighbour on either side)
	function nearestMatch(text, rx) {
		const g = new RegExp(
			rx.source,
			rx.flags.includes("g") ? rx.flags : rx.flags + "g"
		);
		let best = null;
		for (const m of text.matchAll(g)) {
			if (
				!best ||
				Math.abs(m.index - text.length / 2) <
					Math.abs(best.index - text.length / 2)
			)
				best = m;
		}
		return best;
	}
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
	function excerpt(sentence, word, form, at, budget = 300) {
		const m =
			(form && findWord(sentence, wordRx(word, form), at)) ||
			findWord(sentence, wordRx(word), at);
		if (sentence.length <= budget) return [sentence, m?.index];
		if (!m) return [sentence.slice(0, budget).replace(/\s\S*$/, "") + "…"];
		let start = Math.max(0, m.index - Math.round(budget * 0.45));
		if (start + budget > sentence.length)
			start = Math.max(0, sentence.length - budget);
		let out = sentence.slice(start, start + budget);
		let shift = start;
		if (start > 0) {
			const trimmed = out.replace(/^\S*\s/, "");
			shift += out.length - trimmed.length - 1;
			out = "…" + trimmed;
		}
		if (start + budget < sentence.length) out = out.replace(/\s\S*$/, "") + "…";
		return [out, m.index - shift];
	}

	function markWord(sentence, word, color, form, at) {
		const [cut, where] = excerpt(sentence, word, form, at);
		const rx =
			form && wordRx(word, form).test(cut) ? wordRx(word, form) : wordRx(word);
		const m = findWord(cut, rx, where);
		if (!m) return escapeHtml(cut);
		return (
			escapeHtml(cut.slice(0, m.index)) +
			`<mark style="background:${color}2e;box-shadow:inset 0 -2px 0 ${color}66;` +
			`color:inherit;padding:0 1px;">${escapeHtml(m[0])}</mark>` +
			escapeHtml(cut.slice(m.index + m[0].length))
		);
	}
	const tickValues = [10, 100, 1000, 10000];
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<div
	class="fightin-words"
	class:bare
	class:mobile
	class:big={!!source}
	bind:this={rootEl}
>
	{#if !source}
		<!-- the title, and who Fox is compared with, as on the player chart -->
		<div class="head">
			<p class="kicker">on the web</p>
			<p class="heading">
				{#if bodyMode && player === ALL}{fillIn(
						or(headingText, "How Fox News writes about the WNBA"),
						{ unit: unitName(gram) }
					)}{:else}{gram === 3
						? "Three-word phrases"
						: gram === 2
							? "Phrases"
							: "Words"} in {player === ALL
						? `WNBA ${bodyMode ? "articles" : "headlines"}`
						: `headlines naming ${player}`}{/if}
			</p>
			<!-- a div, not a p: the menu inside renders block elements -->
			<div class="subheading">
				<span>{or(comparedWith, "Compared with")}</span>
				<LogoSelect
					options={outletsHere}
					bind:value={against}
					logoOf={(o) => PILL_LOGO[o] ?? null}
					nameOf={outletOption}
					label="Compared with"
				/>
			</div>
		</div>
	{/if}
	{#if !source}
		<!-- the checks, when they're on -->
		{#if checks.on && controls}
			<div class="controls filterbar">
				<div class="field">
					<span class="field-label">Leave out</span>
					<LogoSelect
						options={["none", "game", "names", "both"]}
						bind:value={leaveOut}
						nameOf={(o) =>
							({
								none: "Nothing",
								game: "Game words",
								names: "Names",
								both: "Game words and names"
							})[o]}
						label="Leave out"
					/>
				</div>
				{#if player === ALL}
					<!-- a check: see `college` above -->
					<div class="field">
						<span class="field-label">College coverage</span>
						<LogoSelect
							options={["with", "without"]}
							bind:value={college}
							nameOf={(o) =>
								o === "with" ? "With college" : "Without college"}
							label="College coverage"
						/>
					</div>
				{/if}
			</div>
		{/if}
		{#if controls}
			<!-- the unit as tabs on a rule, the search at the rule's right end -->
			<div class="unit-row">
				{#if bodyMode}
					<div class="unit-tabs" role="tablist" aria-label="Words at a time">
						{#each [1, 2, 3].map((n) => [n, unitName(n)]) as [n, label] (n)}
							<button
								type="button"
								role="tab"
								class:on={gram === n}
								aria-selected={gram === n}
								onclick={() => (gram = n)}>{label}</button
							>
						{/each}
					</div>
				{/if}
				<div class="find">
					<input
						type="search"
						placeholder={or(search, "Find a word…")}
						aria-label="Find a word"
						bind:value={query}
						autocomplete="off"
						spellcheck="false"
						onfocus={() => (open = true)}
						onblur={() => (open = false)}
						oninput={() => ((open = true), (cursor = -1))}
						onkeydown={onKey}
					/>
					{#if open && q && suggestions.length}
						<ul class="suggest" role="listbox">
							{#each suggestions as t, i (t.term)}
								<li
									role="option"
									aria-selected={i === cursor}
									class:on={i === cursor}
									onpointerdown={(e) => (e.preventDefault(), choose(t.term))}
								>
									<span class="term">{properCase(t.term)}</span>
									{#if Math.abs(t.z) < SIGNIFICANT}
										<span class="uses even">{or(rankEven, "Even")}</span>
									{:else}
										<span class="uses" style="color:{t.z > 0 ? FOX : OTHER}"
											>{fillIn(
												t.z > 0
													? or(rankFox, "Fox #{rank}")
													: or(
															rankOthers,
															against === ALL_OUTLETS
																? "Others #{rank}"
																: `${bottomName} #{rank}`
														),
												{
													rank: rankOf.get(t.term)
												}
											)}</span
										>
									{/if}
								</li>
							{/each}
						</ul>
					{/if}
				</div>
			</div>
		{/if}
	{/if}

	<!-- the counts that sat over the chart are in its caption now (2026-10-02) -->

	{#if chart === "bars"}
		<!-- the same words as mirrored bars: the strongest on each side -->
		<WordBars
			{labels}
			{scale}
			{caps}
			{scores}
			source={barSource}
			{fill}
			note={source ? note : caption}
			noteKind={source ? "" : "source"}
			otherName={against === ALL_OUTLETS ? "others" : against}
			{topName}
			highlight={[...HIGHLIGHT]}
			top={mobile ? 10 : 14}
			more={50}
			pager={!source && controls && showPager}
			{previous}
			{next}
			{range}
			{hoverCounts}
			example={barExample}
			onhover={() => {
				if (!source) ensureExamples();
			}}
		/>
	{:else}
		<svg
			viewBox="0 0 {WIDTH} {HEIGHT}"
			role="img"
			aria-label="Weighted log-odds z-score against word frequency, Fox News versus {against}"
		>
			<!-- the band where a difference isn't distinguishable from chance -->
			<rect
				x={PAD.left}
				y={yScale(SIGNIFICANT)}
				width={WIDTH - PAD.right - PAD.left}
				height={yScale(-SIGNIFICANT) - yScale(SIGNIFICANT)}
				fill="rgba(42,21,3,0.05)"
			/>

			{#each tickValues as tick}
				{#if tick >= xScale.domain()[0] && tick <= xScale.domain()[1]}
					<line
						class="grid"
						x1={xScale(tick)}
						x2={xScale(tick)}
						y1={PAD.top}
						y2={HEIGHT - PAD.bottom}
					/>
					<text
						class="axis"
						x={xScale(tick)}
						y={HEIGHT - PAD.bottom + 16}
						text-anchor="middle"
					>
						{tick.toLocaleString()}
					</text>
				{/if}
			{/each}
			{#each yScale.ticks(7) as tick}
				<text
					class="axis"
					x={PAD.left - 8}
					y={yScale(tick) + 3.5}
					text-anchor="end">{tick}</text
				>
			{/each}

			<line
				class="axis-line"
				x1={PAD.left}
				x2={WIDTH - PAD.right}
				y1={yScale(0)}
				y2={yScale(0)}
			/>

			<text
				class="axis-name"
				x={(PAD.left + WIDTH - PAD.right) / 2}
				y={HEIGHT - 10}
				text-anchor="middle"
			>
				how often the word is used, both archives together →
			</text>
			<text
				class="axis-name"
				transform="rotate(-90)"
				x={-(HEIGHT / 2)}
				y="14"
				text-anchor="middle"
			>
				weighted log-odds z-score
			</text>
			{#if source}
				<text class="side" x={PAD.left + 6} y={PAD.top + 2} fill={FOX}>
					{source.topLabel} ↑
				</text>
				<text
					class="side"
					x={PAD.left + 6}
					y={HEIGHT - PAD.bottom - 8}
					fill={OTHER}
				>
					{source.bottomLabel} ↓
				</text>
			{:else}
				<g transform="translate({PAD.left + 6},{PAD.top + 2})">
					<image
						href="{base}/logos/fox-news.svg"
						width="20"
						height="20"
						y="-14"
					/>
					<text class="side" x="26" y="2" fill={FOX}>uses this more ↑</text>
				</g>
				<g transform="translate({PAD.left + 6},{HEIGHT - PAD.bottom - 20})">
					{#each LOGOS[against] ?? [] as logo, i}
						<image
							href="{base}/logos/{logo}"
							x={(LOGOS[against] ?? [])
								.slice(0, i)
								.reduce((sum, l) => sum + LOGO_WIDTH[l] + 8, 0)}
							y="0"
							width={LOGO_WIDTH[logo]}
							height="13"
						/>
					{/each}
					<text class="side" x="0" y="28" fill={OTHER}>use this more ↓</text>
				</g>
			{/if}

			{#each points as point (point.word)}
				<circle
					cx={xScale(point.n)}
					cy={yScale(point.z)}
					r={Math.abs(point.z) < SIGNIFICANT
						? 1.5
						: sizeScale(Math.abs(point.z))}
					fill={colorOf(point.z)}
					opacity={beating && !HIGHLIGHT.has(point.word.toLowerCase())
						? 0.16
						: hovered && hovered !== point.word
							? 0.25
							: 0.75}
					onpointerenter={(e) => showTip(e, point)}
					onpointerleave={hideTip}
					role="presentation"
				/>
				<!-- a generous invisible target, because a 2px dot is unhittable -->
				<circle
					cx={xScale(point.n)}
					cy={yScale(point.z)}
					r="7"
					fill="transparent"
					onpointerenter={(e) => showTip(e, point)}
					onpointerleave={hideTip}
					role="presentation"
				/>
			{/each}

			{#each labelled as point (point.word)}
				<text
					class="word"
					class:lit={point.lit}
					class:weak={point.weak}
					x={point.px + (point.flip ? -6 : 6)}
					y={point.py + 3.5}
					text-anchor={point.flip ? "end" : "start"}
					style:font-size="{point.size}px"
					fill={colorOf(point.z)}
					opacity={hovered && hovered !== point.word ? 0.3 : 1}
					onpointerenter={(e) => showTip(e, point)}
					onpointermove={(e) => showTip(e, point)}
					onpointerleave={hideTip}
					role="presentation"
				>
					{properCase(point.word)}
				</text>
			{/each}
		</svg>

		{#if tip}
			{@const side = tip.z > 0 ? FOX : OTHER}
			<div
				class="tip-card"
				class:flip={tip.cx > tip.boxW - 350}
				style="left:{tip.cx}px; top:{Math.min(
					Math.max(70, tip.cy),
					(tip.boxH || 500) - 70
				)}px"
			>
				<!-- the side's colour in a swatch and on the quote's rule; the words in ink -->
				<span class="tip-head">{properCase(tip.word)}</span
				>
				<!-- the split behind the dot: uses on each side, and the score -->
				<span class="tip-count"
					>{topName}
					{tip.nf.toLocaleString()} · {bottomName}
					{tip.no.toLocaleString()} · z {tip.z > 0 ? "+" : ""}{tip.z.toFixed(
						1
					)}</span
				>
				{#if cardEx?.s}
					<p style="border-left-color:{side}">
						{@html markWord(cardEx.s, tip.word, side, cardEx.w, cardEx.a)}
					</p>
					{#if cardEx.o}<span class="tip-source">{cardEx.o}</span>{/if}
				{/if}
			</div>
		{/if}
	{/if}

	<p class="note">
		Weighted log-odds ratio with an informative Dirichlet prior (Monroe,
		Colaresi &amp; Quinn 2008), using <a
			href="https://github.com/jmhessel/FightingWords"
			target="_blank"
			rel="noreferrer">Jack Hessel's implementation</a
		>, over headlines from April 2023 on. &ldquo;All outlets&rdquo; pools ESPN,
		CBS Sports, USA Today, Just Women's Sports and The Athletic, which together
		publish far more than Fox — so the horizontal axis, which counts both
		archives at once, is mostly theirs. Hover any word for the split. The shaded
		band is |z| &lt; 1.96, where the difference is not distinguishable from
		chance.
	</p>
</div>

<style>
	.fightin-words {
		max-width: 1000px;
		margin: 0 auto;
		position: relative;
	}
	.tip-card {
		position: absolute;
		z-index: 8;
		pointer-events: none;
		width: 320px;
		transform: translate(14px, -50%);
		background: var(--tip-bg);
		border: 1px solid var(--tip-border);
		border-radius: var(--tip-radius);
		padding: var(--tip-pad);
		box-shadow: var(--tip-shadow);
		color: var(--tip-ink);
	}
	.tip-card.flip {
		transform: translate(calc(-100% - 14px), -50%);
	}
	/* the shared tooltip (variables.css) */
	.tip-source {
		display: block;
		font: var(--tip-small);
		color: var(--tip-sub);
		margin-top: 4px;
	}
	.tip-card .swatch {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 2px;
		margin-right: 7px;
		vertical-align: 1px;
	}
	.tip-count {
		display: block;
		font-family: var(--font-chart);
		font-size: 11px;
		color: rgba(42, 21, 3, 0.55);
		margin-top: 2px;
	}
	.tip-head {
		display: block;
		font: var(--tip-title);
	}
	.tip-count {
		display: block;
		font: var(--tip-small);
		color: var(--tip-sub);
		margin: 3px 0 0;
	}
	.tip-weak {
		display: block;
		font-family: var(--font-chart);
		font-size: 10.5px;
		color: rgba(42, 21, 3, 0.5);
		margin-top: 2px;
	}
	.tip-card p {
		margin: 9px 0 0;
		padding: 1px 0 1px 9px;
		border-left: 3px solid var(--tip-rule);
		font: var(--tip-quote);
		color: var(--tip-ink);
	}
	.fightin-words.bare .note,
	.fightin-words .controls[hidden] {
		display: none;
	}

	/* the title in plain words, and what Fox is compared with (as on the
	   player chart) */
	.head {
		max-width: 720px;
		margin: 0 auto 10px;
	}
	.subheading {
		display: flex;
		align-items: center;
		gap: 6px;
		margin: 2px 0 0;
		font-family: var(--font-graphic);
		font-size: 15px;
		color: var(--wnba-tan-dark);
	}
	.subheading > span {
		flex: 0 0 auto;
		white-space: nowrap;
	}
	.subheading :global(.logo-select) {
		flex: 0 1 auto;
		width: auto;
		min-width: 0;
	}
	/* the menu sits in the line as a quiet underlined word */
	.subheading :global(.logo-select .current) {
		height: auto;
		padding: 0 18px 0 0;
		border: 0;
		border-bottom: 1.5px solid currentColor;
		border-radius: 0;
		background: transparent;
		font-family: var(--font-graphic);
		font-size: 15px;
		color: var(--color-ink-dark);
	}
	.subheading :global(.logo-select .current::after) {
		right: 0;
	}
	@media (max-width: 640px) {
		.heading {
			font-size: 20px;
		}
		.subheading,
		.subheading :global(.logo-select .current) {
			font-size: 14px;
		}
	}
	/* the controls in the headline table's style: labelled fields, a
	   heavy-edged white dropdown with its own caret, the same search box */
	/* # words: one rounded box split into numbers, the active one filled */
	/* the unit tabs on a rule, the search at its right end */
	.unit-row {
		display: flex;
		flex-wrap: wrap;
		align-items: flex-end;
		gap: 8px 22px;
		max-width: 720px;
		margin: 4px auto 1.5rem;
		border-bottom: 1px solid var(--color-fg);
	}
	.unit-tabs {
		display: flex;
		gap: 18px;
	}
	.unit-tabs button {
		appearance: none;
		margin: 0 0 -1px;
		padding: 0 0 8px;
		border: 0;
		border-radius: 0;
		border-bottom: 3px solid transparent;
		background: none;
		color: var(--wnba-tan-dark);
		font-family: var(--font-sans);
		font-size: 14px;
		font-weight: 700;
		cursor: pointer;
	}
	.unit-tabs button:hover {
		color: var(--color-ink-dark);
	}
	.unit-tabs button.on {
		color: var(--color-ink-dark);
		border-bottom-color: var(--color-ink-dark);
	}
	.unit-tabs button:focus-visible {
		outline: none;
		text-decoration: underline;
	}
	/* the search: a rounded field with a magnifier */
	.find {
		position: relative;
		margin-left: auto;
		padding-bottom: 6px;
	}
	.find input {
		width: 200px;
		height: 30px;
		padding: 0 10px 0 28px;
		border: 1px solid var(--wnba-tan-light);
		border-radius: 4px;
		background: var(--color-white)
			url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23727272' stroke-width='2.4' stroke-linecap='round'%3E%3Ccircle cx='11' cy='11' r='7'/%3E%3Cpath d='M20 20l-4-4'/%3E%3C/svg%3E")
			no-repeat 10px 50%;
		font-family: var(--font-sans);
		font-size: 14px;
		color: var(--color-ink-dark);
	}
	.find input:focus {
		outline: 2px solid var(--color-ink-dark);
		outline-offset: -2px;
	}
	.uses.even {
		color: rgba(42, 21, 3, 0.55);
	}
	.find .suggest {
		left: auto;
		right: 0;
		width: 260px;
	}
	@media (max-width: 640px) {
		.unit-tabs {
			gap: 14px;
		}
		.unit-tabs button {
			font-size: 13px;
		}
		.find {
			order: -1;
			flex: 1 0 100%;
			margin-left: 0;
		}
		.find input {
			width: 100%;
		}
		.find .suggest {
			left: 0;
			width: 100%;
		}
	}
	.controls.filterbar {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		align-items: flex-end;
		gap: 12px 14px;
		max-width: 720px;
		margin: 0 auto 12px;
	}
	.field {
		display: flex;
		flex-direction: column;
		gap: 5px;
	}
	.field-label {
		font-family: var(--font-sans);
		font-size: 13px;
		font-weight: 600;
		color: var(--color-ink-dark);
	}
	/* on a phone the controls shrink to the bars' scale: shorter fields,
	   smaller type, and no "Search" label over a box that says Search */
	@media (max-width: 640px) {
		.controls.filterbar {
			gap: 8px 8px;
			margin-bottom: 10px;
		}
		.field {
			flex: 1 1 calc(50% - 4px);
			gap: 3px;
		}
		.field-label {
			font-size: 11.5px;
		}
		.field :global(.logo-select),
		.field :global(.logo-select .current) {
			width: 100%;
			min-width: 0;
		}
		.field :global(.logo-select .current) {
			height: 32px;
			padding: 0 28px 0 10px;
			border-radius: 6px;
			font-size: 13px;
		}
		.field :global(.logo-select .current::after) {
			right: 10px;
		}
		.field :global(.logo-select .menu li) {
			min-height: 30px;
			font-size: 13px;
		}
	}
	/* the suggestions, as in the standalone demo: plain words in the chart's
	   sans, a quiet grey on the one under the cursor, the rank in small bold */
	.suggest {
		position: absolute;
		left: 0;
		right: 0;
		top: calc(100% + 2px);
		margin: 0;
		padding: 4px 0;
		list-style: none;
		background: #fff;
		border: 1px solid #e2e2e2;
		border-radius: 6px;
		box-shadow: 0 4px 14px rgba(0, 0, 0, 0.14);
		z-index: 6;
		overflow: hidden;
		text-align: left;
		font-family: var(--font-graphic);
	}
	.suggest li {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 10px;
		padding: 6px 12px;
		font-size: 14px;
		color: var(--color-ink-dark);
		cursor: pointer;
	}
	.suggest li:hover,
	.suggest li.on {
		background: #f4f2ee;
	}
	.suggest .uses {
		font-family: var(--font-graphic);
		font-size: 12px;
		font-weight: 700;
		white-space: nowrap;
	}
	/* a kept word */
	.kept {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		font-family: var(--font-chart);
		font-size: 12px;
		font-weight: 700;
		color: var(--color-ink);
		background: rgba(255, 253, 248, 0.85);
		border: 1px solid rgba(42, 21, 3, 0.25);
		border-radius: 999px;
		padding: 2px 6px 2px 9px;
	}
	.kept button {
		border: 0;
		background: transparent;
		color: rgba(42, 21, 3, 0.6);
		font-size: 14px;
		line-height: 1;
		padding: 0 2px;
		cursor: pointer;
	}

	svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.grid {
		stroke: rgba(42, 21, 3, 0.12);
		stroke-width: 1;
	}
	.axis-line {
		stroke: rgba(42, 21, 3, 0.45);
		stroke-width: 1;
	}
	.axis {
		font-size: 11.5px;
		fill: rgba(42, 21, 3, 0.6);
	}
	.axis-name {
		font-size: 12.5px;
		fill: rgba(42, 21, 3, 0.65);
	}
	.side {
		font-size: 13px;
		font-weight: 800;
	}
	.word {
		font-size: 18px;
		font-weight: 600;
		cursor: default;
		paint-order: stroke;
		stroke: var(--color-paper);
		stroke-width: 3px;
		stroke-linejoin: round;
	}
	.word.lit {
		font-size: 22px;
		font-weight: 800;
		stroke-width: 5.5px;
	}
	/* a word both sides use about equally: labelled, but in a lighter hand */
	.word.weak {
		font-size: 14px;
		font-weight: 500;
		opacity: 0.72;
	}
	.mobile .word.weak {
		font-size: 12.5px;
	}
	.big .word.weak {
		font-size: 17px;
	}

	.mobile .axis {
		font-size: 14px;
	}
	.mobile .axis-name {
		font-size: 14px;
	}
	.mobile .side {
		font-size: 15px;
	}
	.mobile .word {
		font-size: 15.5px;
	}
	.mobile .word.lit {
		font-size: 18.5px;
	}
	.mobile .tip-word {
		font-size: 18px;
	}

	/* declared after .mobile so it wins there */
	.big .word {
		font-size: 24px;
	}
	.big .word.lit {
		font-size: 28px;
		stroke-width: 6px;
	}
	.big .axis {
		font-size: 13px;
	}
	.big .axis-name {
		font-size: 13.5px;
	}
	.big .side {
		font-size: 17px;
	}
	.big .tip-word {
		font-size: 22px;
	}

	.tip {
		pointer-events: none;
	}
	.tip text {
		paint-order: stroke;
		stroke: var(--color-paper);
		stroke-width: 4px;
		stroke-linejoin: round;
	}
	.tip.carded text {
		paint-order: normal;
		stroke: none;
	}
	.tip-word {
		font-size: 15px;
		font-weight: 800;
	}
	.tip.carded .tip-word {
		font-family: var(--font-chart);
		font-size: 12px;
		font-weight: 700;
		fill: #fff;
	}
	.tip-line {
		font-size: 11.5px;
		font-weight: 600;
		fill: rgba(42, 21, 3, 0.75);
	}

	.controls.dimmed {
		opacity: 0.4;
		pointer-events: none;
	}

	.note {
		font-size: 12px;
		line-height: 1.5;
		color: rgba(42, 21, 3, 0.62);
		text-align: center;
		max-width: 640px;
		margin: 12px auto 0;
	}
	.note a {
		color: inherit;
	}
</style>
