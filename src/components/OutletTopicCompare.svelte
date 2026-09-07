<script>
	// Small multiples: one yearly line per outlet, with the outlet's own
	// all-years average ruled across the panel and quoted beside its logo
	import { base } from "$app/paths";
	import rows from "$data/outlet_topics.csv";

	// `dots` is a leftover Doc prop from the logo dot plot this replaced
	// full text only; `method: headline` from the Doc would switch the source
	let { topic = "polrace", method = "body", dots = null } = $props();

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
	const AVG = "#1a1a1a"; // the average rule, apart from either topic colour

	// the outlets with panels (shown most-to-least by their all-years average)
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

	let byOutlet = $derived(data.topics[topic][method]);
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

	const pct = (share) => `${(share * 100).toFixed(share < 0.02 ? 1 : 0)}%`;

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

	// --- the reveal, once the block scrolls into view ------------------------
	// The panels come in one at a time, lowest average first: each dotted
	// average marches in while its chip unscrambles, then its year-line wipes
	// across. Fox News waits for a beat and comes last, alone.
	const STEP_MS = 550; // between one panel's start and the next
	const AVG_MS = 1000; // the march and the unscramble
	const BEAT_MS = 900; // the pause before Fox
	let started = $state(null);
	let elapsed = $state(0);
	let root = $state(null);
	let still = $state(false);
	$effect(() => {
		if (!root) return;
		if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
			still = true;
			return;
		}
		let raf;
		const io = new IntersectionObserver(
			(entries) => {
				if (!entries.some((e) => e.isIntersecting)) return;
				io.disconnect();
				started = performance.now();
				const frame = (now) => {
					elapsed = now - started;
					if (elapsed < lastStart + AVG_MS + 100)
						raf = requestAnimationFrame(frame);
				};
				raf = requestAnimationFrame(frame);
			},
			{ threshold: 0.35 }
		);
		io.observe(root);
		return () => {
			io.disconnect();
			cancelAnimationFrame(raf);
		};
	});
	// when each panel starts: the sports outlets from the lowest average up,
	// then a beat, then Fox
	let startAt = $derived.by(() => {
		const others = outlets.filter((o) => o !== FOX).toReversed();
		const at = {};
		others.forEach((o, i) => (at[o] = i * STEP_MS));
		if (outlets.includes(FOX)) at[FOX] = others.length * STEP_MS + BEAT_MS;
		return at;
	});
	let lastStart = $derived(Math.max(0, ...Object.values(startAt)));
	// a panel's stage and its chip's unscramble, from the clock
	const stageOf = (outlet) => {
		if (still) return "lines";
		if (started === null) return "blank";
		const t = elapsed - startAt[outlet];
		return t < 0 ? "blank" : t < AVG_MS ? "avg" : "lines";
	};
	const revealOf = (outlet) => {
		if (still) return 1;
		if (started === null) return 0;
		return Math.min(1, Math.max(0, (elapsed - startAt[outlet]) / AVG_MS));
	};
	const GLYPHS = "0123456789";
	// the digits settle left to right; letters and the % sign never scramble
	function scrambled(text, progress) {
		const settled = Math.floor(progress * text.length + 1e-6);
		return [...text]
			.map((c, i) =>
				i < settled || !/\d/.test(c)
					? c
					: GLYPHS[Math.floor(Math.random() * GLYPHS.length)]
			)
			.join("");
	}

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
	<div class="grid">
		{#each outlets as outlet, index (outlet)}
			{@const pts = lineFor(outlet)}
			{@const avg = overall(outlet)}
			{@const stage = stageOf(outlet)}
			{@const reveal = revealOf(outlet)}
			<div class="pane" class:fox={outlet === FOX} data-stage={stage}>
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
						<span
							class="avg-chip"
							class:blurred={reveal < 1}
							style="color:{AVG}"
							>{scrambled(`avg ${pct(avg.share)}`, reveal)}</span
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
						{#if +year % 2 === 0}
							<text
								class="tick year"
								x={xMid(index)}
								y={H - 6}
								text-anchor="middle">{year}</text
							>
						{/if}
					{/each}

					{#if avg}
						<!-- at its height from the start; a clip opening left to right
						     lets the dots march across the panel -->
						<clipPath id="march-{topic}-{method}-{index}">
							<rect
								class="march"
								x={M.left}
								y="0"
								width={plotW}
								height={H}
								style="transform-origin: {M.left}px 0; transform: scaleX({stage ===
								'blank'
									? 0
									: 1})"
							/>
						</clipPath>
						<line
							class="avg-line"
							clip-path="url(#march-{topic}-{method}-{index})"
							x1={M.left}
							x2={W - M.right}
							y1={pctY(avg.share)}
							y2={pctY(avg.share)}
							stroke={AVG}
						/>
					{/if}
					<!-- the line and its dots wipe in behind a clip that opens left to right -->
					<clipPath id="wipe-{topic}-{method}-{index}">
						<rect
							class="wipe"
							x={M.left}
							y="0"
							width={plotW}
							height={H}
							style="transform-origin: {M.left}px 0; transform: scaleX({stage ===
							'lines'
								? 1
								: 0})"
						/>
					</clipPath>
					<g clip-path="url(#wipe-{topic}-{method}-{index})">
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
	.otc {
		position: relative;
		max-width: 880px;
		margin: 6px auto 4px;
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
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
	.pane.fox {
		grid-column: 1 / -1;
		width: calc((100% - 44px) / 3);
		margin: 0 auto 6px;
	}
	.mobile .pane.fox {
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
		stroke-width: 2.4;
		stroke-linecap: round;
		stroke-dasharray: 1 5;
	}
	/* the average's march: its clip opens across the panel, steadily */
	.march {
		transition: transform 1000ms linear;
	}
	/* the wipe: a clip that opens across the years, left to right */
	.wipe {
		transition: transform 1800ms cubic-bezier(0.3, 0, 0.2, 1);
	}
	@media (prefers-reduced-motion: reduce) {
		.march,
		.wipe {
			transition: none;
		}
	}
	.avg-chip {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.02em;
		margin-left: 4px;
		font-variant-numeric: tabular-nums;
		transition: filter 700ms ease;
	}
	.avg-chip.blurred {
		filter: blur(2px);
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
