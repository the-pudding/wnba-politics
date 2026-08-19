<script>
	// ---------------------------------------------------------------------------
	// Who does Fox cover that the sports press doesn't?
	//
	// Raw counts can't answer that — Yahoo published 37,275 WNBA headlines to
	// Fox's 2,064 — so each player is measured as a SHARE of that outlet's WNBA
	// headlines, and then the two shares are set against each other.
	//
	// One axis, one face per player. A player at the centre gets the same slice
	// of Fox's attention as she gets from the sports press; the further right,
	// the more Fox is the outlet that writes about her. That balance is the whole
	// claim, so the chart shows it directly rather than making the reader
	// subtract two bars.
	//
	// Doc embed:  chart: outlet-gap
	// ---------------------------------------------------------------------------
	import { base } from "$app/paths";
	import { scaleLinear } from "d3-scale";
	import data from "$data/outlet_gap.json";
	import faceFiles from "$data/net_faces.json";

	const OUTLETS = ["Yahoo Sports", "ESPN", "CBS Sports", "USA Today"];
	const ALL = "the sports press";
	const LOGOS = {
		"Yahoo Sports": "yahoo", "ESPN": "espn",
		"CBS Sports": "cbs-sports", "USA Today": "usa-today"
	};
	const LOGO_WIDTH = { "Yahoo Sports": 46, "ESPN": 44, "CBS Sports": 46, "USA Today": 60 };
	const FOX = "#003366";        // Fox's own navy, as on the headline clippings
	const THEM = "#6b4bb0";

	let against = $state(ALL);
	// A scrollytelling wrapper calls out a few players at a time; with nothing
	// passed every row reads at full strength.
	let { highlight = null, bare = false } = $props();
	let lit = $derived(new Set((highlight ?? []).map((n) => n.toLowerCase())));
	const isLit = (name) => !lit.size || lit.has(name.toLowerCase());

	// the four archives pooled: her headlines across all of them, over their
	// combined size. Both numbers are already cut to the shared window.
	function pressShare(person) {
		if (against !== ALL) return person.byOutlet?.[against];
		let hits = 0, total = 0;
		for (const outlet of OUTLETS) {
			const stat = person.byOutlet?.[outlet];
			if (!stat || !data.totals?.[outlet]) continue;
			hits += stat.n;
			total += data.totals[outlet];
		}
		return total ? { share: hits / total, n: hits } : null;
	}

	let people = $derived.by(() => {
		// headlines only: the full-text variant covered fewer outlets and the
		// switch cost more attention than the second reading was worth
		return data.people
			.map((person) => ({ ...person, them: pressShare(person) }))
			.filter((person) => person.them && person.fox + person.them.share > 0)
			// the balance: 1 = only Fox writes about her, 0 = only they do
			.map((person) => ({ ...person, balance: person.fox / (person.fox + person.them.share) }))
			.toSorted((a, b) => b.balance - a.balance);
	});
	let outlets = $derived(OUTLETS.filter((o) => data.people.some((p) => p.byOutlet?.[o])));

	const slugOf = (name) => name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

	// --- geometry ---------------------------------------------------------------
	// Which dimension binds decides the proportions, and it isn't the same one on
	// every screen.
	//
	// On a desktop this sits in a sticky frame, so HEIGHT binds: at the old
	// 718x894 the browser scaled the chart down to about 610px wide and the faces
	// landed smaller than they are drawn. A wider, shorter viewBox buys a much
	// larger chart out of the same vertical budget.
	//
	// On a phone WIDTH binds, and that same wide viewBox works against us — every
	// unit gets scaled down harder, shrinking the faces. So a narrow screen gets a
	// tighter box, surnames instead of full names, and three ticks instead of five.
	let narrow = $state(false);
	$effect(() => {
		const query = window.matchMedia("(max-width: 640px)");
		const sync = () => (narrow = query.matches);
		sync();
		query.addEventListener("change", sync);
		return () => query.removeEventListener("change", sync);
	});

	let NAMES = $derived(narrow ? 112 : 170);   // right-aligned label column
	let PLOT = $derived(narrow ? 380 : 600);
	let ROW = $derived(narrow ? 44 : 48);
	let FACE = $derived(narrow ? 40 : 42);      // rows clear the ring: FACE/2 + 2.5
	const TOP = 44;
	const BOTTOM = 40;
	let WIDTH = $derived(NAMES + PLOT + 20);

	let height = $derived(TOP + people.length * ROW + BOTTOM);
	let x = $derived(scaleLinear().domain([0, 1]).range([NAMES + 24, NAMES + PLOT]));
	let rowY = $derived((index) => TOP + index * ROW + ROW / 2);

	const ALL_TICKS = [
		{ at: 0, label: "all theirs" },
		{ at: 0.25, label: "3× theirs" },
		{ at: 0.5, label: "equal" },
		{ at: 0.75, label: "3× Fox" },
		{ at: 1, label: "all Fox" }
	];
	// five labels won't fit across a phone without colliding
	let TICKS = $derived(narrow ? ALL_TICKS.filter((t) => t.at % 0.5 === 0) : ALL_TICKS);
	const pct = (share) =>
		share >= 0.1 ? `${(share * 100).toFixed(0)}%` : `${(share * 100).toFixed(1)}%`;

	let hovered = $state(null);
	let tooltip = $state(null);

	function showFace(event, person) {
		const box = event.currentTarget.closest(".outlet-gap").getBoundingClientRect();
		const half = 140;
		tooltip = {
			x: Math.min(Math.max(event.clientX - box.left, half), box.width - half),
			y: event.clientY - box.top,
			person
		};
	}
	const hideFace = () => (tooltip = null);
