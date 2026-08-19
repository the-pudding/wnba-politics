<script>
	// ---------------------------------------------------------------------------
	// The trans-coverage timeline as a unit chart: ONE DOT PER ARTICLE.
	//
	// A bar saying "64" and sixty-four individual marks are different claims on
	// the reader's attention. The whole story here is 131 articles — three in
	// 2021, five in a busy pre-2026 month, then sixty-four in August 2026 alone —
	// and at that scale each article deserves its own mark, with its own headline
	// on hover. Aggregation would hide exactly the gravity being argued.
	//
	// Same contract as TimelineStatic, so the scrolly drives both identically:
	// revealUntil, startMonth/endMonth (the x-window), yCap (the axis pin).
	//
	// Layout is a beeswarm: each dot is anchored to its publication DATE on the
	// x-axis but free to shove sideways when a month gets crowded, so August
	// 2026 reads as a mound spilling outward rather than a needle. No y-axis —
	// height isn't a scale here, it's just accumulation.
	// ---------------------------------------------------------------------------
	import data from "$data/trans_articles.json";
	import { forceSimulation, forceX, forceY, forceCollide } from "d3-force";

	let {
		revealUntil = null,
		startMonth = null,
		endMonth = null,
		yCap = null,
		// the final conversion: same months, but each bar is that month's WHOLE
		// Fox WNBA output scaled to 100%, teal = the trans-athlete share
		share = false,
		// beat 3 the beeswarm way: the 2026 months gain a cream dot for every
		// OTHER article, so the purple share of each mound IS the percentage
		others = false,
		// Pudding-style: fill the phone screen when inside a scrolly
		tall = false
	} = $props();

	const DOT = "var(--c-trans-dots, #b04ac2)";  // follows the LGBTQ purple by default
	const OTHER = "var(--c-other-dots, #8f8b84)";

	// every month in the window, whether or not it has articles — empty months
	// are the silence before 2026, and they belong on the axis
	const first = data.articles[0]?.month ?? "2019-07";
	const last = data.articles[data.articles.length - 1]?.month ?? "2026-08";
	function monthRange(a, b) {
		const out = [];
		let [y, m] = a.split("-").map(Number);
		const [ey, em] = b.split("-").map(Number);
		while (y < ey || (y === ey && m <= em)) {
			out.push(`${y}-${String(m).padStart(2, "0")}`);
			m++; if (m > 12) { m = 1; y++; }
		}
		return out;
	}
	let months = $derived(monthRange(startMonth ?? "2019-07", endMonth ?? last));

	const inWindow = (a) =>
		(!startMonth || a.month >= startMonth) &&
		(!endMonth || a.month <= endMonth) &&
		(!revealUntil || a.month <= revealUntil);
	let shown = $derived([
		...data.articles.filter(inWindow).map((a) => ({ ...a, kind: "trans" })),
		...(others ? (data.others ?? []).filter(inWindow).map((a) => ({ ...a, kind: "other" })) : [])
	]);

	// stack order within a month: trans articles first (purple at the base of
	// each mound), then the rest — so a month's purple share reads at a glance
	let stacked = $derived.by(() => {
		const perMonth = new Map();
		return [...shown]
			.sort((a, b) => (a.kind === b.kind ? (a.date < b.date ? -1 : 1)
				: a.kind === "trans" ? -1 : 1))
			.map((article) => {
				const n = perMonth.get(article.month) ?? 0;
				perMonth.set(article.month, n + 1);
				return { ...article, slot: n };
			});
	});

	// --- geometry (mirrors TimelineStatic so the swap is seamless) --------------
	// Mobile gets a narrower, taller drawing so dots and axis type render larger
	// on screen — same scheme as TimelineStatic.
	let viewportWidth = $state(typeof window === "undefined" ? 1200 : window.innerWidth);
	let mobile = $derived(viewportWidth < 640);
	let WIDTH = $derived(mobile ? 480 : 860);
	let HEIGHT = $derived(mobile ? (tall ? 880 : 440) : 360);
	let margin = $derived(mobile
		? { left: 54, right: 8, top: 34, bottom: 34 }
		: { left: 44, right: 14, top: 30, bottom: 30 });
	let plotWidth = $derived(WIDTH - margin.left - margin.right);
	let plotHeight = $derived(HEIGHT - margin.top - margin.bottom);

	let colWidth = $derived(plotWidth / Math.max(1, months.length));
	let monthIndex = $derived(new Map(months.map((m, i) => [m, i])));

	// Big dots, sized so the swarm fills roughly a third of the plot — the
	// point of a unit chart is that each unit is unmissable.
	let radius = $derived(Math.max(4.5, Math.min(16,
		Math.sqrt((0.30 * plotWidth * plotHeight) / (Math.PI * Math.max(1, shown.length))))));

	// x-anchor at the article's actual DAY, not just its month column
	const anchorX = (article) => {
		const index = monthIndex.get(article.month) ?? 0;
		const day = Number(article.date.slice(8, 10)) || 15;
		return margin.left + (index + (day - 1) / 31) * colWidth;
	};
	let FLOOR = $derived(margin.top + plotHeight);

	// Deterministic beeswarm: seeded from the old single-file stack (no
	// randomness — resizes and beat changes always land the same layout), then
	// relaxed with a hard pull to the date, soft gravity to the baseline, and
	// collision. Floor and walls clamped every tick so the pile grows UP.
	// The x-pull is deliberately loose: strong enough that a lone article
	// sits on its date, weak enough that August 2026's sixty-four spread
	// into a mound instead of a tower. Ceiling + floor clamped every tick,
	// so crowding can only resolve sideways.
	// `floorAt` is each dot's personal floor: the plot baseline normally, or —
	// for the gray pass — the top of the purple stratum under that x, so gray
	// can only ever rest ON the purple, never beside or below it.
	const relax = (nodes, floorAt) => {
		const sim = forceSimulation(nodes)
			.force("x", forceX((d) => d.ax).strength(0.22))
			.force("y", forceY(FLOOR - radius).strength(0.05))
			.force("collide", forceCollide(radius + 0.6).iterations(3))
			.stop();
		for (let i = 0; i < 300; i++) {
			sim.tick();
			for (const n of nodes) {
				if (n.fx == null) {
					const cap = floorAt ? floorAt(n.x) : FLOOR - radius;
					n.y = Math.max(margin.top + radius, Math.min(n.y, cap));
					n.x = Math.max(margin.left + radius,
						Math.min(WIDTH - margin.right - radius, n.x));
				}
			}
		}
	};

	// Two passes so the strata stay clean: the purple trans dots settle first
	// on the baseline and are FROZEN; the gray "everything else" dots then get
	// the purple mound's SURFACE as their floor — purple below, gray above.
	let placed = $derived.by(() => {
		const mk = (article) => ({
			article,
			ax: anchorX(article),
			x: anchorX(article) + (article.slot % 2 ? 0.6 : -0.6),
			y: FLOOR - radius - article.slot * radius * 1.4
		});
		const transNodes = stacked.filter((a) => a.kind !== "other").map(mk);
		relax(transNodes);
		const otherNodes = stacked.filter((a) => a.kind === "other").map(mk);
		if (otherNodes.length) {
			// the purple surface, sampled per month column
			const surface = new Array(months.length).fill(FLOOR - radius);
			for (const n of transNodes) {
				const bucket = Math.max(0, Math.min(months.length - 1,
					Math.floor((n.x - margin.left) / colWidth)));
				surface[bucket] = Math.min(surface[bucket], n.y - 1.8 * radius);
			}
			const graysFloor = (x) => surface[Math.max(0, Math.min(months.length - 1,
				Math.floor((x - margin.left) / colWidth)))];
			for (const n of transNodes) { n.fx = n.x; n.fy = n.y; }
			// seed the grays above their month's surface so they start legal
			for (const n of otherNodes) n.y = Math.min(n.y, graysFloor(n.ax));
			relax([...transNodes, ...otherNodes], graysFloor);
			for (const n of transNodes) { delete n.fx; delete n.fy; }
		}
		return [...transNodes, ...otherNodes];
	});
	// year labels normally; month labels once the window is zoomed to a year
	let xTicks = $derived(months.length <= 14
		? months.map((m, i) => ({
			label: `${MONTH_NAMES[Number(m.slice(5, 7)) - 1]}${m.endsWith("-01") ? " " + m.slice(0, 4) : ""}`,
			x: margin.left + (i + 0.5) * colWidth }))
		: months.map((m, i) => ({ m, i }))
			.filter(({ m }) => m.endsWith("-01") || m === months[0])
			.map(({ m, i }) => ({ label: m.slice(0, 4), x: margin.left + i * colWidth })));

	// --- share mode: % of ALL Fox WNBA articles that month about trans athletes
	let transPerMonth = $derived(shown.reduce((acc, a) => {
		acc.set(a.month, (acc.get(a.month) ?? 0) + 1); return acc;
	}, new Map()));
	let shareBars = $derived(months
		.filter((m) => (data.monthly_totals?.[m] ?? 0) > 0 &&
			(!revealUntil || m <= revealUntil))
		.map((m) => {
			const total = data.monthly_totals[m];
			const trans = transPerMonth.get(m) ?? 0;
			return { month: m, total, trans, pct: trans / total };
		}));
	const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
		"Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
	const monthLabel = (m) => `${MONTH_NAMES[Number(m.slice(5, 7)) - 1]} ${m.slice(0, 4)}`;
	const barX = (m) => margin.left + (monthIndex.get(m) ?? 0) * colWidth + colWidth * 0.1;
	let barW = $derived(colWidth * 0.8);
	const pctY = (pct) => margin.top + plotHeight * (1 - pct);

	let tip = $state(null);
	// a tooltip must not outlive the beat that spawned it
	$effect(() => { share; revealUntil; startMonth; endMonth; tip = null; });
	function place(event) {
		const box = event.currentTarget.closest(".timeline-dots").getBoundingClientRect();
		return { x: event.clientX - box.left,
			y: Math.min(Math.max(60, event.clientY - box.top), box.height - 56),
			flip: event.clientX - box.left > box.width - 320 };
	}
	function showTip(event, article) {
		tip = { head: article.date, body: article.title,
			color: article.kind === "other" ? "#8f8b84" : "#b04ac2", ...place(event) };
	}
	function showBarTip(event, bar) {
		tip = { head: monthLabel(bar.month), color: "#b04ac2",
			body: `${bar.trans} of ${bar.total} Fox WNBA articles — `
				+ `${Math.round(bar.pct * 100)}% — mention trans athletes.`,
			...place(event) };
	}
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<div class="timeline-dots" class:mobile>
	<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img"
		aria-label="One dot for each Fox WNBA article about trans athletes">
		<g transform="translate(0,0)">
			{#each xTicks as tick}
				<text class="tick" x={tick.x} y={HEIGHT - 8}
					text-anchor={months.length <= 14 ? "middle" : "start"}>{tick.label}</text>
			{/each}
			<line class="axis" x1={margin.left} x2={WIDTH - margin.right}
				y1={margin.top + plotHeight} y2={margin.top + plotHeight} />

			<!-- the % scale exists only in share mode -->
			<g class="scale" class:on={share}>
				{#each [0.25, 0.5, 0.75, 1] as pct}
					<line class="grid" x1={margin.left} x2={WIDTH - margin.right}
						y1={pctY(pct)} y2={pctY(pct)} />
					<text class="tick" x={margin.left - 8} y={pctY(pct) + 4}
						text-anchor="end">{pct * 100}%</text>
				{/each}
			</g>

			<g class="marks" class:hidden={share}>
				{#each placed as node (node.article.url)}
					<circle
						cx={node.x} cy={node.y} r={radius}
						fill={node.article.kind === "other" ? OTHER : DOT}
						class:other={node.article.kind === "other"}
						onpointerenter={(e) => showTip(e, node.article)}
						onpointermove={(e) => showTip(e, node.article)}
						onpointerleave={() => (tip = null)}
						role="presentation" />
				{/each}
			</g>

			<g class="marks" class:hidden={!share}>
				{#each shareBars as bar (bar.month)}
					<rect class="bar-all" x={barX(bar.month)} width={barW}
						y={margin.top} height={plotHeight}
						onpointerenter={(e) => showBarTip(e, bar)}
						onpointermove={(e) => showBarTip(e, bar)}
						onpointerleave={() => (tip = null)} />
					<rect class="bar-trans" x={barX(bar.month)} width={barW}
						y={pctY(bar.pct)} height={plotHeight * bar.pct}
						onpointerenter={(e) => showBarTip(e, bar)}
						onpointermove={(e) => showBarTip(e, bar)}
						onpointerleave={() => (tip = null)} />
				{/each}
			</g>
		</g>
	</svg>

	{#if tip}
		<div class="tooltip" class:flip={tip.flip}
			style="left:{tip.x}px; top:{tip.y}px; border-left-color:{tip.color}">
			<strong>{tip.head}</strong>
			<p class="example">{tip.body}</p>
		</div>
	{/if}

</div>

<style>
	.timeline-dots { position: relative; max-width: 860px; margin: 0 auto; }
	svg { width: 100%; height: auto; display: block; overflow: visible; }

	.axis { stroke: rgba(42, 21, 3, 0.4); stroke-width: 1; }
	.tick { font-size: 11px; fill: rgba(42, 21, 3, 0.6); }
	.grid { stroke: rgba(42, 21, 3, 0.1); stroke-width: 1; }

	/* mobile draws 480 units in the same on-screen width, so this renders large */
	.mobile .tick { font-size: 17px; }

	/* the same motion contract as the bars: re-windowing slides surviving dots */
	circle {
		transition: cx 500ms ease, cy 500ms ease, r 500ms ease;
		cursor: default;
		stroke: rgba(255, 253, 248, 0.85); stroke-width: 1;
	}
	circle.other { stroke: rgba(42, 21, 3, 0.25); }

	/* dots <-> share bars: a plain crossfade, 500ms like every other move */
	.marks, .scale { transition: opacity 500ms ease; }
	.marks.hidden { opacity: 0; pointer-events: none; }
	.scale { opacity: 0; }
	.scale.on { opacity: 1; }

	.bar-all { fill: rgba(42, 21, 3, 0.07); }
	.bar-trans { fill: var(--c-trans-dots, #b04ac2); }
	rect { transition: y 500ms ease, height 500ms ease, x 500ms ease, width 500ms ease; }

	/* the clipping card, as everywhere else in the piece */
	.tooltip {
		position: absolute; transform: translate(14px, -50%);
		width: 300px;
		background: #fffdf8; border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid #b04ac2; border-radius: 3px;
		padding: 9px 12px 10px;
		box-shadow: 0 5px 20px rgba(42, 21, 3, 0.16);
		pointer-events: none; z-index: 5;
	}
	.tooltip.flip { transform: translate(calc(-100% - 14px), -50%); }
	.tooltip strong {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
		color: rgba(42, 21, 3, 0.6);
	}
	.tooltip .example { margin: 5px 0 0; font-size: 13.5px; line-height: 1.5; color: #2a1503; }

	.unit-note {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 10.5px; letter-spacing: 0.08em; text-transform: uppercase;
		color: rgba(42, 21, 3, 0.55); text-align: right; margin: 2px 6px 0 0;
	}
</style>
