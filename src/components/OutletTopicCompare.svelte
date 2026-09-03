<script>
	// Small multiples: one yearly line per outlet, with the average of the
	// non-Fox outlets drawn in every panel for reference
	import { base } from "$app/paths";
	import rows from "$data/outlet_topics.csv";

	// `dots` is a leftover Doc prop from the logo dot plot this replaced
	let { topic = "polrace", method: start = "body", dots = null } = $props();

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
			: "mention race or protest politics";
	const MAIN =
		topic === "lgbtq" ? "var(--color-lgbtq)" : "var(--color-politics)";
	const MIN_N = 10;

	// panel order: Fox first, then its NBA baseline, then the sports press
	const ORDER = [
		FOX,
		NBA,
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

	let method = $state(start);
	let byOutlet = $derived(data.topics[topic][method]);
	// The Athletic, CBS and USA Today are headline-only corpora, so they have no
	// full-text panel
	let outlets = $derived(ORDER.filter((o) => byOutlet[o]));

	let years = $derived(
		[
			...new Set(
				outlets.flatMap((o) =>
					Object.entries(byOutlet[o])
						.filter(([, v]) => v.n >= MIN_N)
						.map(([y]) => y)
				)
			)
		].sort()
	);

	function lineFor(outlet) {
		return years
			.map((year, index) => ({ year, index, v: byOutlet[outlet]?.[year] }))
			.filter(({ v }) => v && v.n >= MIN_N)
			.map((p) => ({ ...p, share: p.v.hit / p.v.n }));
	}

	// the reference line: the unweighted mean, each year, of the sports outlets'
	// shares — Fox (and its NBA baseline) left out, so Fox is measured against
	// everyone else
	let average = $derived.by(() => {
		const pts = [];
		years.forEach((year, index) => {
			const shares = outlets
				.filter((o) => o !== FOX && o !== NBA)
				.map((o) => byOutlet[o]?.[year])
				.filter((v) => v && v.n >= MIN_N)
				.map((v) => v.hit / v.n);
			if (shares.length >= 2)
				pts.push({
					year,
					index,
					share: shares.reduce((a, b) => a + b, 0) / shares.length,
					count: shares.length
				});
		});
		return pts;
	});

	// one y scale for every panel, so the lines are comparable at a glance
	let yTop = $derived.by(() => {
		let peak = 0;
		for (const outlet of outlets)
			for (const p of lineFor(outlet)) peak = Math.max(peak, p.share);
		// tops whose halves are round numbers, since the ticks sit at ½ and 1
		for (const nice of [0.02, 0.04, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1])
			if (nice >= peak * 1.05) return nice;
		return 1;
	});

	let viewportWidth = $state(
		typeof window === "undefined" ? 1200 : window.innerWidth
	);
	let mobile = $derived(viewportWidth < 640);

	const W = 220,
		H = 150;
	const M = { left: 34, right: 8, top: 10, bottom: 22 };
	const plotW = W - M.left - M.right;
	const plotH = H - M.top - M.bottom;
	let colW = $derived(plotW / Math.max(1, years.length));
	let pctY = $derived((pct) => M.top + plotH * (1 - pct / yTop));
	let xMid = $derived((index) => M.left + (index + 0.5) * colW);
	let yTicks = $derived([0.5, 1].map((f) => f * yTop));

	const pathFor = (pts) =>
		pts
			.map(
				(p, i) =>
					`${i ? "L" : "M"}${xMid(p.index).toFixed(1)},${pctY(p.share).toFixed(1)}`
			)
			.join("");

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

<div class="otc" class:mobile>
	<div class="method">
		<button class:on={method === "body"} onclick={() => (method = "body")}
			>FULL TEXT</button
		>
		<button
			class:on={method === "headline"}
			onclick={() => (method = "headline")}>HEADLINES</button
		>
	</div>
	<div class="key">
		<span class="swatch line" style="background:{MAIN}"></span> this outlet
		<span class="swatch avg"></span> average of the other sports outlets
	</div>

	<div class="grid">
		{#each outlets as outlet (outlet)}
			{@const pts = lineFor(outlet)}
			<div class="pane" class:fox={outlet === FOX}>
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
						<text
							class="tick"
							x={M.left - 5}
							y={pctY(pct) + 4}
							text-anchor="end">{Math.round(pct * 100)}%</text
						>
					{/each}
					<line
						class="axis"
						x1={M.left}
						x2={W - M.right}
						y1={M.top + plotH}
						y2={M.top + plotH}
					/>
					{#each years as year, index}
						<text
							class="tick year"
							x={xMid(index)}
							y={H - 6}
							text-anchor="middle">{"’" + year.slice(2)}</text
						>
					{/each}

					<path class="avg-line" d={pathFor(average)} />
					<path class="topic-line" d={pathFor(pts)} stroke={MAIN} />
					{#each pts as p (p.year)}
						<circle cx={xMid(p.index)} cy={pctY(p.share)} r="3" fill={MAIN} />
					{/each}
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

	{#if tip}
		{@const avg = average.find((p) => p.year === tip.year)}
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
					The {avg.count} other sports outlets averaged {(
						avg.share * 100
					).toFixed(avg.share < 0.02 ? 1 : 0)}% that year.
				{/if}
			</p>
		</div>
	{/if}
</div>

<style>
	.otc {
		position: relative;
		max-width: 880px;
		margin: 6px auto 4px;
	}
	.method {
		display: flex;
		justify-content: center;
		margin-bottom: 8px;
		border-radius: 6px;
		overflow: hidden;
		width: fit-content;
		margin-left: auto;
		margin-right: auto;
	}
	.method button {
		border: 0;
		background: var(--color-paper);
		color: var(--color-ink);
		padding: 6px 13px;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12px;
		font-weight: 700;
		cursor: pointer;
	}
	.method button.on,
	.method button:hover {
		background: var(--color-ink);
		color: var(--color-paper);
	}
	.key {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 6px;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11.5px;
		color: rgba(42, 21, 3, 0.7);
		margin-bottom: 10px;
	}
	.key .swatch {
		display: inline-block;
		width: 18px;
		height: 3px;
		border-radius: 2px;
	}
	.key .swatch.avg {
		margin-left: 10px;
		height: 0;
		border-top: 2px dashed rgba(42, 21, 3, 0.55);
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 14px 16px;
	}
	.mobile .grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 12px 10px;
	}
	.pane {
		min-width: 0;
	}
	.pane.fox svg {
		background: rgba(255, 253, 248, 0.35);
		border-radius: 4px;
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
		stroke: rgba(42, 21, 3, 0.22);
		stroke-width: 1;
	}
	.axis {
		stroke: var(--color-ink);
		stroke-width: 1.2;
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
	.avg-line {
		fill: none;
		stroke: rgba(42, 21, 3, 0.55);
		stroke-width: 1.6;
		stroke-dasharray: 4 3;
		stroke-linejoin: round;
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
