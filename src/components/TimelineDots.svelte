<script>
	// One dot per Fox article about trans athletes — a beeswarm anchored to
	// publication date, piling upward when a month gets crowded.
	// Same scrolly contract as TimelineBars: revealUntil, startMonth/endMonth, yCap.
	import articles from "$data/trans_articles.csv";
	import { forceSimulation, forceX, forceY, forceCollide } from "d3-force";

	let { revealUntil = null, startMonth = null, endMonth = null, yCap = null, tall = false } = $props();

	const DOT = "var(--color-trans-dots)";
	const MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
		"Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

	const last = articles[articles.length - 1]?.month ?? "2026-08";
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

	let shown = $derived(articles.filter((a) =>
		(!startMonth || a.month >= startMonth) &&
		(!endMonth || a.month <= endMonth) &&
		(!revealUntil || a.month <= revealUntil)));

	let stacked = $derived.by(() => {
		const perMonth = new Map();
		return shown.map((article) => {
			const n = perMonth.get(article.month) ?? 0;
			perMonth.set(article.month, n + 1);
			return { ...article, slot: n };
		});
	});

	// mobile draws a narrower, taller canvas so dots and type render larger
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

	let radius = $derived(Math.max(4.5, Math.min(16,
		Math.sqrt((0.30 * plotWidth * plotHeight) / (Math.PI * Math.max(1, shown.length))))));

	const anchorX = (article) => {
		const index = monthIndex.get(article.month) ?? 0;
		const day = Number(article.date.slice(8, 10)) || 15;
		return margin.left + (index + (day - 1) / 31) * colWidth;
	};
	let FLOOR = $derived(margin.top + plotHeight);

	// deterministic beeswarm: seeded from a per-month stack, pulled to the date,
	// soft gravity down, collision out — floor and walls clamped every tick
	let placed = $derived.by(() => {
		const nodes = stacked.map((article) => ({
			article,
			ax: anchorX(article),
			x: anchorX(article) + (article.slot % 2 ? 0.6 : -0.6),
			y: FLOOR - radius - article.slot * radius * 1.4
		}));
		const sim = forceSimulation(nodes)
			.force("x", forceX((d) => d.ax).strength(0.22))
			.force("y", forceY(FLOOR - radius).strength(0.05))
			.force("collide", forceCollide(radius + 0.6).iterations(3))
			.stop();
		for (let i = 0; i < 300; i++) {
			sim.tick();
			for (const n of nodes) {
				n.y = Math.max(margin.top + radius, Math.min(n.y, FLOOR - radius));
				n.x = Math.max(margin.left + radius,
					Math.min(WIDTH - margin.right - radius, n.x));
			}
		}
		return nodes;
	});

	// year labels normally; month labels once the window zooms to a year
	let xTicks = $derived(months.length <= 14
		? months.map((m, i) => ({
			label: `${MONTH_NAMES[Number(m.slice(5, 7)) - 1]}${m.endsWith("-01") ? " " + m.slice(0, 4) : ""}`,
			x: margin.left + (i + 0.5) * colWidth }))
		: months.map((m, i) => ({ m, i }))
			.filter(({ m }) => m.endsWith("-01") || m === months[0])
			.map(({ m, i }) => ({ label: m.slice(0, 4), x: margin.left + i * colWidth })));

	let tip = $state(null);
	$effect(() => { revealUntil; startMonth; endMonth; tip = null; });
	function showTip(event, article) {
		const box = event.currentTarget.closest(".timeline-dots").getBoundingClientRect();
		tip = { head: article.date, body: article.title,
			x: event.clientX - box.left,
			y: Math.min(Math.max(60, event.clientY - box.top), box.height - 56),
			flip: event.clientX - box.left > box.width - 320 };
	}
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<div class="timeline-dots" class:mobile>
	<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img"
		aria-label="One dot for each Fox WNBA article about trans athletes">
		{#each xTicks as tick}
			<text class="tick" x={tick.x} y={HEIGHT - 8}
				text-anchor={months.length <= 14 ? "middle" : "start"}>{tick.label}</text>
		{/each}
		<line class="axis" x1={margin.left} x2={WIDTH - margin.right}
			y1={margin.top + plotHeight} y2={margin.top + plotHeight} />

		{#each placed as node (node.article.url)}
			<circle
				cx={node.x} cy={node.y} r={radius} fill={DOT}
				onpointerenter={(e) => showTip(e, node.article)}
				onpointermove={(e) => showTip(e, node.article)}
				onpointerleave={() => (tip = null)}
				role="presentation" />
		{/each}
	</svg>

	{#if tip}
		<div class="tooltip" class:flip={tip.flip} style="left:{tip.x}px; top:{tip.y}px">
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
	.mobile .tick { font-size: 17px; }

	circle {
		transition: cx 500ms ease, cy 500ms ease, r 500ms ease;
		cursor: default;
		stroke: rgba(255, 253, 248, 0.85); stroke-width: 1;
	}

	.tooltip {
		position: absolute; transform: translate(14px, -50%);
		width: 300px;
		background: var(--color-paper); border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid var(--color-trans-dots); border-radius: 3px;
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
	.tooltip .example { margin: 5px 0 0; font-size: 13.5px; line-height: 1.5; color: var(--color-ink); }
</style>
