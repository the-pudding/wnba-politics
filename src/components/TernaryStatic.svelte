<script>
	// Static chyron ternary
	import chyData from "$data/chyrons.json";
	import capData from "$data/captions.json";
	// the piece's topic vocabularies, for `topic:` (the same file the outlet
	// panels count with)
	import termRows from "../../data/topic_terms.csv";
	// the same words counted by year, for the timeline
	import chyYears from "$data/chyron_ternary_years.json";
	import capYears from "$data/captions_years.json";


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
		minTotal = 0,
		// topic: "polrace" or "lgbtq" — light that vocabulary's words and shade
		// the triangle where they cluster, weighted by how often they ran
		topic = null,
		// note: the line under the triangle, from the Doc; {period} stands for
		// the months the chyrons cover. Empty string: no line.
		note = null,
		// timeline: a play button and year buttons; the words take their places
		// from the chyrons up to the chosen year. A parent (the pair) can hold
		// the year itself and hide the buttons with controls={false}
		timeline = false,
		controls = true,
		year = $bindable(null), // null: every year
		// source: "chyrons" (the banners, 2017–2026) or "captions" (what was
		// said, from the closed captions, 2017 to Oct 2024)
		source = "chyrons"
	} = $props();
	// fixed for the life of the chart: the Doc sets it
	const chy = source === "captions" ? capData : chyData;
	const yearly = source === "captions" ? capYears : chyYears;
	// the span of the data, for the line under the triangle
	const monthName = (ym) =>
		new Date(+ym.slice(0, 4), +ym.slice(5) - 1, 1).toLocaleString("en-US", {
			month: "long",
			year: "numeric"
		});
	const PERIOD = `${monthName(chy.months[0])}–${monthName(chy.months.at(-1))}`;

	// --- the timeline -------------------------------------------------------
	const YEARS = (yearly.years ?? []).filter((y) => y >= "2018");
	let timelineOn = $derived(timeline === true || timeline === "true");
	let playing = $state(false);
	let playTimer = null;
	const YEAR_MS = 1400;
	function stopPlay() {
		clearInterval(playTimer);
		playTimer = null;
		playing = false;
	}
	function togglePlay() {
		if (playing) return stopPlay();
		playing = true;
		year = YEARS[0];
		playTimer = setInterval(() => {
			const i = YEARS.indexOf(year);
			if (i < 0 || i >= YEARS.length - 1) {
				stopPlay();
				year = null; // the end: every year together again
				return;
			}
			year = YEARS[i + 1];
		}, YEAR_MS);
	}
	$effect(() => () => clearInterval(playTimer));
	// each word's counts and the channels' totals, summed through the year
	let throughYear = $derived.by(() => {
		if (!timelineOn || !year) return null;
		const upTo = (yearly.years ?? []).filter((y) => y <= year);
		const totals = yearly.channels.map((_, i) =>
			upTo.reduce((sum, y) => sum + (yearly.totals[y]?.[i] ?? 0), 0)
		);
		const counts = {};
		for (const [term, byYear] of Object.entries(yearly.terms ?? {})) {
			const c = yearly.channels.map((_, i) =>
				upTo.reduce((sum, y) => sum + (byYear[y]?.[i] ?? 0), 0)
			);
			if (c.some(Boolean)) counts[term] = c;
		}
		return { totals, counts };
	});
	const meta = new Map((chy.ternary ?? []).map((t) => [t.term, t]));

	// --- a topic's words and heat -------------------------------------------
	const TOPIC_TERMS = {
		polrace: ["race / racism", "politics / protest"],
		lgbtq: ["LGBTQ / sexuality", "transgender / trans"],
		// the contact words (the Sheet's "fouls" topic): hip-check, punch, throat…
		fouls: ["fouls"]
	};
	const TOPIC_COLOR = {
		polrace: "var(--color-politics)",
		lgbtq: "var(--color-lgbtq)",
		fouls: "#7a4a00"
	};
	const TOPIC_PHRASE = {
		polrace: "race, politics and protest",
		lgbtq: "LGBTQ+ and trans athletes",
		fouls: "fouls and physical play"
	};
	// chyron words are single tokens, so a vocabulary phrase like "trans athlete"
	// never matches on its own; the bare word carries the topic here
	const TOPIC_EXTRA = { lgbtq: ["trans"], polrace: [], fouls: [] };
	let topicRx = $derived(
		topic && TOPIC_TERMS[topic]
			? new RegExp(
					termRows
						.filter((r) => TOPIC_TERMS[topic].includes(r.topic))
						.map((r) => r.term)
						.join("|"),
					"i"
				)
			: null
	);

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
	let bands = $derived([
		...(groups.length ? groups : words.length ? [words] : []).map((band, i) => ({
			words: new Set(band.map((w) => w.toLowerCase())),
			color: highlightColor ?? GROUP_COLORS[i % GROUP_COLORS.length]
		})),
		// the topic's words form a band of their own, in the topic's colour
		...(topicRx
			? [
					{
						words: new Set(
							(chy.ternary ?? [])
								.filter(
									(t) =>
										topicRx.test(t.term) ||
										(TOPIC_EXTRA[topic] ?? []).includes(t.term)
								)
								.map((t) => t.term)
						),
						color: TOPIC_COLOR[topic],
						topic: true
					}
				]
			: [])
	]);
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

	let terms = $derived.by(() => {
		const floor = Math.max(MIN_TOTAL, minTotal);
		if (throughYear) {
			// placed from the counts through the chosen year, the way the
			// notebook places them for all years: each channel's rate of use,
			// normalised across the three
			const out = [];
			for (const [term, counts] of Object.entries(throughYear.counts)) {
				const total = counts.reduce((a, b) => a + b, 0);
				if (total < floor) continue;
				const rates = counts.map((n, i) => n / Math.max(throughYear.totals[i], 1));
				const ssum = rates.reduce((a, b) => a + b, 0);
				if (!ssum) continue;
				const shares = rates.map((r) => r / ssum);
				const [px, py] = bary(shares);
				const m = meta.get(term) ?? {};
				out.push({ term, total, counts, shares, ex: m.ex, ex_ch: m.ex_ch, px, py, lit: bandFor(term) });
			}
			return out;
		}
		return (chy.ternary ?? [])
			.filter((t) => t.total >= floor)
			.map((t) => {
				const [px, py] = bary(t.shares);
				return { ...t, px, py, lit: bandFor(t.term) };
			});
	});
	let biggest = $derived(Math.max(1, ...terms.map((t) => t.total)));
	// dot size runs on a log scale: "griner" (7,000 uses) would otherwise dwarf
	// everything, leaving a 200-use word like "foul" as a speck
	let smallest = $derived(Math.max(1, Math.min(...terms.map((t) => t.total))));
	const radius = (total) => {
		const span = Math.log(Math.max(2, biggest / smallest));
		const t = Math.log(Math.max(1, total / smallest)) / span; // 0 … 1
		return (big ? 2 : 1.6) + t * (big ? 10 : 7.5);
	};

	// the heat: the triangle cut into a lattice of small triangles, each shaded
	// by how many uses of the topic's words fall near it (a Gaussian kernel,
	// so a word's weight spreads to its neighbours)
	const HEAT_N = 30;
	const HEAT_H = 38; // the kernel's width, in drawing px
	let heatCells = $derived.by(() => {
		if (!topicRx) return [];
		const pts = terms.filter((t) => t.lit === TOPIC_COLOR[topic]);
		if (!pts.length) return [];
		const P = (i, j) => [
			corners.A[0] + (i / HEAT_N) * (corners.B[0] - corners.A[0]) + (j / HEAT_N) * (corners.C[0] - corners.A[0]),
			corners.A[1] + (i / HEAT_N) * (corners.B[1] - corners.A[1]) + (j / HEAT_N) * (corners.C[1] - corners.A[1])
		];
		const cells = [];
		const add = (a, b, c) => {
			const cx = (a[0] + b[0] + c[0]) / 3;
			const cy = (a[1] + b[1] + c[1]) / 3;
			let w = 0;
			for (const t of pts) {
				const d2 = (t.px - cx) ** 2 + (t.py - cy) ** 2;
				w += t.total * Math.exp(-d2 / (2 * HEAT_H * HEAT_H));
			}
			cells.push({ d: `M${a[0]},${a[1]}L${b[0]},${b[1]}L${c[0]},${c[1]}Z`, w });
		};
		for (let i = 0; i < HEAT_N; i++)
			for (let j = 0; j < HEAT_N - i; j++) {
				add(P(i, j), P(i + 1, j), P(i, j + 1));
				if (i + j < HEAT_N - 1) add(P(i + 1, j), P(i + 1, j + 1), P(i, j + 1));
			}
		const peak = Math.max(...cells.map((c) => c.w));
		return cells
			.map((c) => ({ d: c.d, o: 0.8 * Math.pow(c.w / peak, 0.6) }))
			.filter((c) => c.o > 0.03);
	});

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
			.filter((band) => !band.topic)
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
		// on a topic triangle the grey words are context: only the counted
		// (lit) words take a tooltip
		const candidates = topicRx ? terms.filter((x) => x.lit) : terms;
		for (const term of candidates) {
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
	// a tap on the drawing shows the nearest word (touch never hovers); a click
	// anywhere else takes it away again
	function away(event) {
		if (svgEl && !svgEl.contains(event.target)) hovered = null;
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

<svelte:window onclick={away} />

<div class="ternary-static" class:big class:timeline={timelineOn}>
	{#if timelineOn && controls}
		<!-- the years: play runs through them; a button jumps to one; "all" is
		     the whole span -->
		<div class="years">
			<button
				class="play"
				onclick={togglePlay}
				aria-label={playing ? "Pause" : "Play"}>{playing ? "❚❚" : "▶"}</button
			>
			<div class="year-buttons" role="group" aria-label="Through which year">
				{#each YEARS as y (y)}
					<button
						class:on={year === y}
						onclick={() => {
							stopPlay();
							year = y;
						}}>{y}</button
					>
				{/each}
				<button
					class:on={year === null}
					onclick={() => {
						stopPlay();
						year = null;
					}}>all</button
				>
			</div>
		</div>
	{/if}
	<svg
		bind:this={svgEl}
		viewBox="0 0 {SIDE} {HEIGHT}"
		role="img"
		aria-label="Ternary plot of WNBA chyron words across Fox News, CNN and MSNBC"
		onpointermove={track}
		onpointerdown={track}
		onpointerleave={leave}
	>
		<polygon
			class="frame"
			points="{corners.A[0]},{corners.A[1]} {corners.B[0]},{corners
				.B[1]} {corners.C[0]},{corners.C[1]}"
		/>
		<!-- the topic's heat, under the dots -->
		{#if heatCells.length}
			<g
				class="heat"
				fill={TOPIC_COLOR[topic]}
				shape-rendering="crispEdges"
				style="pointer-events:none"
			>
				{#each heatCells as c}
					<path d={c.d} opacity={c.o} />
				{/each}
			</g>
		{/if}

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

		{#if timelineOn}
			<text class="year-stamp" x={PAD} y={corners.A[1] + 8} text-anchor="start"
				>{year ? `through ${year}` : "all years"}</text
			>
		{/if}
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
	<!-- what the triangle covers: the months in the chyron data -->
	{#if note !== ""}
		<p class="period">
			{#if note}
				{@html note.replaceAll("{period}", PERIOD)}
			{:else if source === "captions"}
				Cable news closed captions, {PERIOD}, from the TV News Archive via
				GDELT: a word counts once per caption clip.
				{#if topicRx}
					Shaded where the words about {TOPIC_PHRASE[topic]} cluster, darker
					the more they were said.
				{/if}
			{:else}
				Cable news chyrons, {PERIOD}, from the Internet Archive’s Third Eye.
				{#if topicRx}
					Shaded where the words about {TOPIC_PHRASE[topic]} cluster, darker
					the more they ran.
				{/if}
			{/if}
		</p>
	{/if}

	{#if tip}
		<div
			class="tooltip"
			class:above={tip.above}
			style="left:{tip.x}%; top:{tip.y}%; border-left-color:{tip.term.lit ??
				'var(--color-ink)'}"
		>
			<strong
				>“{tip.term.term}” · {tip.term.total.toLocaleString()} total uses</strong
			>
			<div class="rows">
				{#each channels as channel, i}
					<div class="row">
						<span class="who" style="color:{CHANNEL_COLORS[channel]}"
							>{channel}</span
						>
						<!-- each outlet's share of the word's uses; the counts stay in the data -->
						<span class="pct">{Math.round(tip.term.shares[i] * 100)}%</span>
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
	/* on the timeline the dots glide to their next places */
	.timeline .dot {
		transition:
			cx 900ms cubic-bezier(0.3, 0, 0.2, 1),
			cy 900ms cubic-bezier(0.3, 0, 0.2, 1),
			r 900ms ease;
	}
	.timeline .heat path {
		transition: opacity 900ms ease;
	}
	.year-stamp {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 13px;
		font-weight: 800;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		fill: rgba(42, 21, 3, 0.45);
	}
	.years {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		margin: 2px 0 4px;
		flex-wrap: wrap;
	}
	.years .play {
		width: 30px;
		height: 26px;
		border: 0;
		border-radius: 5px;
		background: var(--color-ink);
		color: #fff;
		font-size: 11px;
		cursor: pointer;
	}
	.year-buttons {
		display: inline-flex;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 5px;
		overflow: hidden;
	}
	.year-buttons button {
		border: 0;
		background: transparent;
		color: var(--color-ink);
		font: inherit;
		font-size: 12px;
		font-weight: 700;
		padding: 4px 7px;
		cursor: pointer;
	}
	.year-buttons button.on {
		background: var(--color-ink);
		color: #fff;
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
	.period {
		margin: 4px 0 0;
		font-size: 12px;
		line-height: 1.4;
		text-align: center;
		color: rgba(42, 21, 3, 0.6);
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
