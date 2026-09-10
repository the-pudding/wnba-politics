<script>
	// How often a word turns up in Fox's WNBA articles, week by week (or day
	// by day), with a date marked. In the Doc:
	//   {.WordTimeline}
	//   word: hip-check        (a word from notebooks/word_timeline.py)
	//   words: hip-check, poke, punch, throat   (several, as lines on one plot)
	//   outlet: Fox News       (or ESPN, CBS Sports, USA Today, The Athletic,
	//                           Just Women's Sports)
	//   scope: any | headline | mentions  (articles with the word anywhere, in the
	//                           headline, or every occurrence of the word)
	//   scaleTo: Fox News      (keep the y-axis at that outlet's peak, so outlets compare)
	//   by: week | day
	//   from: 2024-01-01
	//   to: 2026-08-31         (optional; the data's end by default)
	//   mark: 2026-07-07       (a highlighted date; optional)
	//   markLabel: GOP letter  (optional)
	//   title: ...
	//   {}
	import data from "$data/word_timeline.json";

	let {
		word = "hip-check",
		words = "",
		outlet = "Fox News",
		scope = "any",
		scaleTo = "",
		// the drawing's size in its own units (type stays the same size, so a
		// narrower drawing suits a small panel)
		width = 900,
		height = 300,
		// axis: false hides the y labels (a panel row shares them)
		axis = true,
		by = "week",
		from = "2024-01-01",
		to = "",
		mark = "",
		markLabel = ""
	} = $props();

	const DAY = 86400000;
	const parse = (s) => new Date(s + "T00:00:00Z");
	const iso = (d) => d.toISOString().slice(0, 10);
	const weekly = $derived(String(by).trim().toLowerCase() !== "day");
	// several words: lines on one plot, in a fixed colour order
	const PALETTE = ["#003366", "#6b4bb0", "var(--color-fox)", "#1f9d6e", "#7a4a00", "#b04ac2"];
	let source = $derived(data.outlets[String(outlet).trim()] ?? data.outlets["Fox News"]);
	let field = $derived(
		["headline", "mentions"].includes(String(scope).trim().toLowerCase())
			? String(scope).trim().toLowerCase()
			: "any"
	);
	let unit = $derived(field === "mentions" ? "mentions" : "articles");
	let list = $derived(
		String(words)
			.split(",")
			.map((w) => w.trim())
			.filter((w) => w && source.words[w])
	);
	let multi = $derived(list.length > 1);
	const entriesFor = (src) =>
		(multi ? list : [String(word).trim()]).map((w, i) => {
			const e = src.words[w] ?? { any: {}, headline: {}, examples: {} };
			return { word: w, color: PALETTE[i % PALETTE.length], counts: e[field] ?? {}, examples: e.examples ?? {} };
		});
	let entries = $derived(entriesFor(source));
	const entry = $derived(entries[0]);
	let end = $derived(
		String(to).trim() || Object.keys(source.articles).sort().at(-1) || "2026-08-31"
	);
	// the bins: every day, or every Monday-to-Sunday week, from `from` to `to`
	const binsFor = (src, entries) => {
		const entry = entries[0];
		const start = parse(from);
		const last = parse(end);
		const out = [];
		if (weekly) {
			// back up to the Monday on or before the start
			const s = new Date(start);
			s.setUTCDate(s.getUTCDate() - ((s.getUTCDay() + 6) % 7));
			for (let d = s; d <= last; d = new Date(d.getTime() + 7 * DAY)) {
				let hits = 0, articles = 0, example = "";
				const each = entries.map(() => 0);
				for (let k = 0; k < 7; k++) {
					const key = iso(new Date(d.getTime() + k * DAY));
					hits += entry.counts[key] ?? 0;
					entries.forEach((e, j) => (each[j] += e.counts[key] ?? 0));
					articles += src.articles[key] ?? 0;
					if (!example && entry.examples[key]) example = entry.examples[key];
				}
				out.push({ start: iso(d), hits, each, articles, example });
			}
		} else {
			for (let d = start; d <= last; d = new Date(d.getTime() + DAY)) {
				const key = iso(d);
				out.push({
					start: key,
					hits: entry.counts[key] ?? 0,
					each: entries.map((e) => e.counts[key] ?? 0),
					articles: src.articles[key] ?? 0,
					example: entry.examples[key] ?? ""
				});
			}
		}
		return out;
	};
	let bins = $derived(binsFor(source, entries));
	// the y-axis: this outlet's peak, or another outlet's when `scaleTo` names one
	let scaleSource = $derived(data.outlets[String(scaleTo).trim()] ?? null);
	let scaleBins = $derived(scaleSource ? binsFor(scaleSource, entriesFor(scaleSource)) : null);
	let peak = $derived(
		Math.max(1, ...(scaleBins ?? bins).flatMap((b) => (multi ? b.each : [b.hits])))
	);
	let total = $derived(bins.reduce((s, b) => s + b.hits, 0));
	let totals = $derived(entries.map((_, j) => bins.reduce((s, b) => s + b.each[j], 0)));
	// each line's path, and where to put its label (its peak)
	let lines = $derived(
		entries.map((e, j) => {
			const pts = bins.map((b, i) => [xOf(i) + stepX / 2, yOf(b.each[j])]);
			let top = 0;
			bins.forEach((b, i) => {
				if (b.each[j] > bins[top].each[j]) top = i;
			});
			// the label sits beside the peak, on whichever side has room
			const right = pts[top][0] > PAD.left + plotW * 0.7;
			return {
				...e,
				d: pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" "),
				label: {
					x: right ? pts[top][0] - 8 : pts[top][0] + 8,
					y: Math.max(PAD.top + 12, pts[top][1] + 4),
					anchor: right ? "end" : "start"
				}
			};
		})
	);

	const WIDTH = $derived(+width || 900);
	const HEIGHT = $derived(+height || 300);
	// a small panel: a tick a year, and no date label on the mark
	let small = $derived(WIDTH < 600);
	// room above the plot for the legend row (several words) or the total
	let PAD = $derived({ top: multi ? 34 : 26, right: 18, bottom: 40, left: axis ? 36 : 14 });
	let plotW = $derived(WIDTH - PAD.left - PAD.right);
	let plotH = $derived(HEIGHT - PAD.top - PAD.bottom);
	let stepX = $derived(plotW / Math.max(1, bins.length));
	const xOf = (i) => PAD.left + i * stepX;
	const yOf = (v) => PAD.top + plotH - (v / peak) * plotH;
	// the mark: where the date falls among the bins
	let markX = $derived.by(() => {
		const m = String(mark).trim();
		if (!m) return null;
		const t = parse(m).getTime();
		const i = bins.findIndex(
			(b, j) => t >= parse(b.start).getTime() && (j === bins.length - 1 || t < parse(bins[j + 1].start).getTime())
		);
		if (i < 0) return null;
		const span = weekly ? 7 : 1;
		const frac = (t - parse(bins[i].start).getTime()) / (span * DAY);
		return xOf(i) + frac * stepX;
	});
	// a tick each quarter, labelled with the month and year
	let ticks = $derived(
		bins
			.map((b, i) => ({ b, i }))
			.filter(({ b }, k) => {
				const d = parse(b.start);
				const prev = k ? parse(bins[k - 1].start) : null;
				return !prev || d.getUTCMonth() !== prev.getUTCMonth();
			})
			.filter(({ b }) => (small ? [0] : [0, 3, 6, 9]).includes(parse(b.start).getUTCMonth()))
			.map(({ b, i }) => ({
				x: xOf(i),
				label: small
					? String(parse(b.start).getUTCFullYear())
					: parse(b.start).toLocaleDateString("en-US", { month: "short", year: "numeric", timeZone: "UTC" })
			}))
	);
	let yTicks = $derived([...new Set([0, Math.round(peak / 2), peak])]);

	let tip = $state(null);
	let el = $state(null);
	function show(event, bin, i) {
		const box = el.getBoundingClientRect();
		const scale = box.width / WIDTH;
		const cx = xOf(i) + stepX / 2;
		if (!multi) {
			tip = { bin, cx, x: cx * scale, y: yOf(bin.hits) * scale, j: 0 };
			return;
		}
		// the line nearest the pointer, up or down: the card points at that
		// line's point for this week
		const py = (event.clientY - box.top) / scale;
		let j = 0;
		bin.each.forEach((v, k) => {
			if (Math.abs(yOf(v) - py) < Math.abs(yOf(bin.each[j]) - py)) j = k;
		});
		tip = { bin, cx, x: cx * scale, y: yOf(bin.each[j]) * scale, j };
	}
	const fmt = (s) =>
		parse(s).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
	const weekLabel = (b) => {
		const e = new Date(parse(b.start).getTime() + 6 * DAY);
		return `Week of ${fmt(b.start).replace(/, \d{4}$/, "")} – ${fmt(iso(e))}`;
	};
