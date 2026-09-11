<script>
	// Small multiples: one yearly line per outlet, with the outlet's own
	// all-years average ruled across the panel and quoted beside its logo
	import { base } from "$app/paths";
	import rows from "$data/outlet_topics.csv";
	import { flip } from "svelte/animate";
	import { fade } from "svelte/transition";
	// the vocabulary behind each topic, straight from the notebooks' term list
	import termRows from "../../data/topic_terms.csv";

	// `dots` is a leftover Doc prop from the logo dot plot this replaced
	// full text only; `method: headline` from the Doc would switch the source
	// second: another topic drawn on the same panels (e.g. lgbtq beside polrace)
	// wordsLabel / wordsNote: the "see the words" toggle and the line under the
	// list, editable from the Doc
	let {
		topic = "polrace",
		method = "body",
		dots = null,
		second = null,
		// reveal: "pair" — open with Fox beside ESPN alone and, once the chart
		// has been on screen a moment, let ESPN glide down into the grid as the
		// other outlets fade in. Anything else: every panel from the start.
		reveal = "",
		// top: "espn" — Fox and ESPN share a large top row, the rest sit below;
		// otherwise Fox sits alone on top
		top = "",
		// below: with top: espn, how the rest sit — "3-2" (three, then two
		// centred) or "row" (all five small on one line)
		below = "3-2",
		// layout: "rows" (every outlet the same size, Fox first, rows of
		// three, a short last row centred) or "solo" (Fox alone on top, a
		// third wide)
		layout = "rows",
		// from: the first year shown (e.g. 2024), when a topic only matters lately
		from = "",
		wordsLabel = "See the words included",
		wordsNote = "An article counts when its headline or text contains any of these words or phrases."
	} = $props();

	const data = { topics: {} };
	for (const r of rows) {
		const byMethod = (data.topics[r.topic] ??= {});
		const byOutlet = (byMethod[r.method] ??= {});
		(byOutlet[r.outlet] ??= {})[r.year] = { n: +r.articles, hit: +r.hits };
	}

	const FOX = "Fox News";
	const NBA = "Fox News (NBA)";
	const TOPIC_PHRASE =
		topic === "lgbtq"
			? "mention LGBTQ topics"
			: topic === "fouls"
				? "describe fouls and physical contact"
				: "mention race or protest politics";
	const COLOR_OF = {
		lgbtq: "var(--color-lgbtq)",
		polrace: "var(--color-politics)",
		fouls: "#7a4a00"
	};
	const PHRASE_OF = {
		lgbtq: "LGBTQ+ topics",
		polrace: "race or protest politics",
		fouls: "fouls and physical contact"
	};
	const MAIN = COLOR_OF[topic] ?? "var(--color-politics)";
	const SECOND = second ? COLOR_OF[second] : null;
	const MIN_N = 10;
	const AVG = "#1a1a1a"; // the average rule, apart from either topic colour

	// --- the words counted, for the "see words included" drop-down ------------
	// the same unions as notebooks/topics.py
	// each entry is one list in the drop-down: a label and the term groups it pools
	const TOPIC_GROUPS = {
		polrace: [
			["Race", ["race / racism"]],
			["Politics and protest", ["politics / protest"]]
		],
		lgbtq: [["LGBTQ+", ["LGBTQ / sexuality", "transgender / trans"]]],
		fouls: [["Fouls and contact", ["fouls"]]]
	};
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
		"lgbtq?\\b": "LGBT / LGBTQ",
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
			.replace(/\\b/g, "")
			.replace(/\(\?:([^)]+)\)/g, (_, alts) => alts.split("|").join(" / "))
			.replace(/\[ae\]/g, "a")
			.replace(/\\/g, "");
	const wordGroups = [
		...(TOPIC_GROUPS[topic] ?? []),
		...(second ? (TOPIC_GROUPS[second] ?? []) : [])
	].map(([label, groups]) => ({
		label,
		// a term listed in more than one of the pooled groups shows once
		words: [
			...new Set(
				termRows.filter((r) => groups.includes(r.topic)).map((r) => readable(r.term))
			)
		]
	}));
	let wordsOpen = $state(false);

	// the outlets with panels (shown most-to-least by their all-years average)
	// (Fox's NBA coverage is in the data but not in the panels)
	const ORDER = [
		FOX,
		"ESPN",
		// Yahoo's pool is ~96% syndicated wire copy; left out of the panels
		"Just Women's Sports",
		"The Athletic",
		"CBS Sports",
		"USA Today"
	];
	const LOGOS = {
		"Fox News": { file: "fox-news.svg", h: 20 },
		"Fox News (NBA)": { file: "fox-news.svg", h: 20 },
		"Yahoo Sports (syndicated pool)": { file: "yahoo.svg", h: 16 },
		ESPN: { file: "espn.svg", h: 15 },
		"Just Women's Sports": { file: "jws.png", h: 22 },
		"The Athletic": { file: "the-athletic.png", h: 22 },
		"CBS Sports": { file: "cbs-sports.svg", h: 15 },
		"USA Today": { file: "usa-today.svg", h: 15 }
	};
	const SHORT_NAME = {
		"Yahoo Sports (syndicated pool)": "Yahoo (pool)",
		"Just Women's Sports": "JWS",
		"Fox News (NBA)": "Fox (NBA)"
	};
	const LEAGUE_TAG = { "Fox News": "WNBA", "Fox News (NBA)": "NBA" };

	let byOutlet = $derived(data.topics[topic][method]);
	let byOutlet2 = $derived(second ? data.topics[second]?.[method] : null);
	// the second topic's line and average, from the same years
	function lineFor2(outlet) {
		if (!byOutlet2) return [];
		const pts = years
			.map((year, index) => ({ year, index, v: byOutlet2[outlet]?.[year] }))
			.filter(({ v }) => v && v.n >= MIN_N)
			.map((p) => ({ ...p, share: p.v.hit / p.v.n }));
		return pts;
	}
	function overall2(outlet) {
		if (!byOutlet2) return null;
		let n = 0,
			hit = 0;
		for (const v of Object.values(byOutlet2[outlet] ?? {})) {
			if (v.n < MIN_N) continue;
			n += v.n;
			hit += v.hit;
		}
		return n ? { n, hit, share: hit / n } : null;
	}
	// the reference: the outlet's share pooled over every year with enough articles
	function overall(outlet) {
		let n = 0,
			hit = 0;
		for (const v of Object.values(byOutlet[outlet] ?? {})) {
			if (v.n < MIN_N) continue;
			n += v.n;
			hit += v.hit;
		}
		return n ? { n, hit, share: hit / n } : null;
	}
	// The Athletic is headline-only, so it has no full-text panel; the rest are
	// ordered most-to-least by their average
	let outlets = $derived(
		ORDER.filter((o) => overall(o)).toSorted(
			(a, b) => overall(b).share - overall(a).share
		)
	);

	// the pair stage shows Fox and ESPN only; the reveal opens on it and
	// expands once the block has been in view for a beat
	let stage = $state(reveal === "pair" ? "pair" : "all");
	let root = $state(null);
	$effect(() => {
		if (!root || stage !== "pair") return;
		if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
			stage = "all";
			return;
		}
		let timer;
		const io = new IntersectionObserver(
			(entries) => {
				if (!entries.some((e) => e.isIntersecting)) return;
				io.disconnect();
				timer = setTimeout(() => (stage = "all"), 1400);
			},
			{ threshold: 0.5 }
		);
		io.observe(root);
		return () => {
			io.disconnect();
			clearTimeout(timer);
		};
	});
	let shown = $derived(
		stage === "pair" ? outlets.filter((o) => o === FOX || o === "ESPN") : outlets
	);

	let years = $derived(
		[
			...new Set(
				outlets.flatMap((o) =>
					Object.entries(byOutlet[o])
						.filter(([, v]) => v.n >= MIN_N)
						.map(([y]) => y)
				)
			)
		]
			.filter((y) => !String(from).trim() || y >= String(from).trim())
			.sort()
	);

	function lineFor(outlet) {
		return years
			.map((year, index) => ({ year, index, v: byOutlet[outlet]?.[year] }))
			.filter(({ v }) => v && v.n >= MIN_N)
			.map((p) => ({ ...p, share: p.v.hit / p.v.n }));
	}

	const pct = (share) => `${(share * 100).toFixed(share < 0.02 ? 1 : 0)}%`;

	// one y scale for every panel, so the lines are comparable at a glance
	let yTop = $derived.by(() => {
		let peak = 0;
		for (const outlet of outlets)
			for (const p of [...lineFor(outlet), ...lineFor2(outlet)])
				peak = Math.max(peak, p.share);
		// tops whose halves are round numbers, since the ticks sit at ½ and 1
		for (const nice of [0.02, 0.04, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1])
			if (nice >= peak * 1.05) return nice;
		return 1;
	});

	let viewportWidth = $state(
		typeof window === "undefined" ? 1200 : window.innerWidth
	);
	let mobile = $derived(viewportWidth < 640);
	// the comparison panes in grid order, and the grid's column count
	let others = $derived(outlets.filter((o) => o !== FOX));
	let cols = $derived(mobile ? 2 : 3);
	let topPair = $derived(
		["espn", "pair"].includes(String(top).toLowerCase()) || stage === "pair"
	);

	// Where every pane sits: a six-column grid on desktop (two columns on
	// phones). Fox alone on top spans the row and is drawn a third wide; with
	// top: espn, Fox and ESPN each take half the top row; the rest run in
	// rows of three (two on phones). From these, which panes carry axis labels.
	let cells = $derived.by(() => {
		const units = mobile ? 2 : 30;
		const out = [];
		let row = 0, col = 0;
		const place = (outlet, span, solo = false) => {
			if (col + span > units) {
				row += 1;
				col = 0;
			}
			out.push({ outlet, row, start: col, span, solo });
			col += span;
		};
		const list = [...shown];
		if (topPair) {
			for (const o of [FOX, "ESPN"]) {
				const i = list.indexOf(o);
				if (i >= 0) {
					list.splice(i, 1);
					place(o, mobile ? 1 : 15);
				}
			}
		} else if (list.includes(FOX) && String(layout) !== "rows") {
			list.splice(list.indexOf(FOX), 1);
			place(FOX, units, true);
		}
		row += col ? 1 : 0;
		col = 0;
		if (topPair && !mobile && String(below) === "row") {
			// all of the rest small, on one line
			const span = Math.floor(units / Math.max(1, list.length));
			const start0 = Math.floor((units - span * list.length) / 2);
			list.forEach((o, k) =>
				out.push({ outlet: o, row, start: start0 + span * k, span, solo: false })
			);
		} else if ((topPair || String(layout) === "rows") && !mobile) {
			// rows of three, the last row centred when it is short
			let i = 0;
			while (i < list.length) {
				const take = Math.min(3, list.length - i);
				const start = (3 - take) * 5; // a short row is centred
				for (let k = 0; k < take; k++)
					out.push({ outlet: list[i + k], row, start: start + 10 * k, span: 10, solo: false });
				i += take;
				row += 1;
			}
		} else {
			for (const o of list) place(o, mobile ? 1 : 10);
		}
		// every pane carries both axes' labels
		return out.map((c) => ({ ...c, showY: true, showX: true }));
	});

	const W = 220,
		H = 150;
	const M = { left: 34, right: 8, top: 10, bottom: 22 };
	const plotW = W - M.left - M.right;
	const plotH = H - M.top - M.bottom;
	let colW = $derived(plotW / Math.max(1, years.length));
	let pctY = $derived((pct) => M.top + plotH * (1 - pct / yTop));
	let xMid = $derived((index) => M.left + (index + 0.5) * colW);
	let yTicks = $derived([0.5, 1].map((f) => f * yTop));
	// fainter lines halfway between the labelled ones
	let yMinor = $derived([0.25, 0.75].map((f) => f * yTop));

	const pathFor = (pts) =>
		pts
			.map(
				(p, i) =>
					`${i ? "L" : "M"}${xMid(p.index).toFixed(1)},${pctY(p.share).toFixed(1)}`
			)
			.join("");
	// the same line closed down to the baseline, for the fill beneath it
	let areaFor = $derived((pts) => {
		if (!pts.length) return "";
		const base = (M.top + plotH).toFixed(1);
		const first = xMid(pts[0].index).toFixed(1);
		const last = xMid(pts[pts.length - 1].index).toFixed(1);
		return `M${first},${base}L` + pathFor(pts).slice(1) + `L${last},${base}Z`;
	});

	let tip = $state(null);
	function showTip(event, outlet, year, v) {
		const box = event.currentTarget.closest(".otc").getBoundingClientRect();
		tip = {
			outlet,
			year,
			...v,
			x: event.clientX - box.left,
			y: Math.min(Math.max(60, event.clientY - box.top), box.height - 60),
			flip: event.clientX - box.left > box.width - 250
		};
	}
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<div class="otc" class:mobile bind:this={root}>
	<div class="grid" class:pair={stage === "pair"}>
		{#each cells as cell, index (cell.outlet)}
			{@const outlet = cell.outlet}
			{@const pts = lineFor(outlet)}
			{@const avg = overall(outlet)}
			{@const pts2 = lineFor2(outlet)}
			{@const avg2 = overall2(outlet)}
			<!-- the panes share their axes: the years only where nothing sits
			     below, the percentages only down the left column -->
			{@const showY = cell.showY}
			{@const showX = cell.showX}
			<div
				class="pane"
				class:fox={outlet === FOX}
				class:solo={cell.solo}
				style:grid-column="{cell.start + 1} / span {cell.span}"
				animate:flip={{ duration: 800 }}
				in:fade={{ duration: 500 }}
			>
				<div class="pane-hed">
					<img
						src="{base}/logos/{LOGOS[outlet].file}"
						alt={SHORT_NAME[outlet] ?? outlet}
						style:height="{LOGOS[outlet].h}px"
						style:filter={outlet === NBA ? "grayscale(1) opacity(0.75)" : ""}
					/>
					{#if LEAGUE_TAG[outlet]}
						<span class="league-tag">{LEAGUE_TAG[outlet]}</span>
					{/if}
					{#if avg}
						<span class="avg-chip" style="color:{second ? MAIN : AVG}"
							>avg {pct(avg.share)}</span
						>
					{/if}
					{#if second && avg2}
						<span class="avg-chip" style="color:{SECOND}"
							>avg {pct(avg2.share)}</span
						>
					{/if}
				</div>
				<svg
					viewBox="0 0 {W} {H}"
					role="img"
					aria-label="Share of {outlet} WNBA articles that {TOPIC_PHRASE}, by year"
				>
					{#each yTicks as pct}
						<line
							class="grid-line"
							x1={M.left}
							x2={W - M.right}
							y1={pctY(pct)}
							y2={pctY(pct)}
						/>
						{#if showY}
							<text
								class="tick"
								x={M.left - 5}
								y={pctY(pct) + 4}
								text-anchor="end">{Math.round(pct * 100)}%</text
							>
						{/if}
					{/each}
					{#each yMinor as pct}
						<line
							class="grid-line minor"
							x1={M.left}
							x2={W - M.right}
							y1={pctY(pct)}
							y2={pctY(pct)}
						/>
					{/each}
					<line
						class="axis"
						x1={M.left}
						x2={W - M.right}
						y1={M.top + plotH}
						y2={M.top + plotH}
					/>
					<!-- a tick for every year, in every pane; the labels only where shown -->
					{#each years as year, index}
						<line
							class="axis-tick"
							x1={xMid(index)}
							x2={xMid(index)}
							y1={M.top + plotH}
							y2={M.top + plotH + (+year % 2 === 0 ? 4 : 2.5)}
						/>
					{/each}
					{#each years as year, index}
						{#if showX && +year % 2 === 0}
							<text
								class="tick year"
								x={xMid(index)}
								y={H - 6}
								text-anchor="middle">{year}</text
							>
						{/if}
					{/each}

					{#if avg}
						<line
							class="avg-line"
							x1={M.left}
							x2={W - M.right}
							y1={pctY(avg.share)}
							y2={pctY(avg.share)}
							stroke={second ? MAIN : AVG}
						/>
					{/if}
					{#if second && avg2}
						<line
							class="avg-line"
							x1={M.left}
							x2={W - M.right}
							y1={pctY(avg2.share)}
							y2={pctY(avg2.share)}
							stroke={SECOND}
						/>
					{/if}
					<g>
						{#if second && pts2.length}
							<path class="topic-area" d={areaFor(pts2)} fill={SECOND} />
							<path class="topic-line" d={pathFor(pts2)} stroke={SECOND} />
							{#each pts2 as p (p.year)}
								<circle
									cx={xMid(p.index)}
									cy={pctY(p.share)}
									r="3"
									fill={SECOND}
								/>
							{/each}
						{/if}
						<path class="topic-area" d={areaFor(pts)} fill={MAIN} />
						<path class="topic-line" d={pathFor(pts)} stroke={MAIN} />
						{#each pts as p (p.year)}
							<circle cx={xMid(p.index)} cy={pctY(p.share)} r="3" fill={MAIN} />
						{/each}
					</g>
					{#each pts as p (p.year)}
						<rect
							x={M.left + p.index * colW}
							width={colW}
							y={M.top}
							height={plotH}
							fill="transparent"
							onpointermove={(e) => showTip(e, outlet, p.year, p.v)}
							onpointerleave={() => (tip = null)}
						/>
					{/each}
				</svg>
			</div>
		{/each}
	</div>

	<!-- the vocabulary, folded away under the panels -->
	{#if wordGroups.length}
		<div class="words">
			<button
				class="reveal"
				onclick={() => (wordsOpen = !wordsOpen)}
				aria-expanded={wordsOpen}
			>
				{wordsOpen ? wordsLabel.replace(/^See/i, "Hide") : wordsLabel}
				<span class="caret">{wordsOpen ? "▴" : "▾"}</span>
			</button>
			{#if wordsOpen}
				<div class="word-list">
					{#each wordGroups as group (group.label)}
						<p><b>{group.label}:</b> {group.words.join(", ")}</p>
					{/each}
					{#if wordsNote}<p class="how">{@html wordsNote}</p>{/if}
				</div>
			{/if}
		</div>
	{/if}

	{#if tip}
		{@const avg = overall(tip.outlet)}
		<div
			class="tooltip"
			class:flip={tip.flip}
			style="left:{tip.x}px; top:{tip.y}px"
		>
			<strong>{SHORT_NAME[tip.outlet] ?? tip.outlet} · {tip.year}</strong>
			<p class="line">
				{tip.hit} of {tip.n.toLocaleString()}
				{method === "headline" ? "headlines" : "articles"} —
				{((tip.hit / tip.n) * 100).toFixed(tip.hit / tip.n < 0.02 ? 1 : 0)}% —
				{TOPIC_PHRASE}.
				{#if avg}
					Its average over all years: {pct(avg.share)}.
				{/if}
			</p>
		</div>
	{/if}
</div>

<style>
	.words {
		max-width: 640px;
		margin: 14px auto 0;
	}
	/* a quiet text link on the page colour, not a box */
	.reveal {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		margin: 0 auto;
		padding: 4px 6px;
		border: 0;
		background: transparent;
		font: inherit;
		font-size: 12.5px;
		font-weight: 600;
		color: rgba(42, 21, 3, 0.6);
		cursor: pointer;
	}
	.reveal:hover {
		color: var(--color-ink);
	}
	.words {
		text-align: center;
	}
	.word-list {
		text-align: left;
	}
	.word-list {
		padding: 10px 14px 4px;
		font-size: 13px;
		line-height: 1.55;
		color: var(--color-ink);
	}
	.word-list p {
		margin: 0 0 8px;
	}
	.word-list .how {
		color: rgba(42, 21, 3, 0.62);
		font-size: 12px;
	}
	.otc {
		position: relative;
		max-width: 880px;
		margin: 6px auto 4px;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(30, minmax(0, 1fr));
		gap: 16px 22px;
	}
	.mobile .grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 12px 10px;
	}
	.pane {
		min-width: 0;
	}
	/* Fox on its own row at the top, centred, the size of one column; the
	   six comparison outlets in two rows of three beneath */
	/* Fox alone on top: the row is its own, and it is drawn a third wide, centred */
	.pane.solo {
		width: calc((100% - 44px) / 3);
		margin: 0 auto 6px;
	}
	/* the pair stage of the reveal: just Fox and ESPN, side by side, larger */
	.grid.pair {
		max-width: 760px;
		margin: 0 auto;
	}
	.mobile .pane.solo {
		width: calc((100% - 10px) / 2);
		margin-bottom: 2px;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
		overflow: visible;
	}

	.pane-hed {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		height: 26px;
		margin-bottom: 2px;
	}
	.league-tag {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 10.5px;
		font-weight: 800;
		color: var(--color-ink);
	}

	.grid-line {
		stroke: rgba(42, 21, 3, 0.1);
		stroke-width: 1;
	}
	.grid-line.minor {
		stroke: rgba(42, 21, 3, 0.055);
	}
	.axis {
		stroke: var(--color-ink);
		stroke-width: 1.2;
	}
	.axis-tick {
		stroke: var(--color-ink);
		stroke-width: 1;
		opacity: 0.7;
	}
	.tick {
		font-size: 11px;
		fill: rgba(42, 21, 3, 0.75);
	}
	.mobile .tick {
		font-size: 12px;
	}
	.topic-line {
		fill: none;
		stroke-width: 2.4;
		stroke-linejoin: round;
		stroke-linecap: round;
	}
	/* the area under the line, a tint of its colour */
	.topic-area {
		opacity: 0.22;
	}
	.avg-line {
		stroke-width: 2.4;
		stroke-linecap: round;
		stroke-dasharray: 1 5;
	}
	.avg-chip {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.02em;
		margin-left: 4px;
		font-variant-numeric: tabular-nums;
	}

	.tooltip {
		position: absolute;
		transform: translate(14px, -50%);
		width: 240px;
		background: var(--color-paper);
		border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid rgba(42, 21, 3, 0.35);
		border-radius: 3px;
		padding: 9px 12px 10px;
		box-shadow: 0 5px 20px rgba(42, 21, 3, 0.16);
		pointer-events: none;
		z-index: 5;
	}
	.tooltip.flip {
		transform: translate(calc(-100% - 14px), -50%);
	}
	.tooltip strong {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: rgba(42, 21, 3, 0.6);
	}
	.tooltip .line {
		margin: 5px 0 0;
		font-size: 13px;
		line-height: 1.5;
		color: var(--color-ink);
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
	}
</style>
