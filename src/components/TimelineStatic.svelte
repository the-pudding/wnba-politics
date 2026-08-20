<script>
	// Fox News WNBA articles per month; the `name` prop picks which colored
	// layers stack on the cream all-articles bars.
	// Doc embed: chart: timeline-griner | years: 2022
	import foxTimeline from "$data/fox_timeline.json";
	import nbaMonthly from "$data/fox_nba_monthly.json";
	import { niceTicks, yearTicks } from "../utils/chartAxis.js";

	let {
		name = "timeline-full", // see CHART_TYPES
		from = null,           // optional "2020-01" lower bound
		to = null,             // optional "2023-12" upper bound
		// reveal up to this month; the x-axis keeps its full range
		revealUntil = null,
		// NBA backdrop columns. Doc line: chart: timeline-clark | nba: true
		nba = false,
		// a scrolly beat can pin the y-axis low, then release it
		yCap = null,
		// set by TimelineScrolly; fills the phone screen, phone widths only
		tall = false
	} = $props();

	// months before 2016 are absent, not zero
	const NBA_FROM = nbaMonthly.from;
	const nbaByMonth = Object.fromEntries(
		nbaMonthly.months.map((m, i) => [m, nbaMonthly.counts[i]]));

	// values live in the style block below
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

	// column positions in each month's flat "t" list
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

	// ownScale: the y-axis fits the layer instead of the article total
	const CHART_TYPES = {
		"timeline-full": { layers: [] },
		"timeline-clark": { layers: [{ key: "clark", label: "mention Caitlin Clark", legend: "mentions Caitlin Clark" }] },
		// overlay, not a stack — an article can mention both
		"timeline-griner": {
			overlay: true,
			layers: [
				{ key: "griner", label: "mention Brittney Griner", legend: "Brittney Griner" },
				{ key: "clark", label: "mention Caitlin Clark", legend: "Caitlin Clark" }
			]
		},
		// one union band, not a stack — 13% match both and would count twice
		"timeline-protest": {
			percent: true,
			hatch: "griner",
			layers: [
				{ key: "polrace", label: "touch protest politics or race", legend: "protest politics or race" }
			]
		},
		// mutually exclusive bands: the stack sums to the share touching either topic
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
			// hatch the Griner share so 2022 isn't misread as protest coverage
			hatch: "griner",
			layers: [
				{ key: "politics", label: "touch protest politics" },
				{ key: "race", label: "are about race" },
				{ key: "lgbtq", label: "touch LGBTQ / sexuality" }
			]
		},
		"timeline-trans": { layers: [{ key: "trans", label: "are trans-related" }], ownScale: true }
	};
	const chart = CHART_TYPES[name] ?? CHART_TYPES["timeline-full"];

	// the three-way split is derived from the unions so the two figures agree
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

	// derived, not const: a scrolly beat may re-window from/to
	let allMonths = $derived(foxTimeline.months
		.filter((row) => (!from || row.month >= from) && (!to || row.month <= to))
		.map((row) => ({
			month: row.month,
			articles: row.n,
			example: row.ex ?? "",
			counts: Object.fromEntries(chart.layers.map((l) => [l.key, countOf(row.t, l.key)])),
			hatched: chart.hatch ? (row.t[columnOf[chart.hatch]] ?? 0) : 0,
			hatchExample: chart.hatch ? (row.tex?.[columnOf[chart.hatch]] ?? "") : "",
			hatchHeadline: chart.hatch ? (row.thed?.[columnOf[chart.hatch]] ?? "") : "",
			examples: Object.fromEntries(chart.layers.map((l) => [l.key, row.tex?.[columnOf[l.ex ?? l.key]] ?? ""])),
			headlines: Object.fromEntries(chart.layers.map((l) => [l.key, row.thed?.[columnOf[l.ex ?? l.key]] ?? ""]))
		})));
	// the axis still spans every month
	let months = $derived(revealUntil
		? allMonths.filter((row) => row.month <= revealUntil)
		: allMonths);

	// mobile gets its own drawing: fewer units wide, so type renders larger
	let viewportWidth = $state(typeof window === "undefined" ? 1200 : window.innerWidth);
	let mobile = $derived(viewportWidth < 640);
	let WIDTH = $derived(mobile ? 480 : 860);
	let HEIGHT = $derived(mobile ? (tall ? 880 : 440) : 360);
	let margin = $derived(mobile
		? { left: 54, right: 8, top: 34, bottom: 34 }
		: { left: 44, right: 14, top: 30, bottom: 30 });
	let plotWidth = $derived(WIDTH - margin.left - margin.right);
	let plotHeight = $derived(HEIGHT - margin.top - margin.bottom);
	let barWidth = $derived(plotWidth / Math.max(1, allMonths.length));

	// y-scale fits the whole series, not what's revealed, so the axis stays fixed
	let layerMax = $derived(Math.max(1, ...allMonths.map((m) => Math.max(0, ...Object.values(m.counts)))));
	let articleMax = $derived(Math.max(1, ...allMonths.map((m) => m.articles),
		...(nba ? nbaMonthly.counts : [0])));
	let yMax = $derived(yCap ?? (chart.ownScale ? layerMax : articleMax));

	// clamped so bars taller than a capped axis peg to the top
	let barHeight = $derived((count) => Math.min(plotHeight, (count / yMax) * plotHeight));

	let pctHeight = $derived((count, total) =>
		total ? Math.min(plotHeight, (count / total) * plotHeight) : 0);
	const PCT_TICKS = [25, 50, 75, 100];

	let xTicks = $derived(yearTicks(allMonths));
	let yTicks = $derived(chart.percent ? PCT_TICKS : niceTicks(yMax));
	let tickY = $derived((tick) => chart.percent
		? plotHeight * (1 - tick / 100)
		: plotHeight - barHeight(tick));

	// overlay mode doesn't stack: every band rises from the baseline
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

	let tooltip = $state(null); // null, or {x, y, html}

	function showTooltip(event, html, color = "var(--color-ink)") {
		const box = event.currentTarget.closest(".timeline-chart").getBoundingClientRect();
		tooltip = {
			x: event.clientX - box.left,
			// clamped so the card can't slide off the figure
			y: Math.min(Math.max(64, event.clientY - box.top), box.height - 56),
			flip: event.clientX - box.left > box.width - 330,
			color, html };
	}
	const hideTooltip = () => (tooltip = null);
	// some stored sentences arrive already quoted; strip or the card opens ““
	const unquote = (t) => t.replace(/^[\s"“”']+/, "").replace(/[\s"“”']+$/, "");
	const quote = (text, headline) =>
		text
			? `<div class="example">“${unquote(text)}”</div>` +
			  (headline && headline !== text ? `<div class="src">${headline}</div>` : "")
			: "";


	// legend items sit at cumulative x offsets so labels don't collide
	let legendItems = $derived.by(() => {
		// percent charts always get a key or the gray bar goes unexplained
		if (chart.layers.length <= 1 && !nba && !chart.percent) return [];
		const items = [];
		if (nba && !chart.percent) items.push({ fill: "var(--tl-nba)", label: "NBA" });
		items.push({
			fill: chart.percent ? COLORS.allArticlesPct : COLORS.allArticles,
			stroke: "rgba(42,21,3,0.25)",
			label: chart.percent ? "all articles" : "WNBA" });
		for (const layer of chart.layers)
			items.push({
				fill: layer.key === "polAndLgbtq" ? `url(#both-${name})` : COLORS[layer.key],
				label: layer.legend ?? layer.label });
		if (chart.hatch)
			items.push({ fill: `url(#hatch-${name})`, stroke: "rgba(42,21,3,0.3)",
				label: "Brittney Griner" });
		let x = 0;
		const charWidth = mobile ? 8.6 : 6.8;   // matches the two .tick font sizes
		for (const item of items) {
			item.x = x;
			x += 34 + item.label.length * charWidth;
		}
		return items;
	});

	const chartDescription =
		"Fox News WNBA articles per month" +
		(chart.layers.length ? ", with the share that " + chart.layers[0].label : "");
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<div class="timeline-chart" class:mobile>
	<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label={chartDescription}>
		<defs>
			<pattern id="hatch-{name}" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
				<line x1="0" y1="0" x2="0" y2="6" stroke="var(--tl-griner)" stroke-width="1.6" />
			</pattern>
			<pattern id="both-{name}" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
				<rect width="9" height="9" fill="var(--tl-politics)" />
				<line x1="0" y1="0" x2="0" y2="9" stroke="var(--tl-lgbtq)" stroke-width="4.5" />
			</pattern>
		</defs>
		<g transform="translate({margin.left},{margin.top})">

			{#each yTicks as tick}
				<line x1="0" x2={plotWidth} y1={tickY(tick)} y2={tickY(tick)} class="grid" />
				<text x="-8" y={tickY(tick) + 4} text-anchor="end" class="tick">{tick}{chart.percent ? "%" : ""}</text>
			{/each}

			{#each months as month, index (month.month)}
				{@const x = index * barWidth + 1.5}
				{@const width = Math.max(1, barWidth - 3)}

				<!-- NBA backdrop: never in percent mode — shares of WNBA output have no NBA scale -->
				{#if nba && !chart.ownScale && !chart.percent && month.month >= NBA_FROM}
					<rect class="nba-bar"
						x={x - 0.5} width={Math.max(1, barWidth - 1)}
						y={plotHeight - barHeight(nbaByMonth[month.month] ?? 0)}
						height={barHeight(nbaByMonth[month.month] ?? 0)} />
				{/if}

				<!-- in percent mode the cream bar IS the 100% -->
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

				{#if month.hatched > 0}
					<rect
						{x} {width}
						y={plotHeight - h(month.hatched)}
						height={h(month.hatched)}
						fill="url(#hatch-{name})"
						pointer-events="none"
					/>
				{/if}

				{#each stackedLayers(month) as piece}
					<rect
						{x} {width}
						y={plotHeight - h(piece.bottom) - h(piece.value)}
						height={h(piece.value)}
						fill={piece.key === "polAndLgbtq" ? `url(#both-${name})` : COLORS[piece.key]}
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

			<line x1="0" x2={plotWidth} y1={plotHeight} y2={plotHeight} class="axis" />
			{#each xTicks as tick}
				<text x={tick.index * barWidth} y={plotHeight + 18} class="tick">{tick.year}</text>
			{/each}

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
	/* chart colors; each defers to the page-level --c-* palette (Index.svelte) */
	.timeline-chart {
		--tl-cream: var(--color-cream);
		--tl-pct-bar: rgba(42, 21, 3, 0.07);
		--tl-clark: var(--color-clark);
		--tl-griner: var(--color-griner);
		--tl-politics: var(--color-politics);
		--tl-race: var(--color-race);
		--tl-lgbtq: var(--color-lgbtq);
		--tl-both: #677398;      /* the "touches both" band on the LGBTQ chart */
		--tl-trans: var(--color-trans);
		--tl-nba: var(--color-nba);
	}

	/* x/width transition so re-windowing slides bars rather than teleporting them */
	rect { transition: height 500ms ease, y 500ms ease, x 500ms ease, width 500ms ease; }
	.nba-bar { fill: var(--tl-nba); }
	.tick { transition: y 500ms ease; }

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
		border-left: 3px solid var(--color-ink);   /* recoloured inline per layer */
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
		margin-top: 6px; font-size: 13.5px; line-height: 1.5; color: var(--color-ink);
	}
	.tooltip :global(.src) {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		margin-top: 4px; font-size: 10.5px; color: rgba(42, 21, 3, 0.5);
	}
</style>