</script>

<div class="outlet-gap">
	{#if !bare}
	<div class="picker">
		<span class="picker-label">Fox News against</span>
		<button class="all" class:active={against === ALL} onclick={() => (against = ALL)}>all four</button>
		{#each outlets as outlet}
			<button class:active={against === outlet} onclick={() => (against = outlet)}>
				<img src="{base}/logos/{LOGOS[outlet]}.svg" alt={outlet}
					style="width:{LOGO_WIDTH[outlet] * 0.8}px" />
			</button>
		{/each}
	</div>
	{/if}

	<svg viewBox="0 0 {WIDTH} {height}" role="img"
		aria-label="Whether Fox News or {against} gives each player a larger share of its WNBA headlines">
		<!-- the two directions, named by the outlets' own marks -->
		<!-- the logos sit on their own line, above the two direction labels, or the
		     wordmarks run straight into the text -->
		<text class="head" x={x(0.5) - 14} y="22" text-anchor="end" fill={THEM}>← more of theirs</text>
		<text class="head" x={x(0.5) + 14} y="22" fill={FOX}>more of Fox's →</text>
		<!-- vertical rules, and the axis read twice so it is near every row -->
		{#each TICKS as tick}
			<line class="grid" class:middle={tick.at === 0.5}
				x1={x(tick.at)} x2={x(tick.at)} y1={TOP - 14} y2={height - BOTTOM + 8} />
			<text class="tick" x={x(tick.at)} y={height - BOTTOM + 24} text-anchor="middle">{tick.label}</text>
		{/each}

		{#each people as person, index (person.name)}
			{@const slug = slugOf(person.name)}
			{@const y = rowY(index)}
			<g class="row" class:lit={hovered === person.name} class:dim={!isLit(person.name)}
				onmouseenter={() => (hovered = person.name)}
				onmouseleave={() => (hovered = null)}
				role="presentation">

				<!-- the dashed rule that carries the eye from name to face -->
				<line class="guide" x1={NAMES + 8} x2={NAMES + PLOT} y1={y} y2={y} />
				<text class="name" class:short={narrow} x={NAMES} y={y + 4.5} text-anchor="end">
					{narrow ? person.name.split(" ").slice(-1)[0] : person.name}
				</text>

				<g class="face-mark" transform="translate({x(person.balance)},{y})"
					onpointerenter={(e) => showFace(e, person)}
					onpointermove={(e) => showFace(e, person)}
					onpointerleave={hideFace}
					role="presentation">
					<clipPath id="gap-clip-{slug}">
						<circle cx="0" cy="0" r={FACE / 2} />
					</clipPath>
					<circle class="face-ring" cx="0" cy="0" r={FACE / 2 + 1} />
					{#if faceFiles[slug]}
						<image href="{base}/net/{slug}{faceFiles[slug]}"
							x={-FACE / 2} y={-FACE / 2} width={FACE} height={FACE}
							clip-path="url(#gap-clip-{slug})" preserveAspectRatio="xMidYMid slice" />
					{/if}
				</g>
			</g>
		{/each}
	</svg>

	{#if tooltip}
		<div class="tip" style="left:{tooltip.x}px; top:{tooltip.y - 22}px">
			<strong>{tooltip.person.name}</strong>
			<div><span class="swatch" style="background:{FOX}"></span>
				{pct(tooltip.person.fox)} of Fox's WNBA headlines
				<span class="count">({tooltip.person.foxN.toLocaleString()})</span></div>
			<div><span class="swatch" style="background:{THEM}"></span>
				{pct(tooltip.person.them.share)} of {against === ALL ? "theirs" : against + "'s"}
				<span class="count">({tooltip.person.them.n.toLocaleString()})</span></div>
		</div>
	{/if}
</div>

<style>
	.outlet-gap { position: relative; max-width: 860px; margin: 0 auto; }
	svg { width: 100%; height: auto; display: block; overflow: visible; }

	.tip {
		position: absolute; transform: translate(-50%, -100%);
		background: #1a1a1a; color: #fff;
		font-size: 12.5px; line-height: 1.5;
		padding: 8px 11px; border-radius: 4px;
		pointer-events: none; width: 270px; z-index: 6; text-align: left;
	}
	.tip .count { color: #b9b6ac; font-size: 11px; }
	.tip .swatch {
		display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 5px;
	}

	.picker {
		display: flex; justify-content: center; align-items: center; gap: 6px;
		margin-bottom: 10px; flex-wrap: wrap;
	}
	.picker-label { font-size: 12.5px; color: rgba(42, 21, 3, 0.7); margin-right: 4px; }
	.picker button {
		border: 1px solid transparent; border-radius: 4px;
		background: transparent; padding: 4px 8px; cursor: pointer; line-height: 0;
		opacity: 0.45; filter: grayscale(1);
	}
	.picker button:hover { opacity: 0.85; filter: none; }
	.picker button.active {
		opacity: 1; filter: none;
		border-color: rgba(42, 21, 3, 0.3); background: rgba(255, 253, 248, 0.55);
	}
	.picker img { display: block; height: auto; }
	.picker .all {
		font: inherit; font-size: 12px; font-weight: 700; color: #2a1503;
		line-height: 1.3; padding: 4px 9px;
	}

	.head { font-size: 12.5px; font-weight: 800; }
	.grid { stroke: rgba(42, 21, 3, 0.2); stroke-width: 1; }
	.grid.middle { stroke: rgba(42, 21, 3, 0.5); }
	.guide { stroke: rgba(42, 21, 3, 0.3); stroke-width: 1; stroke-dasharray: 3 4; }
	.tick { font-size: 11px; fill: rgba(42, 21, 3, 0.62); }

	.name { font-size: 13.5px; fill: rgba(42, 21, 3, 0.85); }
	/* the narrow viewBox scales every unit down harder, so the type is drawn
	   larger to land at a comparable size on screen */
	.name.short { font-size: 17px; }
	.row.lit .name { fill: #2a1503; font-weight: 700; }
	/* a beat calls out a few players; the rest recede rather than vanish, so the
	   reader can still see where the called-out ones sit in the order */
	.row.dim { opacity: 0.22; }
	.row { transition: opacity 300ms ease; }

	.face-mark { cursor: default; }
	/* the same treatment as the portraits in the words scrolly: the page's own
	   orange behind, and a white ring hugging the crop rather than a cream disc
	   standing off it like a sticker */
	.face-ring {
		fill: var(--page-orange, #f9a660);
		stroke: rgba(255, 253, 248, 0.92);
		stroke-width: 2;
	}
	.row.lit .face-ring { stroke: #fffdf8; stroke-width: 2.5; }
</style>
