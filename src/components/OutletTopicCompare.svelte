<script>
	// Small multiples
	import { base } from "$app/paths";
	import rows from "$data/outlet_topics.csv";
	// the same counts by month (notebooks/outlet_topics_monthly.py), for a zoomed span
	import monthRows from "$data/outlet_topics_monthly.csv";
	import { flip } from "svelte/animate";
	import { fade } from "svelte/transition";
	// the vocabulary behind each topic, straight from the notebooks' term list
	import { wordGroupsFor } from "$utils/topicWords.js";


	let {
		topic = "polrace",
		method = "body",
		dots = null,
		second = null,
		// every outlet the same size, Fox first, in rows of `across` (three by
		// default; two on phones whatever it says), a short last row centred. Other arrangements tried along the way are in
		// archive/components/OutletTopicCompare.full.svelte.
		across = 3,
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
		// markNote: a short label with an arrow to the rule, on Fox's pane only
		// ("Republicans send letter to commissioner" for the 2026-07-07 letter
		// unless the Doc says otherwise; a long one wraps to two lines)
		markNote = "",
		// measure: what the panes open on, "share" or "count"
		measure: startMeasure = "share",
		// chips: the per-pane numbers beside the wordmark (false hides them)
		chips = true,
		// wordsLabel: the old fold-out's label, ignored now the words always show
		wordsLabel = "",
		// a line above the words, if the Doc gives one (none by default)
		wordsNote = ""
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
				? "use foul words"
				: "mention race";
	const COLOR_OF = {
		lgbtq: "var(--color-lgbtq)",
		polrace: "var(--color-politics)",
		// the word chart's brown and navy, each a step lighter here, where the
		// two lines cross month after month near zero and the darker pair
		// muddied into one (2026-10-02)
		fouls: "color-mix(in srgb, var(--color-brown) 78%, #e09a3e)",   // the foul words in brown
		protect: "color-mix(in srgb, var(--color-fox-navy) 52%, white)" // "protect" in a lighter navy
	};
	const PHRASE_OF = {
		lgbtq: "LGBTQ+ topics",
		polrace: "race",
		fouls: "foul words",
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
	const MARK_NOTE = String(markNote).trim() || (String(mark).trim() === "2026-07-07" ? "Republicans send letter to commissioner" : "");
	// a long note breaks into two lines at the space nearest its middle
	const MARK_LINES = (() => {
		if (MARK_NOTE.length <= 22) return [MARK_NOTE];
		const mid = MARK_NOTE.length / 2;
		let cut = -1;
		for (let i = 0; i < MARK_NOTE.length; i++)
			if (MARK_NOTE[i] === " " && (cut < 0 || Math.abs(i - mid) < Math.abs(cut - mid))) cut = i;
		return cut < 0 ? [MARK_NOTE] : [MARK_NOTE.slice(0, cut), MARK_NOTE.slice(cut + 1)];
	})();
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
	// the chips' shorthand for each topic, and the tooltip's words
	const SHORTHAND = { polrace: "race", lgbtq: "LGBTQ+", fouls: "foul words", protect: "protect" };
	// the tooltip names the pinned topics' words outright
	const LEGEND_OF = { fouls: "hip-check, poke, punch, throat", protect: "protect" };
	// the key line's words: each topic by the name its caption below uses
	const VERB_OF = { lgbtq: "mention", polrace: "mention", fouls: "use" };
	const KEY_OF = { polrace: "race", lgbtq: "LGBTQ+ topics", fouls: "hip-check, poke, punch or throat", protect: "“protect”" };
	const keyTopics = [[topic, MAIN], ...(second ? [[second, SECOND]] : [])].map(([t, color]) => ({
		label: KEY_OF[t] ?? PHRASE_OF[t] ?? t, color
	}));
	const MIN_N = monthly ? 8 : 20;   // a period with fewer articles than this is not drawn: a share of 6 articles is noise
	const AVG = "var(--color-ink-dark)"; // the average rule, apart from either topic colour

	// the words counted, listed under the panels (utils/topicWords.js)
	const wordGroups = wordGroupsFor(topic, second);

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
	let cols = $derived(mobile ? 2 : Math.max(1, parseInt(across) || 3));

	// Where every pane sits: rows of `cols`, the last row centred when it is
	// short (on phones, two to a row and the last on the left). The grid has
	// twice as many tracks as panes to a row, so a centred pane can sit half a
	// pane in. Every pane carries both axes' labels.
	let cells = $derived.by(() => {
		const out = [];
		const list = [...shown];
		if (mobile) {
			list.forEach((o, k) => out.push({ outlet: o, row: Math.floor(k / 2), start: k % 2, span: 1 }));
		} else {
			let i = 0, row = 0;
			while (i < list.length) {
				const take = Math.min(cols, list.length - i);
				const start = cols - take;
				for (let k = 0; k < take; k++)
					out.push({ outlet: list[i + k], row, start: start + 2 * k, span: 2 });
				i += take;
				row += 1;
			}
		}
		// every pane shares the scale, so only the first pane in each row
		// carries the y values and label; the rest keep the gridlines
		return out.map((c, k) => ({ ...c, showY: k === 0 || out[k - 1].row !== c.row, showX: true }));
	});

	const W = 220,
		H = 150;
	// left: the tick values and the axis label turned up beside them; top:
	// the outlet's average, written inside the plot; right: room for the last
	// year label, centred on the last point
	const M = { left: 46, right: 16, top: 16, bottom: monthly ? 32 : 22 };
	// month mode: "Jan" / "Jul" on one row, the year on a row beneath at each
	// January (and under the first column when the span starts mid-year)
	const monthLabel = (period) => (period.endsWith("-01") ? "Jan" : period.endsWith("-07") ? "Jul" : "");
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

<div class="otc" class:mobile class:monthly bind:this={root}>
	<!-- the chart's key as one line over the panes: the measure switch,
	     then what is counted, its colours named in the sentence -->
	<p class="top">
		<span class="measure-toggle" role="group" aria-label="What the panes show">
			<button class:active={measure === "share"} onclick={() => (measure = "share")} title="Share of articles" aria-label="Share of articles">%</button>
			<button class:active={measure === "count"} onclick={() => (measure = "count")} title="Number of articles" aria-label="Number of articles">#</button>
		</span>
		<span class="key-words">
			of WNBA {method === "headline" ? "headlines" : "articles"} that {VERB_OF[topic] ?? "mention"}
			{#each keyTopics as item, k (item.label)}
				{#if k > 0}{k < keyTopics.length - 1 ? ", " : keyTopics[k - 1].label.includes(" or ") ? ", or " : " or "}{/if}<span class="key"><i style="background:{item.color}"></i>{item.label}</span>
			{/each}{#if parts}<span class="key both"> (<i style="background:{BOTH}"></i>both)</span>{/if},
			by {monthly ? "month" : "year"}
		</span>
	</p>
	<div class="grid" style="--tracks: {cols * 2}">
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
				<!-- the outlet, over its plot, at the plot's left edge -->
				<div class="pane-hed" style:padding-left="{(M.left / W) * 100}%">
					<img
						src="{base}/logos/{LOGOS[outlet].file}"
						alt={SHORT_NAME[outlet] ?? outlet}
						style:height="{LOGOS[outlet].h}px"
						style:filter={outlet === NBA ? "grayscale(1) opacity(0.75)" : ""}
					/>
					{#if LEAGUE_TAG[outlet]}
						<span class="league-tag">{LEAGUE_TAG[outlet]}</span>
					{/if}
				</div>
				<svg
					viewBox="0 0 {W} {H}"
					role="img"
					aria-label="{measure === 'share' ? 'Share' : 'Number'} of {outlet} WNBA articles that {TOPIC_PHRASE}, by {monthly ? 'month' : 'year'}"
				>
					{#each yTicks as pct}
						<line class="grid-line" x1={M.left} x2={W - M.right} y1={pctY(pct)} y2={pctY(pct)} />
						{#if showY}
							<text class="tick" x={M.left - 5} y={pctY(pct) + 4} text-anchor="end"
								>{measure === "share" ? Math.round(pct * 100) + "%" : pct.toLocaleString()}</text
							>
						{/if}
					{/each}
					{#if showY}
						<text class="y-label" transform="rotate(-90)" x={-(M.top + plotH / 2)} y="9" text-anchor="middle"
							>{measure === "share" ? "% articles" : "# articles"}</text
						>
					{/if}
					<!-- the outlet's average (its total, counting articles), written in
					     the plot's top corner, clear of the dated note on Fox's pane -->
					{#if showChips && avg}
						{@const left = MARK_NOTE && MARK && outlet === FOX}
						<text class="avg-note" x={left ? M.left + 4 : W - M.right} y={M.top - 4} text-anchor={left ? "start" : "end"}>
							<tspan class="avg-word">{second ? SHORTHAND[topic] ?? topic : measure === "share" ? "avg" : "total"}</tspan>
							<tspan class="avg-value" dx="3">{measure === "share" ? pct(avg.share) : totalHits(pts).toLocaleString()}</tspan>
							{#if second && avg2}
								<tspan class="avg-word" dx="8">{SHORTHAND[second] ?? second}</tspan>
								<tspan class="avg-value" dx="3">{measure === "share" ? pct(avg2.share) : totalHits(pts2).toLocaleString()}</tspan>
							{/if}
						</text>
					{/if}
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
					<!-- a tick for every period; a label every other year (by month,
					     January and July with the year under each January) -->
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
							{#if monthLabel(year)}
								<text class="tick month" x={xMid(index)} y={H - 17} text-anchor="middle">{monthLabel(year)}</text>
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
					</g>
					{#if MARK && years.includes(MARK)}
						<line class="mark" x1={xMid(years.indexOf(MARK))} x2={xMid(years.indexOf(MARK))} y1={M.top} y2={M.top + plotH} />
						<!-- a wider invisible line so the rule is easy to hover -->
						<line class="mark-hit" x1={xMid(years.indexOf(MARK))} x2={xMid(years.indexOf(MARK))} y1={M.top} y2={M.top + plotH}
							onpointermove={(e) => showMarkTip(e, outlet)} onpointerleave={() => (tip = null)} />
						{#if MARK_NOTE && outlet === FOX}
							<!-- on Fox's pane only: what the rule is, an arrow pointing at it -->
							{@const mx = xMid(years.indexOf(MARK))}
							<g class="mark-note">
								<text x={mx - 16} y={M.top + 9} text-anchor="end"
									>{#each MARK_LINES as line, i (i)}<tspan x={mx - 16} dy={i === 0 ? 0 : 11}>{line}</tspan>{/each}</text
								>
								<line x1={mx - 13} x2={mx - 3} y1={M.top + 5.5} y2={M.top + 5.5} />
								<path d="M{mx - 2} {M.top + 5.5} l-4 -2.6 v5.2 z" />
							</g>
						{/if}
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

	<!-- the vocabulary, always shown under the panels as their caption
	     (it was a fold-out "See words included" until 2026-10-01) -->
	{#if wordGroups.length}
		<div class="word-list">
			{#if wordsNote}<p>{@html wordsNote}</p>{/if}
			{#each wordGroups as group (group.label)}
				<p><b>{group.label}:</b> {group.words.join(", ")}</p>
			{/each}
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
	/* the words counted: the chart's caption, in the caption type */
	.word-list {
		max-width: 640px;
		margin: 12px auto 0;
		font-size: 12.5px;
		line-height: 1.5;
		text-align: left;
		color: rgba(42, 21, 3, 0.7);
	}
	.word-list p {
		margin: 0 0 4px;
	}
	.word-list b {
		font-weight: 600;
		color: var(--color-ink-dark);
	}
	.otc {
		position: relative;
		max-width: 880px;
		margin: 6px auto 4px;
	}
	/* two tracks per pane, so a short last row can sit centred; the space
	   between panes is each pane's own padding, not a column gap (a gap on
	   every narrow track outgrew a narrow box and squeezed every column to
	   nothing, 2026-10-01) */
	.grid {
		display: grid;
		grid-template-columns: repeat(var(--tracks, 4), minmax(0, 1fr));
		gap: 16px 0;
	}
	.grid > .pane {
		padding: 0 11px;
		min-width: 0;
	}
	/* a phone's two columns keep their own gap */
	.mobile .grid > .pane {
		padding: 0;
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
		justify-content: flex-start;
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
		stroke: rgba(42, 21, 3, 0.35);
		stroke-width: 1;
	}
	.axis-tick {
		stroke: var(--color-ink);
		stroke-width: 1;
		opacity: 0.5;
	}
	.y-label {
		font-family: var(--font-sans);
		font-size: 10.5px;
		fill: rgba(42, 21, 3, 0.75);
	}
	/* the outlet's average in the plot's corner: the word quiet, the figure
	   in ink */
	.avg-note {
		font-family: var(--font-chart);
		font-size: 11.5px;
	}
	.avg-word {
		fill: rgba(42, 21, 3, 0.6);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-size: 9px;
		font-weight: 600;
	}
	.avg-value {
		fill: var(--color-ink-dark);
		font-weight: 800;
	}
	/* a phone's panes are drawn smaller, so their labels are set larger */
	.mobile .avg-note {
		font-size: 15px;
	}
	.mobile .avg-word {
		font-size: 12px;
	}
	/* the axis numbers in the chart's font, like everything else in it */
	.tick {
		font-family: var(--font-chart);
		font-size: 11px;
		fill: rgba(42, 21, 3, 0.75);
	}
	.mobile .tick {
		font-size: 12px;
	}
	/* the line the same weight however small the pane is drawn */
	.topic-line {
		fill: none;
		stroke-width: 2.5px;
		vector-effect: non-scaling-stroke;
		stroke-linejoin: round;
		stroke-linecap: round;
	}
	/* the area under the line, a tint of its colour */
	/* by month the lines have four times the points, often two of them
	   crossing near zero: a finer pen keeps them from knotting */
	.monthly .topic-line {
		stroke-width: 1.5px;
	}
	.topic-area {
		opacity: 0.14;
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
	/* the key line: the switch sits in the sentence at its size */
	.top {
		margin: 0 0 14px;
		font-family: var(--font-chart);
		font-size: 13px;
		line-height: 1.6;
		color: var(--color-ink);
	}
	.top .measure-toggle {
		display: inline-flex;
		vertical-align: 1px;
		margin: 0 3px 0 0;
	}
	.top .measure-toggle button {
		padding: 1px 8px;
		min-width: 26px;
		font-size: 12px;
	}
	.key {
		display: inline-flex;
		align-items: baseline;
		gap: 4px;
		font-weight: 700;
		white-space: nowrap;
	}
	.key i {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 2px;
		align-self: center;
	}
	.key.both {
		font-weight: 400;
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
	.mark-note text {
		font-family: var(--font-chart);
		font-size: 9.5px;
		font-weight: 600;
		fill: var(--color-ink-dark);
	}
	.mark-note line {
		stroke: var(--color-ink-dark);
		stroke-width: 1;
	}
	.mark-note path {
		fill: var(--color-ink-dark);
	}
	.mark-hit {
		stroke: transparent;
		stroke-width: 9;
		cursor: help;
	}
</style>
