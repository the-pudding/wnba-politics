<script>
	// Small multiples
	import { base } from "$app/paths";
	import rows from "$data/outlet_topics.csv";
	// the same counts by month (notebooks/outlet_topics_monthly.py), for a zoomed span
	import monthRows from "$data/outlet_topics_monthly.csv";
	import { flip } from "svelte/animate";
	import { fade } from "svelte/transition";
	// the vocabulary behind each topic, straight from the notebooks' term list
	import termRows from "../../data/topic_terms.csv";


	let {
		topic = "polrace",
		method = "body",
		dots = null,
		second = null,
		// every outlet the same size, Fox first, in rows of three (two on phones),
		// a short last row centred. Other arrangements tried along the way are in
		// archive/components/OutletTopicCompare.full.svelte.
		// from / to: the first and last period shown (a year, or YYYY-MM by month)
		from = "",
		to = "",
		// by: "year" (the default) or "month" — months for a short span such as
		// the foul words of 2024-2026
		by = "year",
		// average: draw each outlet's pooled-share rule; area: fill under the line
		average = true,
		area = true,
		// stack: draw the second topic on top of the first (as the word chart
		// stacks "protect" on the foul words); mark: a dated dashed rule, e.g. 2026-07-07
		stack = false,
		mark = "",
		// markLabel: what the dashed rule is, shown on hover ("Republicans' letter to the WNBA")
		markLabel = "",
		// measure: what the panes open on, "share" or "count"
		measure: startMeasure = "share",
		// chips: the per-pane numbers beside the wordmark (false hides them)
		chips = true,
		wordsLabel = "See words included",
		wordsNote = "An article counts when its headline or text contains any of these words or phrases."
	} = $props();

	const monthly = String(by).trim().toLowerCase() === "month";
	const data = { topics: {} };
	for (const r of monthly ? monthRows : rows) {
		const byMethod = (data.topics[r.topic] ??= {});
		const byOutlet = (byMethod[r.method] ??= {});
		(byOutlet[r.outlet] ??= {})[monthly ? r.period : r.year] = { n: +r.articles, hit: +r.hits };
	}
	// the span: a year ("2024") or a month ("2024-05"); the CMS turns a bare
	// year into "2024-01", so a yearly chart keeps just the year
	const spanKey = (v) => (!v ? "" : monthly ? String(v).trim().slice(0, 7) : String(v).trim().slice(0, 4));
	const FROM = spanKey(from), TO = spanKey(to);
	const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
	const periodLabel = (p) => (monthly ? `${MONTHS[+p.slice(5, 7) - 1]} ${p.slice(0, 4)}` : p);

	const FOX = "Fox News";
	const NBA = "Fox News (NBA)";
	const TOPIC_PHRASE =
		topic === "lgbtq"
			? "mention LGBTQ topics"
			: topic === "fouls"
				? "use the letter's foul words"
				: "mention race";
	const COLOR_OF = {
		lgbtq: "var(--color-lgbtq)",
		polrace: "var(--color-politics)",
		fouls: "var(--color-brown)",        // as on the word chart: the foul words in brown,
		protect: "color-mix(in srgb, var(--color-fox-navy) 72%, white)"    // "protect" in a lighter navy
	};
	const PHRASE_OF = {
		lgbtq: "LGBTQ+ topics",
		polrace: "race",
		fouls: "the letter's foul words",
		protect: "“protect”"
	};
	const showAvg = average !== false && String(average).toLowerCase() !== "false";

	// stack: true — the second topic on top of the first (articles with both are
	// counted twice); "parts" — three bands, first only / both / second only, so
	// the top edge is exactly the articles with either; false — overlapping areas
	const STACK = String(stack).trim().toLowerCase();
	const parts = STACK === "parts" || STACK === "split";
	const stacked = stack === true || STACK === "true" || parts;
	const showChips = chips !== false && String(chips).toLowerCase() !== "false";
	const MARK = spanKey(mark);
	const markDate = (() => {
		const m = String(mark).trim().match(/^(\d{4})-(\d{2})(?:-(\d{2}))?/);
		if (!m) return String(mark).trim();
		const d = new Date(+m[1], +m[2] - 1, +(m[3] ?? 1));
		return d.toLocaleDateString("en-US", m[3] ? { month: "long", day: "numeric", year: "numeric" } : { month: "long", year: "numeric" });
	})();
	// the piece's one dated rule is the Republicans' letter; a Doc can say otherwise with markLabel
	const MARK_TEXT = String(markLabel).trim() || (String(mark).trim() === "2026-07-07" ? "Republican lawmakers' letter to the WNBA" : "");
	function showMarkTip(event, outlet) {
		const box = event.currentTarget.closest(".otc").getBoundingClientRect();
		tip = { outlet, mark: true, x: event.clientX - box.left,
			y: Math.min(Math.max(60, event.clientY - box.top), box.height - 60), flip: event.clientX - box.left > box.width - 250 };
	}
	const showArea = area !== false && String(area).toLowerCase() !== "false";
	const MAIN = COLOR_OF[topic] ?? "var(--color-politics)";
	const SECOND = second ? COLOR_OF[second] : null;
	const BOTH = second ? `color-mix(in srgb, ${MAIN} 50%, ${SECOND})` : null;
	// the chips' shorthand for each topic, and the legend's words
	const SHORTHAND = { polrace: "race", lgbtq: "LGBTQ+", fouls: "foul words", protect: "protect" };
	// the legend names the pinned topics' words outright
	const LEGEND_OF = { fouls: "hip-check, poke, punch, throat", protect: "protect" };
	const legend = [[topic, MAIN], ...(second ? [[second, SECOND]] : [])].map(([t, color]) => ({
		label: LEGEND_OF[t] ?? PHRASE_OF[t] ?? t, color
	}));
	if (second && ["parts", "split"].includes(String(stack).trim().toLowerCase()))
		legend.splice(1, 0, { label: "both", color: `color-mix(in srgb, ${MAIN} 50%, ${SECOND})` });
	const MIN_N = monthly ? 8 : 20;   // a period with fewer articles than this is not drawn: a share of 6 articles is noise
	const AVG = "var(--color-ink-dark)"; // the average rule, apart from either topic colour

	// --- the words counted, for the "see words included" drop-down ------------
	// the same unions as notebooks/topics.py
	// each entry is one list in the drop-down: a label and the term groups it pools
	const TOPIC_GROUPS = {
		polrace: [["Race", ["race / racism"]]],
		lgbtq: [["LGBTQ+", ["LGBTQ / sexuality", "transgender / trans"]]],
		fouls: [["The letter's foul words", ["fouls"]]],
		protect: [["“Protect”", ["protect"]]]
	};
	// the fouls topic is pinned in notebooks/topics.py (the sheet's rows are
	// not used), so its drop-down lists those words directly
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
		words: groups.length === 1 && PINNED_WORDS[groups[0]]
			? PINNED_WORDS[groups[0]]
			: [...new Set(termRows.filter((r) => groups.includes(r.topic)).map((r) => readable(r.term)))]
	}));
	let wordsOpen = $state(false);

	// the outlets with panels (shown most-to-least by their all-years average)
	// (Fox's NBA coverage is in the data but not in the panels)
	import { COMPARISON, LOGO, SHORT } from "$utils/outlets.js";
	// Fox first, then the sports outlets, then the news arms (Yahoo's pool,
	// ~96% syndicated wire copy, and Fox's NBA coverage stay out of the panels)
	const ORDER = [FOX, ...COMPARISON];
	const LOGOS = {
		"Fox News (NBA)": { file: "fox-news.svg", h: 20 },
		"Yahoo Sports (syndicated pool)": { file: "yahoo.svg", h: 16 },
		...Object.fromEntries(Object.entries(LOGO).map(([o, f]) => [o, { file: f, h: f.endsWith(".png") ? 22 : o === FOX ? 20 : 15 }]))
	};
	const SHORT_NAME = {
		...SHORT,
		"Yahoo Sports (syndicated pool)": "Yahoo (pool)",
		"Fox News (NBA)": "Fox (NBA)"
	};
	// the NBA pane is gone, so Fox's pane no longer needs a "WNBA" tag to tell them apart
	const LEAGUE_TAG = { "Fox News (NBA)": "NBA" };

	// measure: "share" (the topic's share of the outlet's WNBA articles) or
	// "count" (how many articles); a toggle above the panes
	let measure = $state(String(startMeasure).trim().toLowerCase() === "count" ? "count" : "share");
	const yOf = (v) => (measure === "share" ? v.hit / v.n : v.hit);
	let byOutlet = $derived(data.topics[topic][method]);
	let byOutlet2 = $derived(second ? data.topics[second]?.[method] : null);
	// the overlap, when the data carries it ("fouls&protect")
	let byBoth = $derived(second ? data.topics[`${topic}&${second}`]?.[method] : null);
	// the second topic's line and average, from the same years
	function lineFor2(outlet) {
		if (!byOutlet2) return [];
		const pts = years
			.map((year, index) => ({ year, index, v: byOutlet2[outlet]?.[year] }))
			.filter(({ v }) => v && v.n >= MIN_N)
			.map((p) => ({ ...p, share: p.v.hit / p.v.n, y: yOf(p.v) }));
		if (!stacked) return pts;
		// stacked: the second topic sits on the first, so its y is the sum; in
		// parts mode the overlap is taken out of the second band, so the top
		// edge is the union
		const base = Object.fromEntries(lineFor(outlet).map((p) => [p.year, p.y]));
		return pts.map((p) => {
			const both = parts ? bothY(outlet, p.year) : 0;
			return { ...p, y0: base[p.year] ?? 0, y: (base[p.year] ?? 0) + p.y - both };
		});
	}
	// articles with both topics, as a y value in the current measure
	function bothY(outlet, year) {
		const v = byBoth?.[outlet]?.[year];
		return v ? yOf(v) : 0;
	}
	// parts mode: the band of articles with both, sitting on the first topic's
	// "only" part (first-only = first − both)
	function bothBand(outlet) {
		if (!parts || !byBoth) return [];
		return lineFor(outlet).map((p) => {
			const both = bothY(outlet, p.year);
			return { ...p, y0: p.y - both, y: p.y };
		});
	}
	// the stacked band between the first series and the top of the second
	const bandFor = (pts) => {
		if (!pts.length) return "";
		const top = pathFor(pts);
		const bottom = [...pts].reverse().map((p) => `L${xMid(p.index).toFixed(1)},${pctY(p.y0 ?? 0).toFixed(1)}`).join("");
		return top + bottom + "Z";
	};
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
	// ordered most-to-least by average share, or by the number of articles
	// when the toggle shows counts
	let outlets = $derived(
		ORDER.filter((o) => overall(o)).toSorted((a, b) =>
			measure === "share"
				? overall(b).share - overall(a).share
				: overall(b).hit - overall(a).hit
		)
	);

	let root = $state(null);
	let shown = $derived(outlets);

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
			.filter((y) => (!FROM || y >= FROM) && (!TO || y <= TO))
			.sort()
	);

	function lineFor(outlet) {
		return years
			.map((year, index) => ({ year, index, v: byOutlet[outlet]?.[year] }))
			.filter(({ v }) => v && v.n >= MIN_N)
			.map((p) => ({ ...p, share: p.v.hit / p.v.n, y: yOf(p.v) }));
	}
	// in count mode the chip carries the outlet's total over the drawn years
	const totalHits = (pts) => pts.reduce((sum, p) => sum + p.v.hit, 0);

	const pct = (share) => `${(share * 100).toFixed(share < 0.02 ? 1 : 0)}%`;

	// one y scale for every panel, so the lines are comparable at a glance
	let yTop = $derived.by(() => {
		let peak = 0;
		for (const outlet of outlets)
			for (const p of [...lineFor(outlet), ...lineFor2(outlet)])
				peak = Math.max(peak, p.y);
		// tops whose halves are round numbers, since the ticks sit at ½ and 1
		const nices = measure === "share"
			? [0.02, 0.04, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1]
			: [10, 20, 40, 60, 80, 100, 120, 150, 200, 300, 400, 600, 800, 1000, 1500, 2000, 3000];
		for (const nice of nices)
			if (nice >= peak * 1.05) return nice;
		return nices[nices.length - 1];
	});

	let viewportWidth = $state(
		typeof window === "undefined" ? 1200 : window.innerWidth
	);
	let mobile = $derived(viewportWidth < 640);
	// the comparison panes in grid order, and the grid's column count
	let others = $derived(outlets.filter((o) => o !== FOX));
	let cols = $derived(mobile ? 2 : 3);

	// Where every pane sits: rows of three on desktop, the last row centred
	// when it is short; two columns on phones. Every pane carries both axes'
	// labels.
	let cells = $derived.by(() => {
		const out = [];
		const list = [...shown];
		if (mobile) {
			list.forEach((o, k) => out.push({ outlet: o, row: Math.floor(k / 2), start: k % 2, span: 1 }));
		} else {
			let i = 0, row = 0;
			while (i < list.length) {
				const take = Math.min(3, list.length - i);
				const start = (3 - take) * 5;
				for (let k = 0; k < take; k++)
					out.push({ outlet: list[i + k], row, start: start + 10 * k, span: 10 });
				i += take;
				row += 1;
			}
		}
		return out.map((c) => ({ ...c, showY: true, showX: true }));
	});

	const W = 220,
		H = 150;
	const M = { left: 34, right: 8, top: 10, bottom: monthly ? 32 : 22 };
	// month mode: "Jan" / "Jul" on one row, the year on a row beneath at each
	// January (and under the first column when the span starts mid-year)
	const monthLabel = (period, index) => (period.endsWith("-01") ? "Jan" : period.endsWith("-07") ? "Jul" : "");
	const yearLabel = (period, index, all) => {
		if (period.endsWith("-01")) return period.slice(0, 4);
		if (index === 0) {
			const nextJan = all.findIndex((p) => p.endsWith("-01"));
			return nextJan < 0 || nextJan >= 4 ? period.slice(0, 4) : "";
		}
		return "";
	};
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
					`${i ? "L" : "M"}${xMid(p.index).toFixed(1)},${pctY(p.y).toFixed(1)}`
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
	function showTip(event, outlet, year, v, v2 = null) {
		const box = event.currentTarget.closest(".otc").getBoundingClientRect();
		tip = {
			outlet,
			year,
			...v,
			second: v2,
			x: event.clientX - box.left,
			y: Math.min(Math.max(60, event.clientY - box.top), box.height - 60),
			flip: event.clientX - box.left > box.width - 250
		};
	}
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<div class="otc" class:mobile bind:this={root}>
	<div class="top">
		<div class="measure-toggle" role="group" aria-label="What the panes show">
			<button class:active={measure === "share"} onclick={() => (measure = "share")} title="Share of articles" aria-label="Share of articles">%</button>
			<button class:active={measure === "count"} onclick={() => (measure = "count")} title="Number of articles" aria-label="Number of articles">#</button>
		</div>
		<!-- the colours, once, top right -->
		<div class="legend" aria-label="Topics">
			{#each legend as item (item.label)}
				<span class="key"><i style="background:{item.color}"></i>{item.label}</span>
			{/each}
		</div>
	</div>
	<div class="grid">
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
					<!-- the pane's numbers in plain ink, each under its topic's shorthand -->
					{#if showChips && avg}
						<span class="avg-chip">
							<small>{second ? SHORTHAND[topic] ?? topic : "avg"}</small>
							{measure === "share" ? pct(avg.share) : totalHits(pts).toLocaleString()}
						</span>
					{/if}
					{#if showChips && second && avg2}
						<span class="avg-chip">
							<small>{SHORTHAND[second] ?? second}</small>
							{measure === "share" ? pct(avg2.share) : totalHits(pts2).toLocaleString()}
						</span>
					{/if}
				</div>
				<svg
					viewBox="0 0 {W} {H}"
					role="img"
					aria-label="{measure === 'share' ? 'Share' : 'Number'} of {outlet} WNBA articles that {TOPIC_PHRASE}, by {monthly ? 'month' : 'year'}"
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
								text-anchor="end">{measure === "share" ? Math.round(pct * 100) + "%" : pct.toLocaleString()}</text
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
							y2={M.top + plotH + ((monthly ? year.endsWith("-01") : +year % 2 === 0) ? 4 : 2.5)}
						/>
					{/each}
					{#each years as year, index}
						{#if showX && !monthly && +year % 2 === 0}
							<text class="tick year" x={xMid(index)} y={H - 6} text-anchor="middle">{year}</text>
						{:else if showX && monthly}
							{#if monthLabel(year, index)}
								<text class="tick month" x={xMid(index)} y={H - 17} text-anchor="middle">{monthLabel(year, index)}</text>
							{/if}
							{#if yearLabel(year, index, years)}
								<text class="tick year" x={xMid(index)} y={H - 5} text-anchor="middle">{yearLabel(year, index, years)}</text>
							{/if}
						{/if}
					{/each}

					{#if showAvg && avg && measure === "share"}
						<line
							class="avg-line"
							x1={M.left}
							x2={W - M.right}
							y1={pctY(avg.share)}
							y2={pctY(avg.share)}
							stroke={second ? MAIN : AVG}
						/>
					{/if}
					{#if showAvg && second && avg2 && measure === "share"}
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
						{#if second && pts2.length && !stacked}
							{#if showArea}<path class="topic-area" d={areaFor(pts2)} fill={SECOND} />{/if}
							<path class="topic-line" d={pathFor(pts2)} stroke={SECOND} />
							{#each pts2 as p (p.year)}
								<circle
									cx={xMid(p.index)}
									cy={pctY(p.y)}
									r={monthly ? 2 : 3}
									fill={SECOND}
								/>
							{/each}
						{/if}
						{#if showArea}<path class="topic-area" class:solid={stacked} d={areaFor(pts)} fill={MAIN} />{/if}
						<path class="topic-line" d={pathFor(pts)} stroke={MAIN} />
						{#if second && pts2.length && stacked}
							<!-- the second topic stacked on the first, a solid band like the word chart -->
							<path class="topic-area solid" d={bandFor(pts2)} fill={SECOND} />
							<path class="topic-line" d={pathFor(pts2)} stroke={SECOND} />
							{#if parts}
								<!-- the articles with both, a blended band between the two -->
								<path class="topic-area solid" d={bandFor(bothBand(outlet))} fill={BOTH} />
							{/if}
						{/if}
						{#if !stacked}
							{#each pts as p (p.year)}
								<circle cx={xMid(p.index)} cy={pctY(p.y)} r={monthly ? 2 : 3} fill={MAIN} />
							{/each}
						{/if}
					</g>
					{#if MARK && years.includes(MARK)}
						<line class="mark" x1={xMid(years.indexOf(MARK))} x2={xMid(years.indexOf(MARK))} y1={M.top} y2={M.top + plotH} />
						<!-- a wider invisible line so the rule is easy to hover -->
						<line class="mark-hit" x1={xMid(years.indexOf(MARK))} x2={xMid(years.indexOf(MARK))} y1={M.top} y2={M.top + plotH}
							onpointermove={(e) => showMarkTip(e, outlet)} onpointerleave={() => (tip = null)} />
					{/if}
					{#each pts as p (p.year)}
						<rect
							x={M.left + p.index * colW}
							width={colW}
							y={M.top}
							height={plotH}
							fill="transparent"
							onpointermove={(e) => showTip(e, outlet, p.year, p.v, byOutlet2?.[outlet]?.[p.year] ?? null)}
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
				<!-- the label stays put; the caret says whether it is open -->
				{wordsLabel}
				<span class="caret">{wordsOpen ? "▴" : "▾"}</span>
			</button>
			{#if wordsOpen}
				<div class="word-list">
					<!-- what counts, then the words, in the same type -->
					{#if wordsNote}<p>{@html wordsNote}</p>{/if}
					{#each wordGroups as group (group.label)}
						<p><b>{group.label}:</b> {group.words.join(", ")}</p>
					{/each}
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
			{#if tip.mark}
				<strong>{markDate}</strong>
				<p class="line">{MARK_TEXT || "The date marked on every pane."}</p>
			{:else}
			<strong>{SHORT_NAME[tip.outlet] ?? tip.outlet} · {periodLabel(tip.year)}</strong>
			{#if second}
				<!-- two topics: a line for each, in its colour, out of the same articles -->
				<p class="line"><i class="swatch" style="background:{MAIN}"></i><b>{LEGEND_OF[topic] ?? PHRASE_OF[topic] ?? topic}</b>: {tip.hit} of {tip.n.toLocaleString()} {method === "headline" ? "headlines" : "articles"} ({pct(tip.hit / tip.n)})</p>
				{#if tip.second}
					<p class="line"><i class="swatch" style="background:{SECOND}"></i><b>{LEGEND_OF[second] ?? PHRASE_OF[second] ?? second}</b>: {tip.second.hit} of {tip.second.n.toLocaleString()} ({pct(tip.second.hit / tip.second.n)})</p>
				{/if}
				{#if parts && byBoth?.[tip.outlet]?.[tip.year]}
					{@const b = byBoth[tip.outlet][tip.year]}
					<p class="line"><i class="swatch" style="background:{BOTH}"></i><b>both</b>: {b.hit} ({pct(b.hit / b.n)}); either: {tip.hit + tip.second.hit - b.hit} ({pct((tip.hit + tip.second.hit - b.hit) / tip.n)})</p>
				{/if}
			{:else}
				<p class="line">
					{tip.hit} of {tip.n.toLocaleString()}
					{method === "headline" ? "headlines" : "articles"} —
					{((tip.hit / tip.n) * 100).toFixed(tip.hit / tip.n < 0.02 ? 1 : 0)}% —
					{TOPIC_PHRASE}.
					{#if avg}
						Its average over all years: {pct(avg.share)}.
					{/if}
				</p>
			{/if}
			{/if}
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
		margin: 0;
		padding: 4px 6px;
		border: 0;
		background: transparent;
		font: inherit;
		font-size: 12.5px;
		font-weight: 600;
		color: var(--color-ink-dark);
		cursor: pointer;
	}
	.reveal:hover {
		text-decoration: underline;
		text-underline-offset: 3px;
	}
	/* the toggle and the list sit at the left edge of the column */
	.words {
		text-align: left;
	}
	.word-list {
		text-align: left;
	}
	.word-list {
		padding: 10px 0 4px;
		font-size: 13px;
		line-height: 1.55;
		color: var(--color-ink-dark);
	}
	.word-list p {
		margin: 0 0 8px;
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
		font-family: var(--font-chart);
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
	.measure-toggle {
		display: flex;
		justify-content: center;
		gap: 0;
		margin: 0 0 10px;
	}
	.measure-toggle button {
		border: 1px solid rgba(42, 21, 3, 0.3);
		background: transparent;
		color: var(--color-ink);
		font-family: var(--font-chart);
		font-size: 12px;
		font-weight: 700;
		padding: 5px 12px;
		cursor: pointer;
			min-width: 34px;
		font-variant-numeric: tabular-nums;
}
	.measure-toggle button:first-child {
		border-radius: 4px 0 0 4px;
	}
	.measure-toggle button:last-child {
		border-radius: 0 4px 4px 0;
		border-left: 0;
	}
	.measure-toggle button.active {
		background: var(--color-ink);
		color: #fff;
	}
	.avg-chip {
		display: inline-flex;
		flex-direction: column;
		align-items: center;
		line-height: 1.05;
		font-family: var(--font-chart);
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.02em;
		margin-left: 6px;
		color: var(--color-ink);
		font-variant-numeric: tabular-nums;
	}
	.avg-chip small {
		font-size: 8.5px;
		font-weight: 600;
		letter-spacing: 0.05em;
		text-transform: uppercase;
		opacity: 0.65;
	}
	.top {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 10px;
		margin: 0 0 10px;
	}
	.top .measure-toggle {
		margin: 0;
	}
	.legend {
		display: flex;
		gap: 12px;
		font-family: var(--font-chart);
		font-size: 11px;
		font-weight: 700;
		color: var(--color-ink);
	}
	.legend .key {
		display: inline-flex;
		align-items: center;
		gap: 5px;
	}
	.legend i {
		display: inline-block;
		width: 12px;
		height: 12px;
		border-radius: 3px;
	}
	@media (max-width: 640px) {
		.top {
			flex-direction: column;
			align-items: stretch;
		}
		.legend {
			justify-content: flex-end;
		}
	}

	.tooltip {
		position: absolute;
		transform: translate(14px, -50%);
		width: 240px;
		background: var(--tip-bg);
		border: 1px solid var(--tip-border);
		border-radius: var(--tip-radius);
		padding: var(--tip-pad);
		box-shadow: var(--tip-shadow);
		pointer-events: none;
		z-index: 5;
	}
	.tooltip.flip {
		transform: translate(calc(-100% - 14px), -50%);
	}
	/* the shared tooltip (variables.css): serif title, figures in the chart font */
	.tooltip strong {
		display: block;
		font: var(--tip-title);
		color: var(--tip-ink);
	}
	.tooltip .line {
		margin: 5px 0 0;
		font: var(--tip-body);
		color: var(--tip-ink);
	}
	.topic-area.solid {
		opacity: 0.85;
	}
	.mark {
		stroke: var(--color-ink);
		stroke-width: 1;
		stroke-dasharray: 3 3;
	}
	.tick.month {
		font-size: 9px;
		opacity: 0.8;
	}
	.tooltip .swatch {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 2px;
		margin-right: 5px;
		vertical-align: -1px;
	}
	.mark-hit {
		stroke: transparent;
		stroke-width: 9;
		cursor: help;
	}
</style>
