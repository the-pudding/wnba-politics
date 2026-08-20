<script>
	// Google Ngram-style chart: for each word, the share of Fox's WNBA articles
	// that month containing it.
	// Doc embed:  chart: ngram | words: trans language, protect | smooth: 2
	import rows from "$data/fox_ngrams.csv";
	import { line as svgLine, curveMonotoneX } from "d3-shape";

	// `smooth` pools each month with ±N neighbours (hits over articles)
	let { words = [], smooth = 2 } = $props();

	const data = {
		months: rows.map((r) => r.month),
		totals: rows.map((r) => +r.articles),
		series: Object.keys(rows[0])
			.filter((k) => k !== "month" && k !== "articles")
			.map((word) => ({ word, counts: rows.map((r) => +r[word]) }))
	};

	// ~3MB per-word index loads lazily on first touch of the search input
	let kw = $state(null);
	let query = $state("");
	let added = $state([]);
	let notFound = $state("");
	async function ensureIndex() {
		if (!kw) kw = (await import("$data/fox_kw.json")).default;
	}
	let suggestions = $derived.by(() => {
		if (!kw || query.trim().length < 2) return [];
		const q = query.trim().toLowerCase();
		const taken = new Set([...added, ...series.map((s) => s.word)]);
		const all = Object.keys(kw.words);
		const starts = all.filter((w) => w.startsWith(q) && !taken.has(w));
		const contains = all.filter((w) => !w.startsWith(q) && w.includes(q) && !taken.has(w));
		return [...starts, ...contains].slice(0, 7);
	});
	function addWord(word) {
		const w = (word ?? "").trim().toLowerCase();
		if (!w || added.includes(w)) return;
		if (!kw?.words[w]) {
			notFound = `“${w}” isn't in the index (a word needs to appear in 10+ articles)`;
			return;
		}
		notFound = "";
		added = [...added, w];
		query = "";
	}
	const dropWord = (w) => (added = added.filter((x) => x !== w));

	const COLORS = {
		trans: "var(--color-trans)",
		transgender: "#1d4f9c",
		protect: "var(--color-fox)",
		race: "var(--color-race)",
		white: "#6b5b45",
		"trans language": "var(--color-trans)",
		"caitlin clark": "var(--color-clark)",
		"sophie cunningham": "var(--color-cunningham)"
	};
	const FALLBACK_COLORS = ["#1f9d6e", "#7a6bcc", "#b04ac2", "#7a4a00"];

	let wanted = $derived(words.length ? words.map((w) => w.toLowerCase()) : null);
	let series = $derived(data.series
		.filter((s) => !wanted || wanted.includes(s.word))
		.map((s, i) => ({ ...s, color: COLORS[s.word] ?? FALLBACK_COLORS[i % FALLBACK_COLORS.length] })));

	// pooled hits over pooled articles, not averaged ratios — a 2-article month can't swing the line
	let window_ = $derived(Math.max(0, Math.round(+smooth || 0)));
	let pooled = $derived((counts) => counts.map((_, i) => {
		let hit = 0, total = 0;
		for (let j = Math.max(0, i - window_);
			j <= Math.min(counts.length - 1, i + window_); j++) {
			hit += counts[j]; total += data.totals[j];
		}
		return total ? hit / total : 0;
	}));
	let extraSeries = $derived(!kw ? [] : added
		.filter((w) => kw.words[w])
		.map((w, i) => ({ word: w,
			counts: data.months.map((m) => kw.words[w][m] ?? 0),
			color: FALLBACK_COLORS[i % FALLBACK_COLORS.length] })));
	let lines = $derived([...series, ...extraSeries]
		.map((s) => ({ ...s, pct: pooled(s.counts) })));

	let viewportWidth = $state(typeof window === "undefined" ? 1200 : window.innerWidth);
	let mobile = $derived(viewportWidth < 640);
	let WIDTH = $derived(mobile ? 480 : 860);
	let HEIGHT = $derived(mobile ? 440 : 360);
	let margin = $derived(mobile
		? { left: 54, right: 92, top: 34, bottom: 34 }
		: { left: 44, right: 100, top: 30, bottom: 30 });

	// surnames at line ends — full names spill off the chart
	const SHORT = { "caitlin clark": "Clark", "sophie cunningham": "Cunningham" };
	let plotWidth = $derived(WIDTH - margin.left - margin.right);
	let plotHeight = $derived(HEIGHT - margin.top - margin.bottom);

	let months = $derived(data.months);
	let stepX = $derived(plotWidth / Math.max(1, months.length - 1));
	let peak = $derived(Math.max(0.05, ...lines.flatMap((l) => l.pct)));
	let yMax = $derived(Math.ceil(peak * 10) / 10);
	const xAt = (i) => margin.left + i * stepX;
	let yAt = $derived((pct) => margin.top + plotHeight * (1 - pct / yMax));

	// monotone curve: never invents dips below the data between points
	let curve = $derived(svgLine()
		.x((_, i) => xAt(i))
		.y((p) => yAt(p))
		.curve(curveMonotoneX));
	let paths = $derived(lines.map((l) => ({ ...l, d: curve(l.pct) })));

	let endLabels = $derived.by(() => {
		const placed = [];
		for (const l of [...lines].sort((a, b) => yAt(a.pct.at(-1)) - yAt(b.pct.at(-1)))) {
			let y = yAt(l.pct.at(-1)) + 4;
			while (placed.some((p) => Math.abs(p.y - y) < 14)) y += 14;
			placed.push({ word: l.word, color: l.color, y });
		}
		return placed;
	});

	let yTicks = $derived([...Array(Math.round(yMax * 10))].map((_, i) => (i + 1) / 10));
	let xTicks = $derived(months.map((m, i) => ({ m, i }))
		.filter(({ m }) => m.endsWith("-01"))
		.map(({ m, i }) => ({ label: m.slice(0, 4), x: xAt(i) })));

	let tip = $state(null);
	function moved(event) {
		const box = event.currentTarget.getBoundingClientRect();
		const unit = box.width / WIDTH;
		const i = Math.round(((event.clientX - box.left) / unit - margin.left) / stepX);
		if (i < 0 || i >= months.length) { tip = null; return; }
		const holder = event.currentTarget.closest(".ngram-chart").getBoundingClientRect();
		tip = { i, month: months[i],
			rows: lines
				.map((l) => ({ word: l.word, color: l.color, pct: l.pct[i] }))
				.sort((a, b) => b.pct - a.pct),
			x: event.clientX - holder.left,
			y: Math.min(Math.max(70, event.clientY - holder.top), holder.height - 80),
			flip: event.clientX - holder.left > holder.width - 240 };
	}
	const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
		"Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
	const monthLabel = (m) => `${MONTH_NAMES[Number(m.slice(5, 7)) - 1]} ${m.slice(0, 4)}`;
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<div class="ngram-chart" class:mobile>
	<div class="search">
		<div class="box">
			<input
				type="text"
				placeholder="search"
				bind:value={query}
				onfocus={ensureIndex}
				oninput={ensureIndex}
				onkeydown={(e) => { if (e.key === "Enter") addWord(suggestions[0] ?? query); }}
				aria-label="Add a word to the chart" />
			{#if suggestions.length}
				<ul class="sug">
					{#each suggestions as s (s)}
						<li><button onclick={() => addWord(s)}>{s}</button></li>
					{/each}
				</ul>
			{/if}
		</div>
		{#each added as w (w)}
			{@const color = extraSeries.find((s) => s.word === w)?.color}
			<button class="chip" style="border-color:{color}; color:{color}"
				onclick={() => dropWord(w)} title="remove">
				{w} <span class="x">×</span>
			</button>
		{/each}
		{#if notFound}<span class="nf">{notFound}</span>{/if}
	</div>

	<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img"
		aria-label="Share of Fox WNBA articles per month containing each word"
		onpointermove={moved} onpointerleave={() => (tip = null)}>
		{#each yTicks as tick}
			<line class="grid" x1={margin.left} x2={margin.left + plotWidth}
				y1={yAt(tick)} y2={yAt(tick)} />
			<text class="tick" x={margin.left - 8} y={yAt(tick) + 4}
				text-anchor="end">{Math.round(tick * 100)}%</text>
		{/each}
		{#each xTicks as tick}
			<text class="tick" x={tick.x} y={HEIGHT - 8}>{tick.label}</text>
		{/each}
		<line class="axis" x1={margin.left} x2={margin.left + plotWidth}
			y1={margin.top + plotHeight} y2={margin.top + plotHeight} />

		{#if tip}
			<line class="probe" x1={xAt(tip.i)} x2={xAt(tip.i)}
				y1={margin.top} y2={margin.top + plotHeight} />
		{/if}

		{#each paths as line (line.word)}
			<path d={line.d} stroke={line.color} />
			{#if tip}
				<circle cx={xAt(tip.i)} cy={yAt(line.pct[tip.i])} r="3.5" fill={line.color} />
			{/if}
		{/each}

		{#each endLabels as label (label.word)}
			<text class="end" x={margin.left + plotWidth + 6} y={label.y}
				fill={label.color}>{SHORT[label.word] ?? label.word}</text>
		{/each}
	</svg>

	{#if tip}
		<div class="tooltip" class:flip={tip.flip} style="left:{tip.x}px; top:{tip.y}px">
			<strong>{monthLabel(tip.month)}</strong>
			<div class="rows">
				{#each tip.rows as row (row.word)}
					<div class="row">
						<span class="who" style="color:{row.color}">{row.word}</span>
						<span class="pct">{(row.pct * 100).toFixed(1)}%</span>
					</div>
				{/each}
			</div>
		</div>
	{/if}

</div>

<style>
	.ngram-chart { position: relative; max-width: 860px; margin: 6px auto 18px; }
	svg { width: 100%; height: auto; display: block; overflow: visible; }

	.grid { stroke: rgba(42, 21, 3, 0.1); stroke-width: 1; }
	.axis { stroke: rgba(42, 21, 3, 0.35); stroke-width: 1; }
	.tick { font-size: 12px; fill: rgba(42, 21, 3, 0.6); }
	.mobile .tick { font-size: 17px; }
	.probe { stroke: rgba(42, 21, 3, 0.3); stroke-width: 1; stroke-dasharray: 3 3; }

	path { fill: none; stroke-width: 2.4; stroke-linejoin: round; stroke-linecap: round; }
	.end {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12.5px; font-weight: 700;
		paint-order: stroke; stroke: rgba(255, 253, 248, 0.9); stroke-width: 3px;
	}
	.mobile .end { font-size: 15px; }


	.search {
		display: flex; align-items: center; flex-wrap: wrap; gap: 8px;
		margin: 0 0 10px; justify-content: center;
	}
	.box { position: relative; }
	.box input {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 13.5px; color: var(--color-ink);
		background: var(--color-paper); border: 1px solid rgba(42, 21, 3, 0.25);
		border-radius: 3px; padding: 7px 11px; width: 250px;
	}
	.box input:focus { outline: 2px solid rgba(42, 21, 3, 0.25); outline-offset: 1px; }
	.box input::placeholder { color: rgba(42, 21, 3, 0.4); }
	.sug {
		position: absolute; top: calc(100% + 3px); left: 0; right: 0; z-index: 6;
		margin: 0; padding: 4px 0; list-style: none;
		background: var(--color-paper); border: 1px solid rgba(42, 21, 3, 0.18);
		border-radius: 3px; box-shadow: 0 5px 20px rgba(42, 21, 3, 0.16);
	}
	.sug button {
		display: block; width: 100%; text-align: left;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 13.5px; color: var(--color-ink);
		background: none; border: none; padding: 5px 11px; cursor: pointer;
	}
	.sug button:hover { background: rgba(42, 21, 3, 0.07); }
	.chip {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12.5px; font-weight: 700;
		background: var(--color-paper); border: 1.5px solid; border-radius: 999px;
		padding: 4px 11px; cursor: pointer;
	}
	.chip .x { opacity: 0.6; margin-left: 2px; }
	.chip:hover .x { opacity: 1; }
	.nf {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12px; color: var(--color-fox);
	}
	.mobile .box input { width: min(80vw, 320px); font-size: 16px; }

	.tooltip {
		position: absolute; transform: translate(14px, -50%);
		width: 210px;
		background: var(--color-paper); border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid var(--color-fox); border-radius: 3px;
		padding: 9px 12px 10px;
		box-shadow: 0 5px 20px rgba(42, 21, 3, 0.16);
		pointer-events: none; z-index: 5;
	}
	.tooltip.flip { transform: translate(calc(-100% - 14px), -50%); }
	.tooltip strong {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px; font-weight: 700; letter-spacing: 0.06em;
		text-transform: uppercase; color: rgba(42, 21, 3, 0.6);
	}
	.rows { margin-top: 6px; }
	.row {
		display: flex; justify-content: space-between; align-items: baseline;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12.5px; line-height: 1.7;
	}
	.row .who { font-weight: 700; }
	.row .pct { font-weight: 600; color: var(--color-ink); font-variant-numeric: tabular-nums; }
</style>
