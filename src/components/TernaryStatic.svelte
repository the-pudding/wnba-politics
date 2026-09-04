<script>
	// Static chyron ternary
	import chy from "$data/chyrons.json";

	// bare: no title/footnote inside a scrolly; big + highlightColor: scrolly display labels
	let {
		words = [],
		groups = [],
		bare = false,
		big = false,
		highlightColor = null,
		// a word to pin the tooltip on (a chip in the scrolly card being hovered)
		focus = null,
		// write the lit words on the drawing; the scrolly turns this off, since
		// its words sit in the card as chips
		labels = true,
		// draw the dashed circle around each band of words (the search step
		// turns it off: kept words are just lit)
		enclose = true,
		// hide words used fewer times than this (the explore step's slider)
		minTotal = 0
	} = $props();

	// the three networks' colours, shared across the site (properties/color.json)
	const CHANNEL_COLORS = {
		"Fox News": "var(--color-fox)",
		CNN: "var(--color-cnn)",
		MSNBC: "var(--color-msnbc)"
	};
	const GROUP_COLORS = ["#9061c2", "var(--color-fox)", "#1f7a5a", "#1d4f9c"];
	const DOT = "#b3a58a";
	const MIN_TOTAL = 1;

	let channels = $derived(chy.channels ?? []);
	// every band takes the chart's highlight colour when one is given (the
	// scrolly: all Fox red); otherwise each band gets its own palette colour
	let bands = $derived(
		(groups.length ? groups : words.length ? [words] : []).map((band, i) => ({
			words: new Set(band.map((w) => w.toLowerCase())),
			color: highlightColor ?? GROUP_COLORS[i % GROUP_COLORS.length]
		}))
	);
	const bandFor = (term) =>
		bands.find((band) => band.words.has(term))?.color ?? null;
	// the colour a hovered point takes: its band's, else the chart's highlight
	let hoverColor = $derived(highlightColor ?? GROUP_COLORS[0]);

	const SIDE = 700,
		PAD = 58;
	const HEIGHT = SIDE * 0.92;
	const corners = (() => {
		const width = SIDE - PAD * 2;
		const tall = (width * Math.sqrt(3)) / 2;
		const top = (HEIGHT - tall) / 2 + 6;
		return {
			A: [SIDE / 2, top],
			B: [PAD, top + tall],
			C: [SIDE - PAD, top + tall]
		};
	})();
	const bary = (shares) => [
		shares[0] * corners.A[0] +
			shares[1] * corners.B[0] +
			shares[2] * corners.C[0],
		shares[0] * corners.A[1] +
			shares[1] * corners.B[1] +
			shares[2] * corners.C[1]
	];

	let terms = $derived(
		(chy.ternary ?? [])
			.filter((t) => t.total >= Math.max(MIN_TOTAL, minTotal))
			.map((t) => {
				const [px, py] = bary(t.shares);
				return { ...t, px, py, lit: bandFor(t.term) };
			})
	);
	let biggest = $derived(Math.max(1, ...terms.map((t) => t.total)));
	// dot size runs on a log scale: "griner" (7,000 uses) would otherwise dwarf
	// everything, leaving a 200-use word like "foul" as a speck
	let smallest = $derived(Math.max(1, Math.min(...terms.map((t) => t.total))));
	const radius = (total) => {
		const span = Math.log(Math.max(2, biggest / smallest));
		const t = Math.log(Math.max(1, total / smallest)) / span; // 0 … 1
		return (big ? 2 : 1.6) + t * (big ? 10 : 7.5);
	};

	// nudge lit labels apart; anything above the apex hits the network's corner label
	const CEILING = corners.A[1] - 2;
	let labelled = $derived.by(() => {
		const placed = [];
		if (!labels) return placed;
		const rowH = big ? 18 : 14;
		const colW = big ? 130 : 95;
		for (const term of terms.filter((t) => t.lit).sort((a, b) => a.py - b.py)) {
			const x = term.px + radius(term.total) + (big ? 7 : 5);
			let y = term.py + (big ? 5 : 4);
			const clashes = (candidate) =>
				placed.some(
					(o) => Math.abs(o.y - candidate) < rowH && Math.abs(o.x - x) < colW
				);
			// stack downward when a neighbour's label is in the way
			while (clashes(y)) y += rowH;
			placed.push({ ...term, x, y });
		}
		return placed;
	});

	// One dashed circle around each band's words: the smallest circle that holds
	// all their dots (a few rounds of pulling the centre toward the farthest one)
	let enclosures = $derived.by(() => {
		if (!enclose) return [];
		return bands
			.map((band) => {
				const pts = terms.filter((t) => band.words.has(t.term));
				if (!pts.length) return null;
				let cx = pts.reduce((a, t) => a + t.px, 0) / pts.length;
				let cy = pts.reduce((a, t) => a + t.py, 0) / pts.length;
				const reach = (t) => Math.hypot(t.px - cx, t.py - cy) + radius(t.total);
				let r = 0;
				for (let i = 0; i < 40; i++) {
					const far = pts.reduce(
						(a, t) => (reach(t) > reach(a) ? t : a),
						pts[0]
					);
					const d = reach(far);
					if (d <= r + 0.5) break;
					// move the centre a step toward the farthest point, grow to hold it
					const step = (d - r) / 2;
					const len = Math.hypot(far.px - cx, far.py - cy) || 1;
					cx += ((far.px - cx) / len) * step;
					cy += ((far.py - cy) / len) * step;
					r = Math.max(r, reach(far) - step, ...pts.map(reach));
				}
				return { cx, cy, r: r + (big ? 18 : 10), color: band.color };
			})
			.filter(Boolean);
	});

	// Hover snaps to the nearest word wherever the pointer is over the drawing
	let svgEl = $state(null);
	let hovered = $state(null);
	let tip = $state(null);
	function nearest(event) {
		if (!svgEl || !terms.length) return null;
		const pt = new DOMPoint(event.clientX, event.clientY).matrixTransform(
			svgEl.getScreenCTM().inverse()
		);
		let best = null,
			bestD = Infinity;
		for (const term of terms) {
			const d = (term.px - pt.x) ** 2 + (term.py - pt.y) ** 2;
			if (d < bestD) ((bestD = d), (best = term));
		}
		return best;
	}
	// the tooltip sits below the word's dot (above its label near the bottom),
	// clamped inside the drawing; percentages, so it needs no measuring
	const tipFor = (term) => {
		if (!term) return null;
		const r = radius(term.total);
		const labelRoom = big ? 44 : 24;
		const above = term.py > HEIGHT - 150;
		return {
			term,
			x: (Math.min(Math.max(term.px, 110), SIDE - 110) / SIDE) * 100,
			y:
				((above ? term.py - r - labelRoom - 10 : term.py + r + 12) / HEIGHT) *
				100,
			above
		};
	};
	function track(event) {
		hovered = nearest(event);
	}
	function leave() {
		hovered = null;
	}
	let focused = $derived(
		focus
			? (terms.find((t) => t.term === String(focus).toLowerCase()) ?? null)
			: null
	);
	// the hovered word wins; otherwise the chip being hovered in the card
	let shown = $derived(hovered ?? focused);
	$effect(() => {
		tip = tipFor(shown);
	});
	let hoverLabelled = $derived(
		labels && shown && !labelled.some((t) => t.term === shown.term)
			? shown
			: null
	);
