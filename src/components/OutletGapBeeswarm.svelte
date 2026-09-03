<script>
	// The outlet gap as a beeswarm — same shape as FacesBeeswarm, one axis:
	// whether Fox or the sports press gives each player more of its WNBA headlines
	import { base } from "$app/paths";
	import { scaleLinear } from "d3-scale";
	import data from "$data/outlet_gap.json";
	import roster from "$data/people.json";
	const faceFiles = Object.fromEntries(
		Object.values(roster)
			.filter((p) => p.face)
			.map((p) => [p.slug, p.face.slice(p.slug.length)])
	);

	// the outlets Fox is set against — pooled for "all", one at a time from the
	// picker. Yahoo is out for now as an experiment (its 29k mostly-syndicated
	// headlines swamp the pool); put it back by adding it to this list.
	const OUTLETS = [
		"ESPN",
		"CBS Sports",
		"USA Today",
		"The Athletic",
		"Just Women's Sports"
	];
	const ALL = "the sports press";
	const LOGOS = {
		"Yahoo Sports": "yahoo.svg",
		ESPN: "espn.svg",
		"CBS Sports": "cbs-sports.svg",
		"USA Today": "usa-today.svg",
		"The Athletic": "the-athletic.png",
		"Just Women's Sports": "jws.png"
	};
	const RATIO_CAP = 9; // 10× and beyond sit at the edge
	const COUNT_WORDS = [
		"",
		"one",
		"two",
		"three",
		"four",
		"five",
		"six",
		"seven"
	];
	// "2020-01-30" -> "Jan 2020"
	const monthYear = (iso) =>
		new Date(iso + "T12:00:00").toLocaleDateString("en-US", {
			month: "short",
			year: "numeric"
		});
	const PERIOD = `${monthYear(data.window.from)} – ${monthYear(data.window.to)}`;
	const FOX = "#003366"; // Fox's own navy, as on the headline clippings
	const THEM = "#6b4bb0";

	let them = $derived(against === ALL ? "other outlets" : against);
	let { highlight = null, bare = false, against: start = ALL } = $props();
	let against = $state(start);
	// a parent may change the starting outlet later (the Doc, or a scrolly step)
	$effect(() => {
		against = start;
	});
	// the Doc types A’ja with a curly apostrophe, the data with a straight one
	const key = (name) => name.toLowerCase().replace(/[’‘]/g, "'");
	let lit = $derived(new Set((highlight ?? []).map(key)));
	const isLit = (name) => !lit.size || lit.has(key(name));

	// both numbers are already cut to the shared window
	function pressShare(person) {
		if (against !== ALL) return person.byOutlet?.[against];
		let hits = 0,
			total = 0;
		for (const outlet of OUTLETS) {
			const stat = person.byOutlet?.[outlet];
			if (!stat || !data.totals?.[outlet]) continue;
			hits += stat.n;
			total += data.totals[outlet];
		}
		return total ? { share: hits / total, n: hits } : null;
	}

	let people = $derived.by(() =>
		data.people
			.map((person) => ({ ...person, them: pressShare(person) }))
			.filter((person) => person.them && person.fox + person.them.share > 0)
			.map((person) => ({
				...person,
				balance: person.fox / (person.fox + person.them.share),
				// k× Fox -> k − 1, k× theirs -> −(k − 1): uniform either way
				times: Math.max(
					-RATIO_CAP,
					Math.min(
						RATIO_CAP,
						person.fox >= person.them.share
							? person.fox / Math.max(person.them.share, 1e-9) - 1
							: -(person.them.share / Math.max(person.fox, 1e-9) - 1)
					)
				)
			}))
	);
	let outlets = $derived(
		OUTLETS.filter((o) => data.people.some((p) => p.byOutlet?.[o]))
	);

	// "DiJonai Carrington" -> ["DiJonai", "Carrington"]: first name(s) over surname
	const nameLines = (name) => {
		const words = name.split(" ");
		return [words.slice(0, -1).join(" "), words[words.length - 1]];
	};
	const labelHalf = (d) =>
		Math.max(...d.name.split(" ").map((w) => w.length)) * 3.2 + 4;
	const slugOf = (name) =>
		name
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-|-$/g, "");

	// a narrow screen turns the box portrait so the collisions can resolve vertically
	let narrow = $state(false);
	$effect(() => {
		const query = window.matchMedia("(max-width: 640px)");
		const sync = () => (narrow = query.matches);
		sync();
		query.addEventListener("change", sync);
		return () => query.removeEventListener("change", sync);
	});

	let WIDTH = $derived(narrow ? 460 : 900);
	// taller than the framing swarm: the names under the faces need the room
	// tall: the crowd between 1× and 2× stacks vertically rather than spreading
	let HEIGHT = $derived(narrow ? 860 : 700);
	let PAD = $derived(
		narrow
			? { top: 30, right: 26, bottom: 80, left: 26 }
			: { top: 26, right: 54, bottom: 72, left: 54 }
	);

	// sized by how many Fox headlines name her, as in the framing beeswarm
	const biggest = Math.max(...data.people.map((p) => p.foxN));
	let sizeScale = $derived(
		scaleLinear()
			.domain([0, Math.sqrt(biggest)])
			.range([0, narrow ? 26 : 38])
	);
	const radiusOf = (person) =>
		(narrow ? 15 : 16) + sizeScale(Math.sqrt(person.foxN));

	// 5× theirs … 5× Fox always; stretched only when someone sits beyond that
	// (Cunningham against Just Women's Sports)
	let xScale = $derived.by(() => {
		const values = people.map((p) => p.times);
		const lo = Math.min(-4.4, Math.min(...values) - 0.4);
		const hi = Math.max(4.4, Math.max(...values) + 0.4);
		return scaleLinear()
			.domain([lo, hi])
			.range([PAD.left, WIDTH - PAD.right]);
	});

	let baselineY = $derived(HEIGHT - PAD.bottom + 6);

	// Every face sits at its exact x; overlaps are resolved by moving faces up
	// or down, never sideways, so the axis stays honest. Each face claims a box
	// as wide as itself or its name and tall enough for the name beneath it.
	const LABEL_H = 24;
	let nodes = $derived.by(() => {
		const ceiling = PAD.top + 6;
		const floor = baselineY - 8;
		const middle = (ceiling + floor) / 2;
		const boxOf = (d, y) => {
			const r = radiusOf(d);
			const w = Math.max(2 * r, 2 * labelHalf(d)) + 4;
			return { x: d.x - w / 2, w, y: y - r - 2, h: 2 * r + LABEL_H + 2 };
		};
		const clear = (b, taken) =>
			!taken.some(
				(o) =>
					b.x < o.x + o.w &&
					o.x < b.x + b.w &&
					b.y < o.y + o.h &&
					o.y < b.y + b.h
			);
		const taken = [];
		// the biggest faces take the middle first
		const order = [...people].sort(
			(a, b) =>
				radiusOf(b) - radiusOf(a) || Math.abs(a.times) - Math.abs(b.times)
		);
		const placed = [];
		for (const person of order) {
			const d = { ...person, x: xScale(person.times), y: middle };
			const r = radiusOf(d);
			const low = ceiling + r,
				high = floor - r - LABEL_H;
			let best = null;
			for (let step = 0; step < 600 && best === null; step += 3) {
				for (const y of step ? [middle - step, middle + step] : [middle]) {
					if (y < low || y > high) continue;
					if (clear(boxOf(d, y), taken)) {
						best = y;
						break;
					}
				}
			}
			if (best === null) {
				// nowhere is clear: take the slot that overlaps the least
				const overlap = (b) =>
					taken.reduce((sum, o) => {
						const w = Math.min(b.x + b.w, o.x + o.w) - Math.max(b.x, o.x);
						const h = Math.min(b.y + b.h, o.y + o.h) - Math.max(b.y, o.y);
						return sum + (w > 0 && h > 0 ? w * h : 0);
					}, 0);
				let least = Infinity;
				for (let y = low; y <= high; y += 3) {
					const area = overlap(boxOf(d, y));
					if (area < least) ((least = area), (best = y));
				}
				best ??= Math.min(high, Math.max(low, middle));
			}
			d.y = best;
			taken.push(boxOf(d, d.y));
			placed.push(d);
		}
		return placed;
	});

	let ticks = $derived.by(() => {
		const [lo, hi] = xScale.domain();
		const out = [{ at: 0, label: "1×", sub: "equal" }];
		for (let k = 1; k <= RATIO_CAP; k++) {
			if (k <= hi) out.push({ at: k, label: `${k + 1}×` });
			if (-k >= lo) out.push({ at: -k, label: `${k + 1}×` });
		}
		return out;
	});
	const pct = (share) =>
		share >= 0.1
			? `${(share * 100).toFixed(0)}%`
			: `${(share * 100).toFixed(1)}%`;

	let hovered = $state(null);
	let tooltip = $state(null);
	const HALF = 140;
	function showTooltip(event, person) {
		const box = event.currentTarget
			.closest(".outlet-gap-beeswarm")
			.getBoundingClientRect();
		hovered = person.name;
		tooltip = {
			x: Math.min(Math.max(event.clientX - box.left, HALF), box.width - HALF),
			y: event.clientY - box.top,
			person
		};
	}
	const hideTooltip = () => {
		hovered = null;
		tooltip = null;
	};

	const ringColor = (person) =>
		person.times > 0.12
			? FOX
			: person.times < -0.12
				? THEM
				: "rgba(42,21,3,0.45)";
