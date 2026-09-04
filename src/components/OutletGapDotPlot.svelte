<script>
	// The outlet gap as a dot plot: one row per player, her face on a uniform
	// ratio axis (how many times more of Fox's WNBA headlines she is than of
	// the other outlets'). Staged for the scrolly like the beeswarm: faces
	// start on the equal line and glide out as the Doc places them.
	import { base } from "$app/paths";
	import { scaleLinear } from "d3-scale";
	import data from "$data/outlet_gap.json";
	import roster from "$data/people.json";
	import HeadlineClip from "$components/HeadlineClip.svelte";
	const faceFiles = Object.fromEntries(
		Object.values(roster)
			.filter((p) => p.face)
			.map((p) => [p.slug, p.face.slice(p.slug.length)])
	);

	// the same five as the beeswarm; Yahoo (mostly syndicated wire copy) is out
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
	const monthYear = (iso) =>
		new Date(iso + "T12:00:00").toLocaleDateString("en-US", {
			month: "short",
			year: "numeric"
		});
	const PERIOD = `${monthYear(data.window.from)} – ${monthYear(data.window.to)}`;
	const FOX = "#003366"; // Fox's own navy, as on the headline clippings
	const THEM = "#6b4bb0";
	const RATIO_CAP = 9; // 10× and beyond sit at the edge
	// left out of the dot plot for now, to keep the rows to the players the
	// piece discusses; delete names here to bring them back
	const HIDDEN = new Set([
		"Sue Bird",
		"Diana Taurasi",
		"Sabrina Ionescu",
		"Chennedy Carter",
		"Nneka Ogwumike"
	]);

	let {
		highlight = null,
		bare = false,
		against: start = ALL,
		placed = null,
		centered = [],
		// a Fox headline clipping for this step, shown under the picker; the
		// slot is kept open (clipSlot) when any step in the scrolly has one, so
		// the chart does not jump as clippings come and go
		clip = null,
		clipSlot = false,
		// collapse the slot (the explore step: nothing to quote, all chart)
		clipHidden = false,
		// the headline shown blurred while no step has chosen one — the
		// scrolly passes its first clipping; the last one shown takes over
		clipPlaceholder = null,
		// where the clipping sits: "header" — a compact card in a strip above
		// the axis headers, on the Fox half (phones fall back to "top") — or
		// "row" (on the highlighted player's row), "top" (under the pills) or
		// "bottom" (under the axis and its note)
		clipAt = "top",
		// slide the whole chart so the equal line, not the box, is centred on
		// the page (the scrolly turns this on); off on phones, where the
		// parked-faces column would leave the screen
		centerLine = false
	} = $props();
	// unplaced players wait in the column left of their name; a `centered` one
	// sits on the equal line instead, to show where equal coverage would put her
	let centeredSet = $derived(new Set((centered ?? []).map(key)));
	let against = $state(start);
	$effect(() => {
		against = start;
	});
	let them = $derived(against === ALL ? "other outlets" : against);
	// the Doc types A’ja with a curly apostrophe, the data with a straight one
	const key = (name) => name.toLowerCase().replace(/[’‘]/g, "'");
	let lit = $derived(new Set((highlight ?? []).map(key)));
	const isLit = (name) => !lit.size || lit.has(key(name));
	let placedSet = $derived(placed === null ? null : new Set(placed.map(key)));
	const isPlaced = (name) => placedSet === null || placedSet.has(key(name));

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

	// k× Fox -> k − 1, k× theirs -> −(k − 1): uniform either way
	let people = $derived(
		data.people
			.filter((person) => !HIDDEN.has(person.name))
			.map((person) => ({ ...person, them: pressShare(person) }))
			.filter((person) => person.them && person.fox + person.them.share > 0)
			.map((person) => ({
				...person,
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
			.toSorted((a, b) => b.times - a.times)
	);
	let outlets = $derived(
		OUTLETS.filter((o) => data.people.some((p) => p.byOutlet?.[o]))
	);

	const slugOf = (name) =>
		name
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-|-$/g, "");

	// height binds on desktop (sticky frame), width on a phone — hence the narrow variant
	let narrow = $state(false);
	$effect(() => {
		const query = window.matchMedia("(max-width: 640px)");
		const sync = () => (narrow = query.matches);
		sync();
		query.addEventListener("change", sync);
		return () => query.removeEventListener("change", sync);
	});

	// one size for every face; the row spacing follows it
	let R = $derived(narrow ? 20 : 21);
	const radiusOf = () => R;
	let MAX_R = $derived(R);

	// a column left of the names where unplaced faces wait, off the axis
	// entirely so they cannot be read as a value
	let LEFT = $derived(2 * R + 14);
	let NAMES = $derived(LEFT + (narrow ? 112 : 170));
	let PLOT = $derived(narrow ? 380 : 600);
	let ROW = $derived(2 * MAX_R + 8);
	// the header strip opens only when a clipping lives there
	let headerClip = $derived(
		clipAt === "header" && !narrow && Boolean(clip || clipSlot)
	);
	let TOP = $derived(44 + (headerClip ? 70 : 0));
	const BOTTOM = 62;
	let WIDTH = $derived(NAMES + PLOT + 20);
	let height = $derived(TOP + people.length * ROW + BOTTOM);

	// symmetric about equal, stretched equally both ways when someone sits
	// beyond 5× (Cunningham against Just Women's Sports)
	let x = $derived.by(() => {
		const reach = Math.max(4.4, ...people.map((p) => Math.abs(p.times) + 0.4));
		return scaleLinear()
			.domain([-reach, reach])
			.range([NAMES + 24, NAMES + PLOT]);
	});
	let rowY = $derived((index) => TOP + index * ROW + ROW / 2);
	let ticks = $derived.by(() => {
		const [lo, hi] = x.domain();
		const out = [{ at: 0, label: "1×", sub: "equal" }];
		for (let k = 1; k <= RATIO_CAP; k++) {
			if (k <= hi) out.push({ at: k, label: `${k + 1}×` });
			if (-k >= lo) out.push({ at: -k, label: `${k + 1}×` });
		}
		return out;
	});
	let axisY = $derived(height - BOTTOM + 8);
	const pct = (share) =>
		share >= 0.1
			? `${(share * 100).toFixed(0)}%`
			: `${(share * 100).toFixed(1)}%`;
	const SHORT = {
		ESPN: "ESPN",
		"CBS Sports": "CBS",
		"USA Today": "USA Today",
		"The Athletic": "Athletic",
		"Just Women's Sports": "JWS"
	};
	let themShort = $derived(
		against === ALL ? "others" : (SHORT[against] ?? against)
	);
	// "3.1× Fox" or "2.4× ESPN" — the ratio, read off for a named player so the
	// reader need not squint at the axis
	const ratioTag = (person) => {
		const k = Math.abs(person.times) + 1;
		if (Math.abs(person.times) < 0.05) return "1× (equal)";
		return `${k.toFixed(k < 10 ? 1 : 0)}× ${person.times > 0 ? "Fox" : themShort}`;
	};
	const ringColor = (person) =>
		person.times > 0.12
			? FOX
			: person.times < -0.12
				? THEM
				: "rgba(42,21,3,0.45)";

	// the row-anchored clipping: the first highlighted (or centered) player
	// who is on the axis, with the card in the half of her row her face is
	// not in. Percentages, so it scales with the drawing.
	let rowClip = $derived.by(() => {
		if (!clip || clipAt !== "row" || narrow) return null;
		const index = people.findIndex(
			(p) =>
				(lit.has(key(p.name)) || centeredSet.has(key(p.name))) &&
				(isPlaced(p.name) || centeredSet.has(key(p.name)))
		);
		if (index < 0) return null;
		const person = people[index];
		const onFox = isPlaced(person.name) ? person.times >= 0 : false;
		const gap = 14;
		const left = onFox ? NAMES + 24 : x(0) + gap;
		const right = onFox ? x(0) - gap : NAMES + PLOT;
		return {
			top: (rowY(index) / height) * 100,
			left: (left / WIDTH) * 100,
			width: ((right - left) / WIDTH) * 100
		};
	});
	let clipSlotWanted = $derived(
		(clip || clipSlot) &&
			(clipAt === "top" ||
				((clipAt === "row" || clipAt === "header") && narrow))
	);
	// the header strip card: the Fox half, from the equal line to the plot's edge
	let headerCard = $derived(
		headerClip && clip
			? {
					left: ((x(0) + 6) / WIDTH) * 100,
					width: ((NAMES + PLOT - x(0) - 6) / WIDTH) * 100
				}
			: null
	);

	// the card always shows a headline: this step's, else the last one shown
	// (blurred), else the placeholder (blurred)
	let lastClip = $state(null);
	$effect(() => {
		if (clip) lastClip = clip;
	});
	// no placeholder before the first clipping: the slot stays empty until one
	// arrives, then keeps the last one (blurred) between steps
	let shownClip = $derived(clip ?? lastClip);

	// Where the equal line really is on screen. In the scrolly the drawing is
	// height-bound and scaled down inside a wider box, so a viewBox percentage
	// would miss; measure the rendered SVG instead.
	let svgEl = $state(null);
	let equalLeft = $state(null);
	let shift = $state(0);
	$effect(() => {
		if (!svgEl) return;
		const measure = () => {
			const r = svgEl.getBoundingClientRect();
			if (!r.width || !r.height) return;
			const scale = Math.min(r.width / WIDTH, r.height / height);
			const offset = (r.width - WIDTH * scale) / 2;
			equalLeft = offset + x(0) * scale;
			if (!centerLine || narrow) {
				shift = 0;
				return;
			}
			// how far left the box must move for the line to sit at its centre,
			// but never past the viewport's left edge
			const box = svgEl.closest(".outlet-gap").getBoundingClientRect();
			const baseLeft = box.left - shift;
			shift = Math.max(box.width / 2 - equalLeft, -(baseLeft - 8));
		};
		measure();
		const ro = new ResizeObserver(measure);
		ro.observe(svgEl);
		return () => ro.disconnect();
	});

	let hovered = $state(null);
	let tooltip = $state(null);
	function showFace(event, person) {
		const box = event.currentTarget
			.closest(".outlet-gap")
			.getBoundingClientRect();
		const half = 140;
		tooltip = {
			x: Math.min(Math.max(event.clientX - box.left, half), box.width - half),
			y: event.clientY - box.top,
			person
		};
	}
	const hideFace = () => (tooltip = null);
</script>

<div
	class="outlet-gap"
	style:transform={shift ? `translateX(${shift}px)` : undefined}
>
	<!-- on screen and live for the whole scrolly, so the reader can switch at any step -->
	<!-- the matchup as a title, centred on the equal line; the pills below switch it -->
	<div
		class="head"
		style="--equal: {equalLeft === null
			? `${(x(0) / WIDTH) * 100}%`
			: `${equalLeft}px`}"
	>
		<h4 class="vs">Fox News vs. {against === ALL ? "All Outlets" : against}</h4>
		<div class="picker">
			<button
				class="all"
				class:active={against === ALL}
				onclick={() => (against = ALL)}>all</button
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
	</div>

	{#if clipSlotWanted}
		<div class="clip-slot" class:collapsed={clipHidden}>
			{#if shownClip}
				<div class="slot-card">
					<HeadlineClip clip={shownClip} rot={-1} compact blurred={!clip} />
				</div>
			{/if}
		</div>
	{/if}

	<div class="plot">
		<svg
			bind:this={svgEl}
			viewBox="0 0 {WIDTH} {height}"
			role="img"
			aria-label="Whether Fox News or {against} gives each player a larger share of its WNBA headlines"
		>
			<text
				class="head"
				x={x(0) - 14}
				y={TOP - 22}
				text-anchor="end"
				fill={THEM}>← More {them}</text
			>
			<text class="head" x={x(0) + 14} y={TOP - 22} fill={FOX}
				>More Fox News →</text
			>
			{#each ticks as tick}
				{#if tick.at === 0}
					<line
						class="grid"
						class:middle={tick.at === 0}
						x1={x(tick.at)}
						x2={x(tick.at)}
						y1={TOP - 14}
						y2={axisY}
					/>
				{/if}
				<text class="tick" x={x(tick.at)} y={axisY + 16} text-anchor="middle"
					>{tick.label}</text
				>
				{#if tick.sub}
					<text
						class="tick sub"
						x={x(tick.at)}
						y={axisY + 27}
						text-anchor="middle">{tick.sub}</text
					>
				{/if}
			{/each}
			<text
				class="note"
				x={(NAMES + 24 + NAMES + PLOT) / 2}
				y={axisY + 46}
				text-anchor="middle"
				>Share of each outlet's WNBA headlines naming her, {PERIOD}</text
			>

			{#each people as person, index (person.name)}
				{@const slug = slugOf(person.name)}
				{@const y = rowY(index)}
				{@const r = radiusOf(person)}
				{@const on = isPlaced(person.name)}
				<!-- a centered player is shown bright, named or not: she is the point of the step -->
				{@const named =
					(lit.size > 0 && isLit(person.name)) ||
					centeredSet.has(key(person.name))}
				<g
					class="row"
					class:lit={hovered === person.name}
					class:dim={on && !isLit(person.name)}
					class:waiting={!on && !named}
					onmouseenter={() => (hovered = person.name)}
					onmouseleave={() => (hovered = null)}
					role="presentation"
				>
					<line class="guide" x1={NAMES + 8} x2={NAMES + PLOT} y1={y} y2={y} />
					<text
						class="name"
						class:short={narrow}
						x={NAMES}
						y={y + 4.5}
						text-anchor="end"
					>
						{narrow ? person.name.split(" ").slice(-1)[0] : person.name}
					</text>

					<g
						class="face-mark"
						style:transform="translate({on
							? x(person.times)
							: centeredSet.has(key(person.name))
								? x(0)
								: LEFT / 2}px, {y}px)"
						onpointerenter={(e) => on && showFace(e, person)}
						onpointermove={(e) => on && showFace(e, person)}
						onpointerleave={hideFace}
						role="presentation"
					>
						<clipPath id="gap-clip-{slug}">
							<circle cx="0" cy="0" r={Math.max(0, r - 1)} />
						</clipPath>
						{#if faceFiles[slug]}
							<circle cx="0" cy="0" {r} fill="#f7f2e6" />
							<image
								href="{base}/net/{slug}{faceFiles[slug]}"
								x={-r * 1.2}
								y={-r * 1.05}
								width={r * 2.4}
								height={r * 2.4}
								clip-path="url(#gap-clip-{slug})"
								preserveAspectRatio="xMidYMid slice"
							/>
						{:else}
							<circle cx="0" cy="0" {r} fill="#d8cdb6" />
						{/if}
						<circle
							cx="0"
							cy="0"
							{r}
							class="ring"
							style="stroke:{ringColor(person)}"
						/>
						{#if !on && !named}
							<!-- waiting on the equal line: veiled, unless this step names her -->
							<circle cx="0" cy="0" r={r + 1.5} class="veil" />
						{/if}
						{#if on && (named || hovered === person.name)}
							<text
								class="ratio"
								x={person.times >= 0 ? r + 9 : -r - 9}
								y="4.5"
								text-anchor={person.times >= 0 ? "start" : "end"}
								fill={ringColor(person)}>{ratioTag(person)}</text
							>
						{/if}
					</g>
				</g>
			{/each}
		</svg>
		{#if headerCard}
			<div
				class="header-clip"
				style="left:{headerCard.left}%; width:{headerCard.width}%"
			>
				<HeadlineClip {clip} rot={-0.8} compact />
			</div>
		{/if}
		{#if rowClip}
			<div
				class="row-clip"
				style="top:{rowClip.top}%; left:{rowClip.left}%; width:{rowClip.width}%"
			>
				<HeadlineClip {clip} rot={-1} small />
			</div>
		{/if}
	</div>

	{#if (clip || clipSlot) && clipAt === "bottom"}
		<div class="clip-slot bottom">
			{#if clip}<HeadlineClip {clip} rot={-1} small />{/if}
		</div>
	{/if}

	{#if tooltip}
		<div class="tip" style="left:{tooltip.x}px; top:{tooltip.y - 22}px">
			<strong>{tooltip.person.name}</strong>
			<div>
				<span class="swatch" style="background:{FOX}"></span>
				{pct(tooltip.person.fox)} of Fox's WNBA headlines
				<span class="count">({tooltip.person.foxN.toLocaleString()})</span>
			</div>
			<div>
				<span class="swatch" style="background:{THEM}"></span>
				{pct(tooltip.person.them.share)} of {them === "other outlets"
					? "the other outlets'"
					: them + "'s"}
				<span class="count">({tooltip.person.them.n.toLocaleString()})</span>
			</div>
		</div>
	{/if}
</div>

<style>
	.outlet-gap {
		position: relative;
		max-width: 860px;
		margin: 0 auto;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
		overflow: visible;
	}

	.tip {
		position: absolute;
		transform: translate(-50%, -100%);
		background: #1a1a1a;
		color: #fff;
		font-size: 12.5px;
		line-height: 1.5;
		padding: 8px 11px;
		border-radius: 4px;
		pointer-events: none;
		width: 270px;
		z-index: 6;
		text-align: left;
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

	.picker {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 5px;
		margin-bottom: 6px;
		flex-wrap: nowrap;
	}
	/* title and pills sit centred over the equal line, not the whole box */
	.head {
		position: relative;
	}
	.head > * {
		position: relative;
		left: var(--equal, 50%);
		transform: translateX(-50%);
		width: max-content;
		/* no wider than fits centred on the line: twice the nearer margin */
		max-width: min(
			calc(2 * (100% - var(--equal, 50%))),
			calc(2 * var(--equal, 50%))
		);
	}
	.vs {
		text-align: center;
		font-size: 30px;
		font-weight: 800;
		line-height: 1.15;
		margin: 0 0 10px;
		color: var(--color-ink);
	}
	@media (max-width: 640px) {
		.vs {
			font-size: 24px;
		}
	}
	.picker button {
		display: inline-flex;
		align-items: center;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 999px;
		background: rgba(255, 253, 248, 0.35);
		padding: 3px 8px;
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
		height: 12px;
		width: auto;
	}
	.picker button.square img {
		height: 15px;
	}
	.picker .all {
		padding: 3px 9px;
		font-size: 11px;
	}
	/* a phone: the pills shrink, and wrap to stay centred on the line */
	@media (max-width: 640px) {
		.picker {
			gap: 3px;
			flex-wrap: wrap;
			justify-content: center;
		}
		.picker button {
			padding: 2px 6px;
		}
		.picker .all {
			padding: 2px 7px;
			font-size: 10px;
		}
		.picker img {
			height: 10px;
		}
		.picker button.square img {
			height: 12px;
		}
	}
	.slot-card {
		width: 100%;
		animation: slide-in 700ms cubic-bezier(0.22, 0.8, 0.3, 1);
	}
	@keyframes slide-in {
		from {
			opacity: 0;
			transform: translateX(40vw);
		}
	}
	.clip-slot {
		min-height: 50px;
		display: flex;
		justify-content: center;
		align-items: center;
		margin: 0 auto 4px;
		max-width: 380px;
	}
	.clip-slot {
		overflow: hidden;
		max-height: 80px;
		transition:
			max-height 450ms ease,
			opacity 300ms ease,
			margin 450ms ease,
			min-height 450ms ease;
	}
	.clip-slot.collapsed {
		max-height: 0;
		min-height: 0;
		opacity: 0;
		margin-bottom: 0;
	}
	.clip-slot.bottom {
		margin: 8px auto 0;
	}
	.plot {
		position: relative;
	}
	.row-clip {
		position: absolute;
		transform: translateY(-50%);
		display: flex;
		justify-content: center;
		pointer-events: none;
		transition: top 900ms cubic-bezier(0.22, 0.8, 0.3, 1);
	}
	.row-clip :global(.clip) {
		width: 100%;
		max-width: 330px;
		box-sizing: border-box;
	}
	.header-clip {
		position: absolute;
		top: 0;
		pointer-events: none;
	}
	.header-clip :global(.clip) {
		width: 100%;
		box-sizing: border-box;
	}
	.clip-slot :global(.clip) {
		width: 100%;
	}

	.head {
		font-size: 12.5px;
		font-weight: 800;
	}
	.grid {
		stroke: rgba(42, 21, 3, 0.2);
		stroke-width: 1;
	}
	.grid.middle {
		stroke: rgba(42, 21, 3, 0.5);
		stroke-dasharray: 4 4;
	}
	.guide {
		stroke: rgba(42, 21, 3, 0.3);
		stroke-width: 1;
		stroke-dasharray: 3 4;
	}
	.tick {
		font-size: 12.5px;
		font-weight: 600;
		fill: rgba(42, 21, 3, 0.72);
	}
	.ratio {
		font-size: 13.5px;
		font-weight: 800;
		paint-order: stroke;
		stroke: var(--color-page-orange, #f9a660);
		stroke-width: 4px;
		stroke-linejoin: round;
	}
	.tick.sub {
		font-size: 9.5px;
		fill: rgba(42, 21, 3, 0.5);
	}
	.note {
		font-size: 11px;
		fill: rgba(42, 21, 3, 0.55);
	}

	.name {
		font-size: 13.5px;
		fill: rgba(42, 21, 3, 0.85);
	}
	.name.short {
		font-size: 17px;
	}
	.row.lit .name {
		fill: var(--color-ink);
		font-weight: 700;
	}
	.row {
		transition: opacity 300ms ease;
	}
	.row.dim {
		opacity: 0.22;
	}
	/* not yet placed: on the equal line, veiled, name faded */
	.row.waiting .name {
		opacity: 0.45;
	}
	.veil {
		fill: var(--color-page-orange, #f9a660);
		opacity: 0.72;
	}

	.face-mark {
		cursor: default;
		transition: transform 900ms cubic-bezier(0.22, 0.8, 0.3, 1);
	}
	@media (prefers-reduced-motion: reduce) {
		.face-mark {
			transition: none;
		}
	}
	.ring {
		fill: none;
		stroke-width: 3;
	}
	.row.lit .ring {
		stroke-width: 3.5;
	}
</style>