</script>

<div class="ternary-static" class:big>
	<svg
		bind:this={svgEl}
		viewBox="0 0 {SIDE} {HEIGHT}"
		role="img"
		aria-label="Ternary plot of WNBA chyron words across Fox News, CNN and MSNBC"
		onpointermove={track}
		onpointerleave={leave}
	>
		<polygon
			class="frame"
			points="{corners.A[0]},{corners.A[1]} {corners.B[0]},{corners
				.B[1]} {corners.C[0]},{corners.C[1]}"
		/>

		<text
			class="corner"
			x={corners.A[0]}
			y={corners.A[1] - (big ? 30 : 18)}
			text-anchor="middle"
			fill={CHANNEL_COLORS[channels[0]]}>{channels[0]}</text
		>
		<text
			class="corner"
			x={corners.B[0] - (big ? 14 : 8)}
			y={corners.B[1] + (big ? 40 : 24)}
			text-anchor="start"
			fill={CHANNEL_COLORS[channels[1]]}>{channels[1]}</text
		>
		<text
			class="corner"
			x={corners.C[0] + (big ? 14 : 8)}
			y={corners.C[1] + (big ? 40 : 24)}
			text-anchor="end"
			fill={CHANNEL_COLORS[channels[2]]}>{channels[2]}</text
		>

		<!-- unlit dots first, lit ones after: the lit sit on top -->
		{#each terms.filter((t) => !t.lit) as term (term.term)}
			<circle
				class="dot"
				class:lit={term.lit}
				cx={term.px}
				cy={term.py}
				r={radius(term.total)}
				fill={term.lit ?? DOT}
				opacity={term.lit ? 1 : bands.length ? 0.22 : 0.4}
			/>
		{/each}
		{#each terms.filter((t) => t.lit) as term (term.term)}
			<circle
				class="dot"
				class:lit={term.lit}
				cx={term.px}
				cy={term.py}
				r={radius(term.total)}
				fill={term.lit ?? DOT}
				opacity={term.lit ? 1 : bands.length ? 0.22 : 0.4}
			/>
		{/each}
		<!-- one dashed circle around each band of mentioned words -->
		{#each enclosures as ring, i (i)}
			<circle
				class="enclosure"
				cx={ring.cx}
				cy={ring.cy}
				r={ring.r}
				stroke={ring.color}
			/>
		{/each}
		{#if shown}
			<circle
				class="hover-dot"
				cx={shown.px}
				cy={shown.py}
				r={radius(shown.total) + (big ? 4 : 2.5)}
				fill={shown.lit ?? hoverColor}
			/>
		{/if}

		{#each labelled as term (term.term)}
			<text
				class="word"
				x={term.x}
				y={term.y}
				text-anchor="start"
				fill={term.lit}
			>
				{term.term}
			</text>
		{/each}
		{#if hoverLabelled}
			<text
				class="word hover"
				x={hoverLabelled.px}
				y={hoverLabelled.py - radius(hoverLabelled.total) - (big ? 12 : 6)}
				text-anchor="middle"
				fill={hoverLabelled.lit ?? hoverColor}
			>
				{hoverLabelled.term}
			</text>
		{/if}
	</svg>

	{#if tip}
		<div
			class="tooltip"
			class:above={tip.above}
			style="left:{tip.x}%; top:{tip.y}%; border-left-color:{tip.term.lit ??
				'var(--color-ink)'}"
		>
			<strong>“{tip.term.term}” · {tip.term.total.toLocaleString()} uses</strong
			>
			<div class="rows">
				{#each channels as channel, i}
					<div class="row">
						<span class="who" style="color:{CHANNEL_COLORS[channel]}"
							>{channel}</span
						>
						<span class="pct"
							>{(tip.term.counts?.[i] ?? 0).toLocaleString()}
							<em>{Math.round(tip.term.shares[i] * 100)}%</em></span
						>
					</div>
				{/each}
			</div>
			{#if tip.term.ex}
				<p class="example">
					<span class="who" style="color:{CHANNEL_COLORS[tip.term.ex_ch]}"
						>{tip.term.ex_ch}</span
					>
					“{tip.term.ex}”
				</p>
			{/if}
		</div>
	{/if}
</div>

<style>
	.ternary-static {
		position: relative;
		max-width: 700px;
		margin: 0 auto;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
		overflow: visible;
	}

	.frame {
		fill: rgba(255, 253, 248, 0.35);
		stroke: rgba(42, 21, 3, 0.3);
		stroke-width: 1;
	}
	.corner {
		font-size: 15px;
		font-weight: 800;
	}
	.big .corner {
		font-size: 26px;
	}
	.dot.lit {
		stroke: var(--color-paper);
		stroke-width: 2;
	}
	.big .dot.lit {
		stroke-width: 2.5;
	}
	.hover-dot {
		stroke: var(--color-paper);
		stroke-width: 2.5;
		pointer-events: none;
	}
	.enclosure {
		fill: none;
		stroke-width: 2;
		stroke-dasharray: 7 5;
		pointer-events: none;
	}
	.word.hover {
		font-weight: 700;
	}
	.word {
		font-size: 13px;
		font-weight: 800;
		pointer-events: none;
		paint-order: stroke;
		stroke: var(--color-paper);
		stroke-width: 3.5px;
		stroke-linejoin: round;
	}
	.big .word {
		font-size: 15px;
		stroke-width: 4px;
	}
	.tooltip {
		position: absolute;
		transform: translate(-50%, 0);
		width: 200px;
		background: var(--color-paper);
		border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid var(--color-ink);
		border-radius: 3px;
		padding: 9px 12px 10px;
		box-shadow: 0 5px 20px rgba(42, 21, 3, 0.16);
		pointer-events: none;
		z-index: 5;
	}
	.tooltip.above {
		transform: translate(-50%, -100%);
	}
	.tooltip strong {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: rgba(42, 21, 3, 0.6);
	}
	.rows {
		margin-top: 6px;
	}
	.row {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12.5px;
		line-height: 1.7;
	}
	.row .who {
		font-weight: 700;
	}
	.row .pct {
		font-weight: 600;
		color: var(--color-ink);
		font-variant-numeric: tabular-nums;
	}
	.row .pct em {
		font-style: normal;
		font-weight: 400;
		color: rgba(42, 21, 3, 0.55);
		margin-left: 6px;
	}
	.example {
		margin: 7px 0 0;
		padding-top: 6px;
		border-top: 1px solid rgba(42, 21, 3, 0.12);
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11.5px;
		line-height: 1.45;
		color: rgba(42, 21, 3, 0.75);
		text-transform: uppercase;
		letter-spacing: 0.01em;
	}
	.example .who {
		font-weight: 800;
		margin-right: 4px;
	}
</style>