</script>

<div class="word-timeline" bind:this={el}>
	<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Fox WNBA articles containing “{word}”, by {weekly ? 'week' : 'day'}" onpointerleave={() => (tip = null)}>
		{#each yTicks as t}
			<line class="grid" x1={PAD.left} x2={WIDTH - PAD.right} y1={yOf(t)} y2={yOf(t)} />
			{#if axis}<text class="axis" x={PAD.left - 6} y={yOf(t) + 4} text-anchor="end">{t}</text>{/if}
		{/each}
		{#each ticks as t}
			<line class="tick" x1={t.x} x2={t.x} y1={PAD.top + plotH} y2={PAD.top + plotH + 5} />
			<text class="axis" x={t.x} y={PAD.top + plotH + 18} text-anchor="start">{t.label}</text>
		{/each}
		<line class="baseline" x1={PAD.left} x2={WIDTH - PAD.right} y1={PAD.top + plotH} y2={PAD.top + plotH} />
		{#if axis && !small}
			<text class="axis-title" x={PAD.left} y={PAD.top - 8} text-anchor="start"
				>{unit === "mentions" ? "Mentions of the term, per week" : `Articles that mention the term, per ${weekly ? "week" : "day"}`}</text
			>
		{/if}
		{#if multi}
			{#each lines as l, j (l.word)}
				<path class="line" d={l.d} style="stroke:{l.color}" />
				{#if totals[j]}<text
					class="line-label"
					x={l.label.x}
					y={l.label.y}
					text-anchor={l.label.anchor}
					style="fill:{l.color}">{l.word} <tspan class="legend-n">{totals[j]} total {unit}</tspan></text
				>{/if}
			{/each}
			{#if tip}
				<!-- the point the card is about -->
				<circle class="point" cx={tip.cx} cy={yOf(tip.bin.each[tip.j])} r="4.5" style="fill:{entries[tip.j].color}" />
			{/if}
		{/if}
		{#each bins as bin, i (bin.start)}
			{#if !multi}
				<rect
					class="bar"
					class:lit={tip?.bin === bin}
					x={xOf(i) + 0.5}
					y={yOf(bin.hits)}
					width={Math.max(1, stepX - 1)}
					height={PAD.top + plotH - yOf(bin.hits)}
				/>
			{/if}
			<!-- a wide, invisible target, so the thin bars are hoverable -->
			<rect
				class="hit"
				x={xOf(i)}
				y={PAD.top}
				width={stepX}
				height={plotH}
				onpointerenter={(e) => show(e, bin, i)}
				onpointermove={(e) => show(e, bin, i)}
				role="presentation"
			/>
		{/each}
		{#if markX !== null}
			<line class="mark" x1={markX} x2={markX} y1={PAD.top - 2} y2={PAD.top + plotH} />
			{#if !small}
				<text class="mark-label" x={markX - 6} y={PAD.top - 8} text-anchor="end"
					>{String(markLabel).trim() || fmt(String(mark).trim())}</text
				>
			{/if}
		{/if}
		{#if !multi}
			<text class="total" x={WIDTH - PAD.right} y={PAD.top - 10} text-anchor="end"
				>{total.toLocaleString()} {unit === "mentions" ? "mentions of" : "articles say"} “{word}”</text
			>
		{/if}
	</svg>
	{#if tip}
		<div class="tip" style="left:{tip.x}px; top:{tip.y}px; border-left-color:{multi ? entries[tip.j].color : 'var(--color-fox)'}">
			<strong>{weekly ? weekLabel(tip.bin) : fmt(tip.bin.start)}</strong>
			{#if multi}
				<span class="stat lead" style="color:{entries[tip.j].color}"
					><span class="dot" style="background:{entries[tip.j].color}"></span>{entries[tip.j].word}: {tip.bin.each[tip.j]}
					{unit === "mentions" ? `mentions across ${tip.bin.articles} ${tip.bin.articles === 1 ? "article" : "articles"}` : `of ${tip.bin.articles} ${tip.bin.articles === 1 ? "article" : "articles"}`}</span
				>
				{#each entries as e, j (e.word)}
					{#if j !== tip.j && tip.bin.each[j]}
						<span class="stat muted"><span class="dot" style="background:{e.color}"></span>{e.word}: {tip.bin.each[j]}</span>
					{/if}
				{/each}
			{:else}
				<span class="stat">{tip.bin.hits} {unit === "mentions" ? "mentions across" : "of"} {tip.bin.articles} {tip.bin.articles === 1 ? "article" : "articles"}</span>
				{#if tip.bin.example}<span class="example">{tip.bin.example}</span>{/if}
			{/if}
		</div>
	{/if}
</div>

<style>
	.word-timeline {
		position: relative;
		max-width: 920px;
		margin: 6px auto 4px;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.bar {
		fill: var(--color-fox);
	}
	.bar.lit {
		fill: var(--color-ink);
	}
	.hit {
		fill: transparent;
	}
	.line {
		fill: none;
		stroke-width: 2;
		stroke-linejoin: round;
	}
	.line-label,
	.legend {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11.5px;
		font-weight: 700;
		paint-order: stroke;
		stroke: var(--color-bg, #f3b56b);
		stroke-width: 3px;
	}
	.legend-n {
		font-weight: 400;
		fill: rgba(42, 21, 3, 0.6);
	}
	.point {
		stroke: #fffdf8;
		stroke-width: 2;
		pointer-events: none;
	}
	.tip .lead {
		font-weight: 700;
	}
	.tip .dot {
		display: inline-block;
		width: 8px;
		height: 8px;
		border-radius: 50%;
		margin-right: 6px;
	}
	.tip .muted {
		color: rgba(42, 21, 3, 0.5);
	}
	.grid {
		stroke: rgba(42, 21, 3, 0.1);
	}
	.baseline,
	.tick {
		stroke: rgba(42, 21, 3, 0.45);
		stroke-width: 1;
	}
	.axis {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px;
		fill: rgba(42, 21, 3, 0.6);
	}
	.mark {
		stroke: var(--color-ink);
		stroke-width: 1.5;
		stroke-dasharray: 4 3;
	}
	.axis-title {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11.5px;
		fill: rgba(42, 21, 3, 0.6);
	}
	.mark-label,
	.total {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11.5px;
		font-weight: 700;
		fill: var(--color-ink);
	}
	.total {
		font-weight: 400;
		fill: rgba(42, 21, 3, 0.6);
	}
	.tip {
		position: absolute;
		transform: translate(-50%, calc(-100% - 12px));
		width: 280px;
		max-width: 80vw;
		background: var(--color-paper);
		color: var(--color-ink);
		border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid var(--color-fox);
		border-radius: 3px;
		box-shadow: 0 5px 20px rgba(42, 21, 3, 0.16);
		font-size: 12.5px;
		line-height: 1.4;
		padding: 9px 12px 10px;
		pointer-events: none;
		z-index: 6;
	}
	.tip strong {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11.5px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--color-ink);
	}
	.tip strong,
	.tip .stat,
	.tip .example {
		display: block;
	}
	.tip .stat {
		color: rgba(42, 21, 3, 0.7);
		margin-top: 2px;
	}
	.tip .example {
		margin-top: 5px;
		font-style: italic;
		color: var(--color-ink);
	}
</style>
