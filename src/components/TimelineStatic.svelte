<script>
	// ---------------------------------------------------------------------------
	// One bar chart: Fox News WNBA articles per month.
	//
	// Cream bars are ALL articles in that month. On top of them we stack colored
	// "layers" — e.g. the share of those articles that mention Caitlin Clark.
	// Which layers appear is decided by the `chartName` prop, so every timeline
	// figure in the story is this one component with a different setting.
	//
	// Written from a Google Doc line like:   chart: timeline-griner | years: 2022
	//
	// Svelte notes for a Python reader:
	//   * Code in <script> runs once when the component is created, like __init__.
	//   * $props() are the arguments the parent passed in (like keyword args).
	//   * $state(x) marks a variable that re-renders the page when reassigned.
	//   * The markup below is HTML plus {#each ...} loops and {#if ...} branches.
	//   * The style rules at the bottom apply only to this component.
	// ---------------------------------------------------------------------------
	import foxTimeline from "$data/fox_timeline.json";
	import nbaMonthly from "$data/fox_nba_monthly.json";
	import { niceTicks, yearTicks } from "../utils/chartAxis.js";

	let {
		chartName = "timeline-full", // which chart to draw (see CHART_TYPES below)
		startMonth = null,           // optional "2020-01" lower bound
		endMonth = null,             // optional "2023-12" upper bound
		// Reveals the chart a year at a time. The x-axis keeps its full range so
		// the bars grow rightward into empty space rather than re-fitting, and the
		// y-axis is scaled to what has been revealed — which is the point, because
		// each new year flattens the ones before it.
		revealUntil = null,
		// Fox's NBA articles as pale columns behind the WNBA bars — the control
		// that says whether Fox found women's basketball or just basketball.
		// Doc line:  chart: timeline-clark | nba: true
		showNBA = false,
		// A scrolly beat can pin the y-axis low (e.g. 10) so the early, small
		// bars are legible, then release it on the next beat — the rescale is the
		// story: the same bars shrink as 2026 towers over them.
		yCap = null,
		// Pudding-style mobile scrollytelling: the chart fills the phone screen
		// instead of sitting as a ribbon in the middle. Set by TimelineScrolly;
		// only takes effect at phone widths.
		tall = false
	} = $props();

	// month -> NBA article count, from Fox's own NBA tag feeds (the same
	// standard the WNBA corpus was built on). Months before the harvest floor
	// (2016) are absent-not-zero, though the chart axis never reaches them.
	const NBA_FROM = nbaMonthly.from;
	const nbaByMonth = Object.fromEntries(
		nbaMonthly.months.map((m, i) => [m, nbaMonthly.counts[i]]));

	// Keys only — every VALUE lives in the style block at the bottom,
	// Pudding-style, where it can be tweaked next to the rest of the design.
	const COLORS = {
		allArticles: "var(--tl-cream)",
		allArticlesPct: "var(--tl-pct-bar)",
		clark: "var(--tl-clark)",
		griner: "var(--tl-griner)",
		politics: "var(--tl-politics)",
		race: "var(--tl-race)",
		polrace: "var(--tl-politics)",   // the union band wears the protest green
		lgbtq: "var(--tl-lgbtq)",
		polOnly: "var(--tl-politics)",
		polAndLgbtq: "var(--tl-both)",
		lgbtqOnly: "var(--tl-lgbtq)",
		trans: "var(--tl-trans)"
	};

	// The data file keeps one number per month per topic/player, all in a flat
	// list called "t". These are the positions of the ones we care about.
	const columnOf = {
		politics: foxTimeline.topics.indexOf("politics / protest"),
		race: foxTimeline.topics.indexOf("race / racism"),
		// the union columns: an article touching both counts once
		polrace: foxTimeline.topics.indexOf("politics or race"),
		pollgbtq: foxTimeline.topics.indexOf("politics or LGBTQ"),
		allthree: foxTimeline.topics.indexOf("politics or race or LGBTQ"),
		lgbtq: foxTimeline.topics.indexOf("LGBTQ / sexuality"),
		trans: foxTimeline.topics.indexOf("transgender / trans"),
		// players are stored after the topics in that same list
		griner: foxTimeline.topics.length + foxTimeline.players.indexOf("Brittney Griner"),
		clark: foxTimeline.topics.length + foxTimeline.players.indexOf("Caitlin Clark")
	};

	// Each chart is a list of colored layers to stack on the cream bars.
	// `ownScale: true` means the y-axis fits the layer instead of the article
	// total — useful when a layer is tiny (a handful of articles a month).
	const CHART_TYPES = {
		"timeline-full": { layers: [] },
		"timeline-clark": { layers: [{ key: "clark", label: "mention Caitlin Clark", legend: "mentions Caitlin Clark" }] },
		// After the first (count) timeline establishes scale, the later ones are
		// 100% charts: every month's bar is its whole output, and the question
		// shifts from "how much coverage" to "how much OF the coverage".
		// the main-character handoff: Griner's era and Clark's, drawn from the
		// same baseline (overlay, not a stack — an article can mention both)
		"timeline-griner": {
			overlay: true,
			layers: [
				{ key: "griner", label: "mention Brittney Griner", legend: "Brittney Griner" },
				{ key: "clark", label: "mention Caitlin Clark", legend: "Caitlin Clark" }
			]
		},
		// protest and race read as one story — the 2020 walkouts, the Jacob Blake
		// shirts, the coverage that followed — so they are ONE band: the union,
		// not a stack (13% of these articles match both and would count twice)
		"timeline-protest": {
			percent: true,
			hatch: "griner",
			layers: [
				{ key: "polrace", label: "touch protest politics or race", legend: "protest politics or race" }
			]
		},
		// a THREE-WAY split: politics-only, both, LGBTQ-only. The bands are
		// mutually exclusive, so the stack is honest — it sums to exactly the
		// share touching either topic, and June 2020 no longer clips.
		"timeline-lgbtq": {
			percent: true,
			hatch: "griner",
			layers: [
				{ key: "polOnly", ex: "politics", label: "touch race / protest politics only", legend: "race + protest" },
				{ key: "polAndLgbtq", ex: "lgbtq", label: "touch both", legend: "both" },
				{ key: "lgbtqOnly", ex: "lgbtq", label: "touch LGBTQ / sexuality only", legend: "LGBTQ / sexuality" }
			]
		},
		"timeline-politics": {
			// The 2022 spike is the detainment, not a turn toward politics, so
			// mark the Griner share of every bar rather than leaving it to be
			// misread as protest coverage.
			hatch: "griner",
			layers: [
				{ key: "politics", label: "touch protest politics" },
				{ key: "race", label: "are about race" },
				{ key: "lgbtq", label: "touch LGBTQ / sexuality" }
			]
		},
		"timeline-trans": { layers: [{ key: "trans", label: "are trans-related" }], ownScale: true }
	};
	const chart = CHART_TYPES[chartName] ?? CHART_TYPES["timeline-full"];

	// resolve a layer key to a monthly count — the three-way LGBTQ split is
	// derived from the unions rather than stored: the base band is the SAME
	// race+protest union as the previous chart, so the two figures agree
	function countOf(t, key) {
		if (key === "polOnly" || key === "lgbtqOnly" || key === "polAndLgbtq") {
			const polrace = t[columnOf.polrace] ?? 0;
			const lgb = t[columnOf.lgbtq] ?? 0;
			const union = t[columnOf.allthree] ?? 0;
			const both = Math.max(0, polrace + lgb - union);
			return key === "polAndLgbtq" ? both : key === "polOnly" ? polrace - both : lgb - both;
		}
		return t[columnOf[key]] ?? 0;
	}

	// --- the rows we will draw --------------------------------------------------
	// derived, not const: a scrolly beat may re-window the x-axis (from/to), so
	// everything downstream of the month list has to follow it
	let allMonths = $derived(foxTimeline.months
		.filter((row) => (!startMonth || row.month >= startMonth) && (!endMonth || row.month <= endMonth))
		.map((row) => ({
			month: row.month,
			articles: row.n,
			example: row.ex ?? "",
			// per-layer counts, plus one real headline to show on hover.
			// The three-way keys are derived: both = politics + lgbtq - union.
			counts: Object.fromEntries(chart.layers.map((l) => [l.key, countOf(row.t, l.key)])),
			hatched: chart.hatch ? (row.t[columnOf[chart.hatch]] ?? 0) : 0,
			hatchExample: chart.hatch ? (row.tex?.[columnOf[chart.hatch]] ?? "") : "",
			hatchHeadline: chart.hatch ? (row.thed?.[columnOf[chart.hatch]] ?? "") : "",
			examples: Object.fromEntries(chart.layers.map((l) => [l.key, row.tex?.[columnOf[l.ex ?? l.key]] ?? ""])),
			headlines: Object.fromEntries(chart.layers.map((l) => [l.key, row.thed?.[columnOf[l.ex ?? l.key]] ?? ""]))
		})));
	// what is on screen right now; the axis still spans every month
	let months = $derived(revealUntil
		? allMonths.filter((row) => row.month <= revealUntil)
		: allMonths);

	// --- geometry (an SVG drawing scaled to fit by CSS) --------------------------
	// On a phone the 860-unit drawing shrinks ~2.4x, which crushes the chart to a
	// ribbon and the axis type to fly print. Mobile gets its own drawing: fewer
	// units wide (so every unit — and every letter — renders larger) and taller.
	let viewportWidth = $state(typeof window === "undefined" ? 1200 : window.innerWidth);
	let mobile = $derived(viewportWidth < 640);
	let WIDTH = $derived(mobile ? 480 : 860);
	// tall = Pudding-style: inside a scrolly on a phone, the drawing is nearly twice
	// as high as wide, so the sticky chart fills the screen
	let HEIGHT = $derived(mobile ? (tall ? 880 : 440) : 360);
	let margin = $derived(mobile
		? { left: 54, right: 8, top: 34, bottom: 34 }
		: { left: 44, right: 14, top: 30, bottom: 30 });
	let plotWidth = $derived(WIDTH - margin.left - margin.right);
	let plotHeight = $derived(HEIGHT - margin.top - margin.bottom);
	let barWidth = $derived(plotWidth / Math.max(1, allMonths.length));

	// The tallest thing on the chart sets the y-scale.
	// Scaled to the whole series, not to what's revealed: a fixed axis lets the
	// reader watch the bars arrive against a constant reference, where a
	// rescaling one re-draws the meaning of the same height at every step.
	let layerMax = $derived(Math.max(1, ...allMonths.map((m) => Math.max(0, ...Object.values(m.counts)))));
	let articleMax = $derived(Math.max(1, ...allMonths.map((m) => m.articles),
		...(showNBA ? nbaMonthly.counts : [0])));
	// reactive now: a scrolly beat can override the axis via yCap
	let yMax = $derived(yCap ?? (chart.ownScale ? layerMax : articleMax));

	// count -> pixel height, clamped so bars taller than a capped axis peg to the
	// top rather than escaping the plot
	let barHeight = $derived((count) => Math.min(plotHeight, (count / yMax) * plotHeight));

	// In percent mode heights are shares of the month's own total, and the
	// y-axis is a fixed 0–100%.
	let pctHeight = $derived((count, total) =>
		total ? Math.min(plotHeight, (count / total) * plotHeight) : 0);
	const PCT_TICKS = [25, 50, 75, 100];

	let xTicks = $derived(yearTicks(allMonths));
	let yTicks = $derived(chart.percent ? PCT_TICKS : niceTicks(yMax));
	let tickY = $derived((tick) => chart.percent
		? plotHeight * (1 - tick / 100)
		: plotHeight - barHeight(tick));

	// Stack one month's layers so they sit on each other and never exceed the
	// month's article total. Returns the pieces ready to draw.
	// In overlay mode they don't stack at all: every band rises from the
	// baseline at its true share, later layers drawn in front of earlier ones —
	// so overlapping topics can both be read without clipping.
	function stackedLayers(monthRow) {
		if (chart.overlay) {
			return chart.layers
				.filter((layer) => monthRow.counts[layer.key] > 0)
				.map((layer) => ({ ...layer, value: monthRow.counts[layer.key], bottom: 0 }));
		}
		let used = 0;
		const pieces = [];
		for (const layer of chart.layers) {
			const room = chart.ownScale ? Infinity : Math.max(0, monthRow.articles - used);
			const value = Math.min(monthRow.counts[layer.key], room);
			if (value > 0) pieces.push({ ...layer, value, bottom: used });
			used += value;
		}
		return pieces;
	}

	// --- tooltip ---------------------------------------------------------------
	let tooltip = $state(null); // null, or {x, y, html}

	function showTooltip(event, html, color = "#2a1503") {
		const box = event.currentTarget.closest(".timeline-chart").getBoundingClientRect();
		tooltip = {
			x: event.clientX - box.left,
			// clamped so the card can't slide off the top or bottom of the figure
			y: Math.min(Math.max(64, event.clientY - box.top), box.height - 56),
			flip: event.clientX - box.left > box.width - 330,
			color, html };
	}
	const hideTooltip = () => (tooltip = null);
	// The proving sentence is the point of the tooltip: it is the line that made
	// the article count as protest politics, or LGBTQ, or race. The headline it
	// came from is attribution, in smaller type underneath.
	// Some stored sentences arrive already wearing quotation marks; strip them
	// before adding our own, or the card opens with a stutter: ““If I asked…
	const unquote = (t) => t.replace(/^[\s"“”']+/, "").replace(/[\s"“”']+$/, "");
	const quote = (text, headline) =>
		text
			? `<div class="example">“${unquote(text)}”</div>` +
			  (headline && headline !== text ? `<div class="src">${headline}</div>` : "")
			: "";


	// Simple legend: NBA, WNBA, then the layers by name. Items sit at cumulative
	// x offsets so long labels don't collide with their neighbours.
	let legendItems = $derived.by(() => {
		// percent charts always get a key — the gray "all articles" bar and any
		// hatch are unexplained without one
		if (chart.layers.length <= 1 && !showNBA && !chart.percent) return [];
		const items = [];
		if (showNBA && !chart.percent) items.push({ fill: "var(--tl-nba)", label: "NBA" });
		items.push({
			fill: chart.percent ? COLORS.allArticlesPct : COLORS.allArticles,
			stroke: "rgba(42,21,3,0.25)",
			label: chart.percent ? "all articles" : "WNBA" });
		for (const layer of chart.layers)
			items.push({
				fill: layer.key === "polAndLgbtq" ? `url(#both-${chartName})` : COLORS[layer.key],
				label: layer.legend ?? layer.label });
		if (chart.hatch)
			items.push({ fill: `url(#hatch-${chartName})`, stroke: "rgba(42,21,3,0.3)",
				label: "Brittney Griner" });
		let x = 0;
		const charWidth = mobile ? 8.6 : 6.8;   // matches the two .tick font sizes
		for (const item of items) {
			item.x = x;
			x += 34 + item.label.length * charWidth;
		}
		return items;
	});

	// screen-reader description, built here to keep the markup simple
	const chartDescription =
		"Fox News WNBA articles per month" +
		(chart.layers.length ? ", with the share that " + chart.layers[0].label : "");
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<div class="timeline-chart" class:mobile>
	<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label={chartDescription}>
		<defs>
			<!-- diagonal crosshatch over the Griner share of a bar, in Griner's own
			     bronze so it reads as hers across every chart -->
			<pattern id="hatch-{chartName}" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
				<line x1="0" y1="0" x2="0" y2="6" stroke="var(--tl-griner)" stroke-width="1.6" />
			</pattern>
			<!-- the "both topics" band: green and purple in alternating stripes -->
			<pattern id="both-{chartName}" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
				<rect width="9" height="9" fill="var(--tl-politics)" />
				<line x1="0" y1="0" x2="0" y2="9" stroke="var(--tl-lgbtq)" stroke-width="4.5" />
			</pattern>
		</defs>
		<g transform="translate({margin.left},{margin.top})">

			<!-- horizontal gridlines and their y-axis numbers -->
			{#each yTicks as tick}
				<line x1="0" x2={plotWidth} y1={tickY(tick)} y2={tickY(tick)} class="grid" />
				<text x="-8" y={tickY(tick) + 4} text-anchor="end" class="tick">{tick}{chart.percent ? "%" : ""}</text>
			{/each}

			<!-- one set of bars per month -->
			{#each months as month, index (month.month)}
				{@const x = index * barWidth + 1.5}
				{@const width = Math.max(1, barWidth - 3)}

				<!-- NBA backdrop, drawn first so the WNBA bars sit in front of it
				     (never in percent mode: shares of WNBA output have no NBA scale) -->
				{#if showNBA && !chart.ownScale && !chart.percent && month.month >= NBA_FROM}
					<rect class="nba-bar"
						x={x - 0.5} width={Math.max(1, barWidth - 1)}
						y={plotHeight - barHeight(nbaByMonth[month.month] ?? 0)}
						height={barHeight(nbaByMonth[month.month] ?? 0)} />
				{/if}

				<!-- cream bar: every article that month. In percent mode it IS the
				     100% — full height whenever the month published anything -->
				{#if !chart.ownScale}
					<rect
						{x} {width}
						y={chart.percent ? (month.articles ? 0 : plotHeight) : plotHeight - barHeight(month.articles)}
						height={chart.percent ? (month.articles ? plotHeight : 0) : barHeight(month.articles)}
						fill={chart.percent ? COLORS.allArticlesPct : COLORS.allArticles}
						onmousemove={(e) => showTooltip(e,
							`<strong>${month.month}</strong> · ${month.articles} articles` +
							(month.hatched
								? `<div class="sub">${month.hatched} of them mention ${chart.hatch}</div>`
								: "") +
							quote(month.hatchExample || month.example, month.hatchHeadline),
							"#003366")}
						onmouseleave={hideTooltip}
					/>
				{/if}

				{@const h = chart.percent
					? (count) => pctHeight(count, month.articles)
					: barHeight}

				<!-- the Griner share of the month, hatched -->
				{#if month.hatched > 0}
					<rect
						{x} {width}
						y={plotHeight - h(month.hatched)}
						height={h(month.hatched)}
						fill="url(#hatch-{chartName})"
						pointer-events="none"
					/>
				{/if}

				<!-- colored layers stacked on top -->
				{#each stackedLayers(month) as piece}
					<rect
						{x} {width}
						y={plotHeight - h(piece.bottom) - h(piece.value)}
						height={h(piece.value)}
						fill={piece.key === "polAndLgbtq" ? `url(#both-${chartName})` : COLORS[piece.key]}
						onmousemove={(e) => showTooltip(e,
							`<strong>${month.month}</strong> · ${month.counts[piece.key]} of ` +
							`${month.articles}` +
							(chart.percent && month.articles
								? ` — ${Math.round(month.counts[piece.key] / month.articles * 100)}% —`
								: "") +
							` ${piece.label}` +
							quote(month.examples[piece.key] || month.example, month.headlines[piece.key]),
							COLORS[piece.key])}
						onmouseleave={hideTooltip}
					/>
				{/each}
			{/each}

			<!-- x-axis line and year labels -->
			<line x1="0" x2={plotWidth} y1={plotHeight} y2={plotHeight} class="axis" />
			{#each xTicks as tick}
				<text x={tick.index * barWidth} y={plotHeight + 18} class="tick">{tick.year}</text>
			{/each}

			<!-- color key, when there is more than one mark to tell apart — which
			     the NBA backdrop counts as, or the pale bars go unexplained -->
			{#if legendItems.length}
				<g transform="translate(0,-14)" class="legend">
					{#each legendItems as item}
						<rect x={item.x} y="0" width="12" height="12" fill={item.fill}
							stroke={item.stroke ?? "none"} />
						<text x={item.x + 17} y="10">{item.label}</text>
					{/each}
				</g>
			{/if}
		</g>
	</svg>

	{#if tooltip}
		<div class="tooltip" class:flip={tooltip.flip}
			style="left:{tooltip.x}px; top:{tooltip.y}px; border-left-color:{tooltip.color}">
			{@html tooltip.html}
		</div>
	{/if}
</div>

<style>
	/* -----------------------------------------------------------------------
	   COLORS — every mark this chart draws, in one place. Each defers to the
	   page-level --c-* palette (Index.svelte), so change it there to recolor
	   every chart, or here to recolor just the timelines.
	   ----------------------------------------------------------------------- */
	.timeline-chart {
		--tl-cream: var(--c-cream, #f5ecd8);
		--tl-pct-bar: rgba(42, 21, 3, 0.07);
		--tl-clark: var(--c-clark, #2a78d6);
		--tl-griner: var(--c-griner, #a8720a);
		--tl-politics: var(--c-politics, #1f9d6e);
		--tl-race: var(--c-race, #d55181);
		--tl-lgbtq: var(--c-lgbtq, #b04ac2);
		--tl-both: #677398;      /* the "touches both" band on the LGBTQ chart */
		--tl-trans: var(--c-trans, #17a2b8);
		--tl-nba: var(--c-nba, #2a1503);
	}

	/* x and width join the transition so re-windowing the axis slides the
	   surviving months sideways rather than teleporting them */
	rect { transition: height 500ms ease, y 500ms ease, x 500ms ease, width 500ms ease; }
	.nba-bar { fill: var(--tl-nba); }
	.tick { transition: y 500ms ease; }

	.timeline-chart { position: relative; width: 100%; margin: 6px auto 18px; }
	svg { width: 100%; height: auto; }

	.grid { stroke: rgba(42, 21, 3, 0.14); stroke-width: 1; }
	.axis { stroke: rgba(42, 21, 3, 0.35); stroke-width: 1; }
	.tick { font-size: 12px; fill: rgba(42, 21, 3, 0.6); }
	.legend text { font-size: 12.5px; fill: rgba(42, 21, 3, 0.75); }

	/* the mobile drawing is 480 units in the same on-screen width, so these
	   render ~1.8x larger than the same size would on desktop */
	.mobile .tick { font-size: 17px; }
	.mobile .legend text { font-size: 15px; }

	/* The same clipping card as the Fightin' Words tooltip: cream, hairline
	   border, a left accent in the layer's own colour, the quote in the story's
	   serif. One tooltip grammar across the piece. */
	.tooltip {
		position: absolute;
		transform: translate(14px, -50%);
		width: 300px;
		background: #fffdf8;
		border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid #2a1503;   /* recoloured inline per layer */
		border-radius: 3px;
		color: #2a1503;
		font-size: 12.5px;
		line-height: 1.45;
		padding: 9px 12px 10px;
		box-shadow: 0 5px 20px rgba(42, 21, 3, 0.16);
		pointer-events: none;
		z-index: 5;
	}
	.tooltip.flip { transform: translate(calc(-100% - 14px), -50%); }
	/* :global is needed because this HTML comes from a string, not from markup */
	.tooltip :global(strong) {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11.5px; font-weight: 700; letter-spacing: 0.06em;
		text-transform: uppercase;
	}
	.tooltip :global(.what) { text-transform: lowercase; }
	.tooltip :global(.n) { color: rgba(42, 21, 3, 0.5); font-size: 11.5px; }
	.tooltip :global(.sub) {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		color: rgba(42, 21, 3, 0.55); font-size: 11px; margin-top: 2px;
	}
	.tooltip :global(.example) {
		margin-top: 6px; font-size: 13.5px; line-height: 1.5; color: #2a1503;
	}
	.tooltip :global(.src) {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		margin-top: 4px; font-size: 10.5px; color: rgba(42, 21, 3, 0.5);
	}
</style>