</script>

<div class="outlet-gap-beeswarm">
	<!-- on screen and live for the whole scrolly, so the reader can switch at any step -->
	<div class="picker">
		<span class="picker-label">Fox News against</span>
		<button
			class="all"
			class:active={against === ALL}
			onclick={() => (against = ALL)}
			>all {COUNT_WORDS[outlets.length] ?? outlets.length}</button
		>
		{#each outlets as outlet}
			<button
				class:active={against === outlet}
				class:pooled={against === ALL}
				class:square={LOGOS[outlet].endsWith(".png")}
				title={outlet}
				aria-label={outlet}
				onclick={() => (against = outlet)}
			>
				<img src="{base}/logos/{LOGOS[outlet]}" alt="" />
			</button>
		{/each}
	</div>

	<svg
		viewBox="0 0 {WIDTH} {HEIGHT}"
		role="img"
		aria-label="Whether Fox News or {against} gives each player a larger share of its WNBA headlines"
	>
		<line
			class="baseline"
			x1={PAD.left}
			x2={WIDTH - PAD.right}
			y1={baselineY}
			y2={baselineY}
		/>
		{#each ticks as tick}
			<line
				class="tick"
				x1={xScale(tick.at)}
				x2={xScale(tick.at)}
				y1={baselineY}
				y2={baselineY + 4}
			/>
			<text
				class="axis"
				x={xScale(tick.at)}
				y={baselineY + 17}
				text-anchor="middle">{tick.label}</text
			>
			{#if tick.sub}
				<text
					class="axis sub"
					x={xScale(tick.at)}
					y={baselineY + 29}
					text-anchor="middle">{tick.sub}</text
				>
			{/if}
		{/each}
		<text
			class="note"
			x={(PAD.left + WIDTH - PAD.right) / 2}
			y={baselineY + 46}
			text-anchor="middle"
			>Share of each outlet's WNBA headlines naming her, {PERIOD}</text
		>
		<line
			class="zero"
			x1={xScale(0.5)}
			x2={xScale(0.5)}
			y1={PAD.top}
			y2={baselineY}
		/>
		<text
			class="end-label"
			x={PAD.left}
			y={PAD.top - 8}
			text-anchor="start"
			fill={THEM}>← More {them}</text
		>
		<text
			class="end-label"
			x={WIDTH - PAD.right}
			y={PAD.top - 8}
			text-anchor="end"
			fill={FOX}>More Fox News →</text
		>

		{#each nodes as person (person.name)}
			{@const size = radiusOf(person)}
			{@const slug = slugOf(person.name)}
			<g
				class="face"
				class:faded={hovered && hovered !== person.name}
				class:dim={!isLit(person.name)}
				onpointerenter={(e) => showTooltip(e, person)}
				onpointermove={(e) => showTooltip(e, person)}
				onpointerleave={hideTooltip}
			>
				<clipPath id="gap-swarm-{slug}">
					<circle cx={person.x} cy={person.y} r={Math.max(0, size - 1)} />
				</clipPath>
				{#if faceFiles[slug]}
					<circle cx={person.x} cy={person.y} r={size} fill="#f7f2e6" />
					<image
						href="{base}/net/{slug}{faceFiles[slug]}"
						x={person.x - size * 1.2}
						y={person.y - size * 1.05}
						width={size * 2.4}
						height={size * 2.4}
						preserveAspectRatio="xMidYMid slice"
						clip-path="url(#gap-swarm-{slug})"
					/>
				{:else}
					<circle cx={person.x} cy={person.y} r={size} fill="#d8cdb6" />
				{/if}
				<circle
					cx={person.x}
					cy={person.y}
					r={size}
					class="ring"
					style="stroke:{ringColor(person)}"
				/>
				<text
					class="label"
					class:full={lit.size && isLit(person.name)}
					x={person.x}
					y={person.y + size + 11}
					text-anchor="middle"
				>
					{#each nameLines(person.name) as line, i}
						<tspan x={person.x} dy={i ? "1.1em" : 0}>{line}</tspan>
					{/each}
				</text>
			</g>
		{/each}
	</svg>

	{#if tooltip}
		{@const person = tooltip.person}
		<div class="tip" style="left:{tooltip.x}px; top:{tooltip.y - 14}px">
			<strong>{person.name}</strong>
			<div class="stat">
				<span class="swatch" style="background:{FOX}"></span>
				{pct(person.fox)} of Fox's WNBA headlines
				<span class="count">({person.foxN.toLocaleString()})</span>
			</div>
			<div class="stat">
				<span class="swatch" style="background:{THEM}"></span>
				{pct(person.them.share)} of {them === "other outlets"
					? "the other outlets'"
					: them + "'s"}
				<span class="count">({person.them.n.toLocaleString()})</span>
			</div>
		</div>
	{/if}
</div>

<style>
	.outlet-gap-beeswarm {
		position: relative;
		max-width: 920px;
		margin: 0 auto;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
		overflow: visible;
	}

	.baseline,
	.tick {
		stroke: rgba(42, 21, 3, 0.35);
		stroke-width: 1;
	}
	.zero {
		stroke: rgba(42, 21, 3, 0.28);
		stroke-width: 1;
		stroke-dasharray: 4 4;
	}
	.axis {
		font-size: 11px;
		fill: rgba(42, 21, 3, 0.6);
	}
	.axis.sub {
		font-size: 9.5px;
		fill: rgba(42, 21, 3, 0.5);
	}
	.end-label {
		font-size: 12px;
		font-weight: 700;
	}
	.note {
		font-size: 11px;
		fill: rgba(42, 21, 3, 0.55);
	}
	.label {
		font-size: 10.5px;
		font-weight: 600;
		fill: rgba(42, 21, 3, 0.8);
		paint-order: stroke;
		stroke: rgba(249, 166, 96, 0.85);
		stroke-width: 3px;
		pointer-events: none;
	}
	.label.full {
		font-size: 12px;
		font-weight: 700;
		fill: var(--color-ink);
		stroke: rgba(255, 253, 248, 0.9);
	}

	.face {
		cursor: default;
		transition: opacity 300ms ease;
	}
	.face.faded {
		opacity: 0.25;
	}
	.face.dim {
		opacity: 0.22;
	}
	.ring {
		fill: none;
		stroke-width: 3;
	}

	.picker {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 6px;
		margin-bottom: 12px;
		flex-wrap: wrap;
	}
	.picker-label {
		font-size: 12.5px;
		color: rgba(42, 21, 3, 0.7);
		margin-right: 4px;
	}
	.picker button {
		display: inline-flex;
		align-items: center;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 999px;
		background: rgba(255, 253, 248, 0.35);
		padding: 5px 10px;
		cursor: pointer;
		font: inherit;
		font-size: 12px;
		font-weight: 600;
		line-height: 1.3;
		color: var(--color-ink);
		opacity: 0.55;
		transition:
			opacity 150ms ease,
			background 150ms ease;
	}
	.picker button:hover {
		opacity: 0.9;
	}
	/* "all five" lights every outlet, so it is clear which five */
	.picker button.pooled {
		opacity: 0.85;
	}
	.picker button.active {
		opacity: 1;
		background: rgba(255, 253, 248, 0.95);
		border-color: var(--color-ink);
		font-weight: 800;
		box-shadow: 0 1px 4px rgba(42, 21, 3, 0.18);
	}
	.picker img {
		display: block;
		height: 15px;
		width: auto;
	}
	.picker button.square img {
		height: 18px;
	}
	.picker .all {
		padding: 4px 11px;
	}

	.tip {
		position: absolute;
		transform: translate(-50%, -100%);
		background: #1a1a1a;
		color: #fff;
		font-size: 12.5px;
		line-height: 1.45;
		padding: 8px 11px;
		border-radius: 4px;
		pointer-events: none;
		width: 270px;
		z-index: 6;
		text-align: left;
	}
	.tip .stat {
		color: #d8d6cc;
		margin-top: 2px;
	}
	.tip .count {
		color: #b9b6ac;
		font-size: 11px;
	}
	.tip .swatch {
		display: inline-block;
		width: 8px;
		height: 8px;
		border-radius: 2px;
		margin-right: 5px;
	}
</style>
