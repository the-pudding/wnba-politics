<script>
	// ---------------------------------------------------------------------------
	// Two yearly LINE charts side by side: the share of each outlet's WNBA
	// articles touching a topic. Fox on the left, a chooseable outlet on the
	// right, identical scales. Below, an optional one-axis dot plot places every
	// outlet's aggregate share as its logo.
	//
	// Patterns are identical to the fox_timeline topic columns, so the piece's
	// charts agree by construction. Years with fewer than 10 articles are
	// dropped rather than drawn as wild percentages.
	//
	// Doc embed:  chart: outlet-topics | topic: lgbtq | dots: lgbtq | title: …
	// ---------------------------------------------------------------------------
	import { base } from "$app/paths";
	import data from "$data/outlet_topics.json";

	let { topic = "polrace", dotsTopic = null } = $props();

	const FOX = "Fox News";
	const TOPIC_PHRASE = { lgbtq: "mention LGBTQ topics",
		all: "touch race, protest politics, or LGBTQ topics" }[topic]
		?? "mention race or protest politics";
	const MAIN = topic === "lgbtq"
		? "var(--c-lgbtq, #b04ac2)"
		: "var(--c-politics, #1f9d6e)";
	const MIN_N = 10;

	// logos with their natural aspect kept: width only, height follows —
	// forcing a square squashed the wide wordmarks (ESPN)
	const LOGOS = {
		"Fox News": { file: "fox-news.svg", w: 30 },
		"Fox News (NBA)": { file: "fox-news.svg", w: 30 },
		"Yahoo Sports (syndicated pool)": { file: "yahoo.svg", w: 52 },
		"ESPN": { file: "espn.svg", w: 48 },
		"Just Women's Sports": { file: "jws.png", w: 28 },
		"The Athletic": { file: "the-athletic.png", w: 28 },
		"CBS Sports": { file: "cbs-sports.svg", w: 48 },
		"USA Today": { file: "usa-today.svg", w: 56 }
	};
	const SHORT_NAME = {
		"Yahoo Sports (syndicated pool)": "Yahoo (pool)",
		"Just Women's Sports": "JWS",
		"Fox News (NBA)": "Fox (NBA)"
	};

	// full text where outlets have it; headlines to level the field. One mode
	// governs everything — a body rate next to a headline rate would
	// manufacture a gap, since the patterns hit bodies far more often.
	let method = $state("body");
	let outlets = $derived(data.topics[topic][method]);
	let others = $derived(Object.keys(outlets).filter((o) => o !== FOX));
	let against = $state("");
	$effect(() => {
		if (!others.includes(against))
			against = others.includes("Just Women's Sports") ? "Just Women's Sports" : others[0];
	});

	let viewportWidth = $state(typeof window === "undefined" ? 1200 : window.innerWidth);
	let mobile = $derived(viewportWidth < 640);

	// one shared year axis: every year either side can show
	let years = $derived([...new Set([
		...Object.entries(outlets[FOX]).filter(([, v]) => v.n >= MIN_N).map(([y]) => y),
		...Object.entries(outlets[against] ?? {}).filter(([, v]) => v.n >= MIN_N).map(([y]) => y)
	])].sort());

	// the axis fits the data, shared by both panels
	let yTop = $derived.by(() => {
		let peak = 0;
		for (const outlet of [FOX, against]) {
			for (const [, v] of Object.entries(outlets[outlet] ?? {})) {
				if (v.n >= MIN_N) peak = Math.max(peak, v.hit / v.n);
			}
		}
		for (const nice of [0.05, 0.1, 0.15, 0.2, 0.25, 0.5, 0.75, 1]) {
			if (nice >= peak * 1.05) return nice;
		}
		return 1;
	});

	const W = 420, H = 300;
	const M = { left: 46, right: 14, top: 26, bottom: 30 };
	const plotW = W - M.left - M.right;
	const plotH = H - M.top - M.bottom;
	let colW = $derived(plotW / Math.max(1, years.length));
	let pctY = $derived((pct) => M.top + plotH * (1 - pct / yTop));
	let xMid = $derived((index) => M.left + (index + 0.5) * colW);
	let yTicks = $derived([0.25, 0.5, 0.75, 1].map((f) => f * yTop));

	// the line: only years that clear the article floor
	function lineFor(outlet) {
		return years
			.map((year, index) => ({ year, index, v: (outlets[outlet] ?? {})[year] }))
			.filter(({ v }) => v && v.n >= MIN_N)
			.map((p) => ({ ...p, share: p.v.hit / p.v.n }));
	}
	const pathFor = (pts) =>
		pts.map((p, i) => `${i ? "L" : "M"}${xMid(p.index).toFixed(1)},${pctY(p.share).toFixed(1)}`).join("");

	let tip = $state(null);
	function showTip(event, outlet, year, v) {
		const box = event.currentTarget.closest(".otc").getBoundingClientRect();
		tip = { outlet, year, ...v,
			x: event.clientX - box.left,
			y: Math.min(Math.max(60, event.clientY - box.top), box.height - 60),
			flip: event.clientX - box.left > box.width - 250 };
	}

	// --- the logo dot plot: every outlet's aggregate share on one axis --------
	let dotOutlets = $derived.by(() => {
		if (!dotsTopic) return [];
		const src = data.topics[dotsTopic][method];
		const rows = [];
		for (const [name, yearsOf] of Object.entries(src)) {
			let n = 0, hit = 0;
			for (const v of Object.values(yearsOf)) { n += v.n; hit += v.hit; }
			if (n >= 50) rows.push({ name, n, hit, share: hit / n });
		}
		return rows.sort((a, b) => a.share - b.share);
	});
	let dotCap = $derived.by(() => {
		const peak = Math.max(0.02, ...dotOutlets.map((o) => o.share));
		for (const nice of [0.05, 0.1, 0.15, 0.2, 0.25, 0.5]) if (nice >= peak * 1.1) return nice;
		return 1;
	});
	// regular intervals from zero
	let dotStep = $derived(dotCap <= 0.05 ? 0.01 : dotCap <= 0.25 ? 0.05 : 0.1);
	let dotTicks = $derived.by(() => {
		const out = [];
		for (let t = 0; t <= dotCap + 1e-9; t += dotStep) out.push(t);
		return out;
	});
	const DW = 860;
	const DML = 24, DMR = 34;
	let dotX = $derived((share) => DML + (share / dotCap) * (DW - DML - DMR));

	// crowded logos stack VERTICALLY: each takes the lowest level where it
	// doesn't sit on a neighbour; a dashed leader keeps its true position
	const LEVEL_H = 34;
	let dotPlaced = $derived.by(() => {
		const placed = [];
		for (const o of dotOutlets) {
			const x = dotX(o.share);
			const w = LOGOS[o.name]?.w ?? 28;
			let level = 0;
			while (placed.some((q) => q.level === level &&
					Math.abs(q.x - x) < (q.w + w) / 2 + 6)) level++;
			placed.push({ ...o, x, w, level });
		}
		return placed;
	});
	let maxLevel = $derived(Math.max(0, ...dotPlaced.map((o) => o.level)));
	// the drawing grows to fit the tallest stack (+ room for the WNBA/NBA tags)
	let DH = $derived(96 + (maxLevel + 1) * 0 + maxLevel * LEVEL_H + 14);
	let dotMid = $derived(DH - 32);
	// the two Fox logos carry explicit league tags
	const LEAGUE_TAG = { "Fox News": "WNBA", "Fox News (NBA)": "NBA" };
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<div class="otc" class:mobile>
	<div class="method">
		<button class:on={method === "body"} onclick={() => (method = "body")}>FULL TEXT</button>
		<button class:on={method === "headline"} onclick={() => (method = "headline")}>HEADLINES</button>
	</div>
	<div class="panes">
		{#each [FOX, against] as outlet (outlet)}
			<div class="pane">
				{#if outlet === FOX}
					<div class="pane-hed">
						<img src="{base}/logos/{LOGOS[FOX].file}" alt="Fox News" style:height="24px" />
					</div>
				{:else}
					<div class="pane-hed">
						{#if LOGOS[outlet]}
							<img src="{base}/logos/{LOGOS[outlet].file}" alt={outlet} style:height="22px"
								style:filter={outlet === "Fox News (NBA)" ? "grayscale(1) opacity(0.75)" : ""} />
						{/if}
						<select class="picker" bind:value={against} aria-label="Compare outlet">
							{#each others as name}<option value={name}>{SHORT_NAME[name] ?? name}</option>{/each}
						</select>
					</div>
				{/if}
				<svg viewBox="0 0 {W} {H}" role="img"
					aria-label="Share of {outlet} WNBA articles that {TOPIC_PHRASE}, by year">
					{#each yTicks as pct}
						<line class="grid" x1={M.left} x2={W - M.right} y1={pctY(pct)} y2={pctY(pct)} />
						<text class="tick" x={M.left - 6} y={pctY(pct) + 4}
							text-anchor="end">{Math.round(pct * 100)}%</text>
					{/each}
					<line class="axis" x1={M.left} x2={W - M.right}
						y1={M.top + plotH} y2={M.top + plotH} />
					{#each lineFor(outlet) as p (p.year)}
						<!-- invisible full-height hover column per year -->
						<rect x={M.left + p.index * colW} width={colW} y={M.top} height={plotH}
							fill="transparent"
							onpointermove={(e) => showTip(e, outlet, p.year, p.v)}
							onpointerleave={() => (tip = null)} />
					{/each}
					<path class="topic-line" d={pathFor(lineFor(outlet))} stroke={MAIN} />
					{#each lineFor(outlet) as p (p.year)}
						<circle cx={xMid(p.index)} cy={pctY(p.share)} r="4" fill={MAIN}
							onpointermove={(e) => showTip(e, outlet, p.year, p.v)}
							onpointerleave={() => (tip = null)} />
						<text class="tick year" x={xMid(p.index)} y={H - 10}
							text-anchor="middle">{"’" + p.year.slice(2)}</text>
					{/each}
				</svg>
			</div>
		{/each}
	</div>

	{#if dotsTopic && dotOutlets.length}
		<div class="dots-hed">Every outlet, all years since 2019</div>
		<svg class="dots" viewBox="0 0 {DW} {DH}" role="img"
			aria-label="Each outlet's overall share of articles touching the topic">
			<line x1={DML} x2={DW - DMR} y1={dotMid} y2={dotMid} class="axis" />
			{#each dotTicks as t}
				<line x1={dotX(t)} x2={dotX(t)} y1={dotMid - 5} y2={dotMid + 5} class="axis" />
				<text class="tick" x={dotX(t)} y={dotMid + 22} text-anchor="middle">{Math.round(t * 100)}%</text>
			{/each}
			{#each dotPlaced as o (o.name)}
				{@const y = dotMid - 34 - o.level * LEVEL_H}
				{#if o.level > 0}
					<line x1={o.x} x2={o.x} y1={y + 30} y2={dotMid} class="leader" />
				{/if}
				<image href="{base}/logos/{LOGOS[o.name]?.file}"
					x={o.x - o.w / 2} y={y} width={o.w}
					style={o.name === "Fox News (NBA)" ? "filter: grayscale(1) opacity(0.75)" : ""}
					onpointermove={(e) => showTip(e, SHORT_NAME[o.name] ?? o.name, "2019–2026", o)}
					onpointerleave={() => (tip = null)} />
				{#if LEAGUE_TAG[o.name]}
					<text class="tick league-tag" x={o.x} y={y - 5} text-anchor="middle">{LEAGUE_TAG[o.name]}</text>
				{/if}
			{/each}
		</svg>
	{/if}

	{#if tip}
		<div class="tooltip" class:flip={tip.flip} style="left:{tip.x}px; top:{tip.y}px">
			<strong>{tip.outlet} · {tip.year}</strong>
			<p class="line">{tip.hit} of {tip.n.toLocaleString()}
				{method === "headline" ? "headlines" : "articles"} —
				{(tip.hit / tip.n * 100).toFixed(tip.hit / tip.n < 0.02 ? 1 : 0)}% —
				{TOPIC_PHRASE}.</p>
		</div>
	{/if}
</div>

<style>
	.otc { position: relative; max-width: 880px; margin: 6px auto 4px; }
	.method {
		display: flex; justify-content: center; margin-bottom: 8px;
		border-radius: 6px; overflow: hidden; width: fit-content;
		margin-left: auto; margin-right: auto;
		border: 1.5px solid #2a1503;
	}
	.method button {
		border: 0; background: #fffdf8; color: #2a1503; padding: 6px 13px;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12px; font-weight: 700; cursor: pointer;
	}
	.method button.on { background: #2a1503; color: #fffdf8; }
	.panes { display: flex; gap: 18px; }
	.pane { flex: 1 1 0; min-width: 0; }
	.mobile .panes { flex-direction: column; }
	svg { width: 100%; height: auto; display: block; overflow: visible; }

	.pane-hed {
		display: flex; align-items: center; justify-content: center; gap: 8px;
		height: 30px; margin-bottom: 4px;
	}
	.picker {
		border: 1px solid rgba(42, 21, 3, 0.3); border-radius: 4px;
		background: #fffdf8; padding: 3px 6px; font-size: 12.5px;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
	}

	.grid { stroke: rgba(42, 21, 3, 0.35); stroke-width: 1; }
	.axis { stroke: #2a1503; stroke-width: 1.5; }
	.tick { font-size: 13.5px; fill: #2a1503; }
	.mobile .tick { font-size: 16px; }
	.topic-line { fill: none; stroke-width: 2.8; stroke-linejoin: round; stroke-linecap: round; }

	.dots-hed {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 13px; font-weight: 700; color: #2a1503;
		text-align: center; margin: 18px 0 2px;
	}
	.dots { overflow: visible; }
	.leader { stroke: rgba(42, 21, 3, 0.35); stroke-width: 1; stroke-dasharray: 2 3; }
	.league-tag { font-weight: 800; font-size: 12px; }

	.tooltip {
		position: absolute; transform: translate(14px, -50%);
		width: 230px;
		background: #fffdf8; border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid rgba(42, 21, 3, 0.35); border-radius: 3px;
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
	.tooltip .line { margin: 5px 0 0; font-size: 13px; line-height: 1.5; color: #2a1503;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }
</style>
