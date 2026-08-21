<script>
	// Fox WNBA articles per month. Two charts: timeline-clark (cream WNBA bars,
	// Clark layer, optional NBA backdrop) and timeline-griner (Griner and Clark
	// overlaid from the baseline). Hover a month for counts and an example per category.
	// Doc embed: chart: timeline-clark | nba: true | caption: …
	import foxTimeline from "$data/fox_timeline.json";
	import nbaMonthly from "$data/fox_nba_monthly.json";
	import { niceTicks, yearTicks } from "../utils/chartAxis.js";

	let { name = "timeline-clark", from = null, to = null, nba = false } = $props();

	const PLAYERS = { clark: "Caitlin Clark", griner: "Brittney Griner" };
	const col = (key) => foxTimeline.topics.length + foxTimeline.players.indexOf(PLAYERS[key]);
	const LAYERS = name === "timeline-griner"
		? [{ key: "griner", label: "Brittney Griner", color: "var(--color-griner)" },
			{ key: "clark", label: "Caitlin Clark", color: "var(--color-clark)" }]
		: [{ key: "clark", label: "mentions Caitlin Clark", color: "var(--color-clark)" }];

	const nbaCount = Object.fromEntries(nbaMonthly.months.map((m, i) => [m, nbaMonthly.counts[i]]));
	const nbaExample = nbaMonthly.ex ?? {};

	let months = $derived(foxTimeline.months
		.filter((r) => (!from || r.month >= from) && (!to || r.month <= to))
		.map((r) => ({
			month: r.month, articles: r.n, example: r.ex ?? "",
			counts: Object.fromEntries(LAYERS.map((l) => [l.key, r.t[col(l.key)] ?? 0])),
			headlines: Object.fromEntries(LAYERS.map((l) =>
				[l.key, r.thed?.[col(l.key)] || r.tex?.[col(l.key)] || ""]))
		})));

	// mobile gets its own drawing: fewer units wide, so type renders larger
	let viewportWidth = $state(typeof window === "undefined" ? 1200 : window.innerWidth);
	let mobile = $derived(viewportWidth < 640);
	let WIDTH = $derived(mobile ? 480 : 860);
	let HEIGHT = $derived(mobile ? 440 : 360);
	let margin = $derived(mobile
		? { left: 54, right: 8, top: 34, bottom: 34 }
		: { left: 44, right: 14, top: 30, bottom: 30 });
	let plotWidth = $derived(WIDTH - margin.left - margin.right);
	let plotHeight = $derived(HEIGHT - margin.top - margin.bottom);
	let barWidth = $derived(plotWidth / Math.max(1, months.length));

	let yMax = $derived(Math.max(1, ...months.map((m) => m.articles),
		...(nba ? months.map((m) => nbaCount[m.month] ?? 0) : [0])));
	let barHeight = $derived((count) => (count / yMax) * plotHeight);

	let xTicks = $derived(yearTicks(months));
	let yTicks = $derived(niceTicks(yMax));

	const MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
		"July", "August", "September", "October", "November", "December"];
	const monthLabel = (m) => `${MONTH_NAMES[Number(m.slice(5, 7)) - 1]} ${m.slice(0, 4)}`;
	// some stored sentences arrive already quoted; strip or the card opens ““
	const unquote = (t) => t.replace(/^[\s"“”']+/, "").replace(/[\s"“”']+$/, "");

	// the segment under the pointer names itself: its category, count, example
	let tooltip = $state(null);
	function showTooltip(event, month, label, color, n, quote) {
		const box = event.currentTarget.closest(".timeline-chart").getBoundingClientRect();
		tooltip = { month: monthLabel(month.month), label, color, n, quote,
			x: event.clientX - box.left,
			y: Math.min(Math.max(70, event.clientY - box.top), box.height - 70),
			flip: event.clientX - box.left > box.width - 330 };
	}
	const hideTooltip = () => (tooltip = null);
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<div class="timeline-chart" class:mobile>
	<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img"
		aria-label="Fox News WNBA articles per month, with the share that {LAYERS[0].label}">
		<g transform="translate({margin.left},{margin.top})">

			{#each yTicks as tick}
				<line x1="0" x2={plotWidth} y1={plotHeight - barHeight(tick)} y2={plotHeight - barHeight(tick)} class="grid" />
				<text x="-8" y={plotHeight - barHeight(tick) + 4} text-anchor="end" class="tick">{tick}</text>
			{/each}

			{#each months as month, index (month.month)}
				{@const x = index * barWidth + 1.5}
				{@const width = Math.max(1, barWidth - 3)}

				{#if nba && month.month >= nbaMonthly.from}
					{@const nbaH = barHeight(nbaCount[month.month] ?? 0)}
					<rect class="nba-bar" x={x - 0.5} width={Math.max(1, barWidth - 1)}
						y={plotHeight - nbaH} height={nbaH} />
					<!-- hover only where the black is actually visible above the WNBA bar -->
					{#if nbaH > barHeight(month.articles)}
						<rect fill="transparent" x={x - 0.5} width={Math.max(1, barWidth - 1)}
							y={plotHeight - nbaH} height={nbaH - barHeight(month.articles)}
							onmousemove={(e) => showTooltip(e, month, "NBA", "var(--color-nba)",
								nbaCount[month.month] ?? 0, nbaExample[month.month] ?? "")}
							onmouseleave={hideTooltip} />
					{/if}
				{/if}

				<rect {x} {width} fill="var(--color-cream)"
					y={plotHeight - barHeight(month.articles)} height={barHeight(month.articles)}
					onmousemove={(e) => showTooltip(e, month, "WNBA", "var(--color-cream)",
						month.articles, month.example)}
					onmouseleave={hideTooltip} />

				<!-- overlay, not a stack: an article can mention both players -->
				{#each LAYERS as layer}
					<rect {x} {width} fill={layer.color}
						y={plotHeight - barHeight(month.counts[layer.key])}
						height={barHeight(month.counts[layer.key])}
						onmousemove={(e) => showTooltip(e, month, PLAYERS[layer.key], layer.color,
							month.counts[layer.key], month.headlines[layer.key])}
						onmouseleave={hideTooltip} />
				{/each}
			{/each}

			<line x1="0" x2={plotWidth} y1={plotHeight} y2={plotHeight} class="axis" />
			{#each xTicks as tick}
				<text x={tick.index * barWidth} y={plotHeight + 18} class="tick">{tick.year}</text>
			{/each}

			<g transform="translate(0,-14)" class="legend">
				{#each [...(nba ? [{ label: "NBA", color: "var(--color-nba)" }] : []),
					{ label: "WNBA", color: "var(--color-cream)", stroke: "rgba(42,21,3,0.25)" },
					...LAYERS] as item, i}
					{@const offset = mobile ? 8.6 : 6.8}
					{@const x = [...(nba ? [{ label: "NBA" }] : []), { label: "WNBA" }, ...LAYERS]
						.slice(0, i).reduce((sum, prev) => sum + 34 + prev.label.length * offset, 0)}
					<rect {x} y="0" width="12" height="12" fill={item.color} stroke={item.stroke ?? "none"} />
					<text x={x + 17} y="10">{item.label}</text>
				{/each}
			</g>
		</g>
	</svg>

	{#if tooltip}
		<div class="tooltip" class:flip={tooltip.flip}
			style="left:{tooltip.x}px; top:{tooltip.y}px; border-left-color:{tooltip.color}">
			<strong>{tooltip.month}</strong>
			<div class="row">
				<span class="dot" style="background:{tooltip.color}"></span>
				<span class="who">{tooltip.label}</span>
				<span class="n">{tooltip.n.toLocaleString()} {tooltip.n === 1 ? "article" : "articles"}</span>
			</div>
			{#if tooltip.quote}<div class="example">“{unquote(tooltip.quote)}”</div>{/if}
		</div>
	{/if}
</div>

<style>
	rect { transition: height 500ms ease, y 500ms ease, x 500ms ease, width 500ms ease; }
	.nba-bar { fill: var(--color-nba); pointer-events: none; }

	.timeline-chart { position: relative; width: 100%; margin: 6px auto 18px; }
	svg { width: 100%; height: auto; }

	.grid { stroke: rgba(42, 21, 3, 0.14); stroke-width: 1; }
	.axis { stroke: rgba(42, 21, 3, 0.35); stroke-width: 1; }
	.tick { font-size: 12px; fill: rgba(42, 21, 3, 0.6); }
	.legend text { font-size: 12.5px; fill: rgba(42, 21, 3, 0.75); }

	/* the 480-unit mobile drawing renders these ~1.8x larger */
	.mobile .tick { font-size: 17px; }
	.mobile .legend text { font-size: 15px; }

	.tooltip {
		position: absolute;
		transform: translate(14px, -50%);
		width: 300px;
		background: var(--color-paper);
		border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid var(--color-ink);
		border-radius: 3px;
		color: var(--color-ink);
		font-size: 12.5px;
		line-height: 1.45;
		padding: 9px 12px 10px;
		box-shadow: 0 5px 20px rgba(42, 21, 3, 0.16);
		pointer-events: none;
		z-index: 5;
	}
	.tooltip.flip { transform: translate(calc(-100% - 14px), -50%); }
	.tooltip strong {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11.5px; font-weight: 700; letter-spacing: 0.06em;
		text-transform: uppercase;
	}
	.row { display: flex; align-items: baseline; gap: 6px; margin-top: 6px; }
	.dot { width: 9px; height: 9px; border-radius: 2px; border: 1px solid rgba(42, 21, 3, 0.25); flex: none; align-self: center; }
	.who { font-weight: 700; }
	.n { color: rgba(42, 21, 3, 0.55); font-size: 11.5px; margin-left: auto; font-variant-numeric: tabular-nums; }
	.example { margin: 2px 0 0 15px; font-size: 12.5px; line-height: 1.45; color: rgba(42, 21, 3, 0.85); }
</style>
