<script>
	import { untrack } from "svelte";
	// The outlet gap as a dot plot: one row per player
	import { base } from "$app/paths";
	import { scaleLinear } from "d3-scale";
	import gapData from "$data/outlet_gap.json";
	import pairData from "$data/pair_gap.json";
	import castData from "$data/cast_gap.json";
	import roster from "$data/people.json";
	import HeadlineClip from "$components/HeadlineClip.svelte";
	import { checks } from "$utils/checks.svelte.js";
	import { or } from "$utils/fill.js";
	import LogoSelect from "$components/helpers/LogoSelect.svelte";
	const faceFiles = Object.fromEntries(
		Object.values(roster)
			.filter((p) => p.face)
			.map((p) => [p.slug, p.face.slice(p.slug.length)])
	);

	import { COMPARISON, GROUPS, AGGREGATES, LOGO, SHORT as SHORT_NAMES } from "$utils/outlets.js";
	// every outlet the picker offers on its own
	const OUTLETS = [...COMPARISON];
	// the pooled baselines the picker offers before the outlets themselves
	// the default baseline: the sports press when the registry has one, else everyone pooled
	const ALL = GROUPS["sports outlets"]?.length ? "sports outlets" : "all outlets";
	// the pools the registry has members for
	const POOLED = [...AGGREGATES];
	const POOL_LABEL = { "sports outlets": "the sports press", "all outlets": "the other outlets", "news outlets": "the news outlets" };
	const POOL_SHORT = { "sports outlets": "sports", "all outlets": "all", "news outlets": "news" };
	const MEMBERS = (group) => GROUPS[group];
	const monthYear = (iso) =>
		new Date(iso + "T12:00:00").toLocaleDateString("en-US", {
			month: "short",
			year: "numeric"
		});
	const FOX = "var(--wnba-red)"; // Fox's own navy, as on the headline clippings
	const THEM = "var(--color-outlets)";
	// left out of the dot plot for now, to keep the rows to the players the
	// piece discusses; delete names here to bring them back
	const HIDDEN = new Set([
		"Sue Bird",
		"Diana Taurasi",
		"Sabrina Ionescu",
		"Chennedy Carter",
		"Nneka Ogwumike",
		"Candace Parker",
		"Cameron Brink",
		"Kelsey Plum"
	]);

	let {
		// source: "players" (outlet_gap.json)
		source = "players",
		reach = 15,
		// minFox: leave out rows with fewer Fox headlines than this (the pairs page)
		minFox = 0,
		highlight = null,
		bare = false,
		against: start = ALL,
		placed = null,
		// speed: milliseconds for a face's slide into place (3500 by default)
		speed = 3500,
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
		centerLine = false,
		// a wider axis on desktop, for the scrolly with no clipping beside it
		wide = false,
		// the title and the line under it (the Doc can set these on the scrolly)
		heading = "",
		comparedWith = "",
		allOutlets = ""
	} = $props();
	// the title spans the axis; the menu names what Fox is compared with
	const HEADING = "How often Fox News names each player in WNBA headlines";
	const POOL_NAME = { "all outlets": "six other outlets combined", "sports outlets": "the sports outlets combined", "news outlets": "the news outlets combined" };
	const againstName = (o) =>
		o === "all outlets" && allOutlets ? allOutlets : (POOL_NAME[o] ?? o);
	const fullData =
		source === "pairs" ? pairData : source === "cast" ? castData : gapData;
	// A check, shown only with ?checks in the address (utils/checks.svelte.js):
	// with or without college coverage. The no-college numbers come from a rerun
	// of notebook 05, cast_gap.py and pair_gap.py with college articles dropped
	// (static/data/nocollege/src/, 2026-09-30).
	let college = $state("with");
	let ncData = $state(null);
	$effect(() => {
		if (college !== "without" || ncData) return;
		const file = source === "pairs" ? "pair_gap" : source === "cast" ? "cast_gap" : "outlet_gap";
		fetch(`${base}/data/nocollege/src/${file}.json`)
			.then((r) => r.json())
			.then((v) => (ncData = v))
			.catch(() => {});
	});
	let data = $derived(college === "without" && ncData ? ncData : fullData);
	let PERIOD = $derived(`${monthYear(data.window.from)} – ${monthYear(data.window.to)}`);
	const pairs = source === "pairs";
	const RATIO_CAP = reach + 1.6; // past the end of the axis, everyone sits at the edge
	// a pair's short name: the two surnames
	const shortName = (person) =>
		person.names
			? person.names.map((n) => n.split(" ").slice(-1)[0]).join(" + ")
			: person.name.split(" ").slice(-1)[0];

	// unplaced players wait on the equal line, veiled; a `centered` one is shown
	// bright there, to make the point that equal coverage would put her at 1×
	let centeredSet = $derived(new Set((centered ?? []).map(key)));

	// how long a placement slide takes (also the CSS transition); the Doc can
	// set it with `speed:` in milliseconds on the scrolly block
	let SLIDE_MS = $derived(Math.max(100, +speed || 3500));

	let against = $state(start);
	$effect(() => {
		against = start;
	});
	let them = $derived(against === ALL ? "everybody else" : (POOL_LABEL[against] ?? against));
	const topName = "Fox News";
	const topShort = "Fox";
	// the Doc types A’ja with a curly apostrophe, the data with a straight one
	const key = (name) => name.toLowerCase().replace(/[’‘]/g, "'");
	let placedSet = $derived(placed === null ? null : new Set(placed.map(key)));
	// the placement the faces are drawn at lags the step by a frame or two:
	// the stacking order below is settled first, so a face never moves in
	// the DOM in the same frame its slide starts (that would cut the
	// transition and snap it into place)
	let placedShown = $state(placed === null ? null : new Set(placed.map(key)));
	$effect(() => {
		const target = placedSet;
		let inner;
		const outer = requestAnimationFrame(() => {
			inner = requestAnimationFrame(() => (placedShown = target));
		});
		return () => {
			cancelAnimationFrame(outer);
			if (inner) cancelAnimationFrame(inner);
		};
	});
	const isPlaced = (name) => placedShown === null || placedShown.has(key(name));

	// both numbers are already cut to the shared window
	function pressShare(person) {
		if (!POOLED.includes(against)) return person.byOutlet?.[against];
		if (person.byOutlet?.[against]) return person.byOutlet[against];
		let hits = 0,
			total = 0;
		for (const outlet of MEMBERS(against) ?? OUTLETS) {
			const stat = person.byOutlet?.[outlet];
			if (!stat || !data.totals?.[outlet]) continue;
			hits += stat.n;
			total += data.totals[outlet];
		}
		return total ? { share: hits / total, n: hits } : null;
	}
	// the top side's share: Fox's own
	const topShare = (person) => ({ share: person.fox, n: person.foxN ?? 0 });

	// k× Fox -> k − 1, k× theirs -> −(k − 1): uniform either way
	let people = $derived(
		data.people
			.filter((person) => source !== "players" || !HIDDEN.has(person.name))
			.filter((person) => (person.foxN ?? 0) >= minFox)
			.map((person) => ({ ...person, them: pressShare(person), top: topShare(person) }))
			.filter((person) => person.them && person.top.share + person.them.share > 0)
			.map((person) => ({
				...person,
				times: Math.max(
					-RATIO_CAP,
					Math.min(
						RATIO_CAP,
						person.top.share >= person.them.share
							? person.top.share / Math.max(person.them.share, 1e-9) - 1
							: -(person.them.share / Math.max(person.top.share, 1e-9) - 1)
					)
				)
			}))
			.toSorted((a, b) => b.times - a.times)
	);
	// names: all — everyone lit, as a named list would be
	let litAll = $derived((highlight ?? []).some((n) => key(n) === "all"));
	let lit = $derived(
		new Set(litAll ? people.map((p) => key(p.name)) : (highlight ?? []).map(key))
	);
	const isLit = (name) => !lit.size || lit.has(key(name));
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
	// Sized in pixels. 
	const FACE_R = { phone: 30, desktop: 40 }; // the most a face may be
	const FACE_OF_ROW = 0.62; // else its radius as a share of the row height
	let frame = $state({ w: 0, h: 0 });
	let WIDTH = $derived(frame.w || (narrow ? 375 : 1000));
	let avail = $derived(frame.h || (narrow ? 560 : 720));

	// the header strip opens only when a clipping lives there
	let headerClip = $derived(
		clipAt === "header" && !narrow && Boolean(clip || clipSlot)
	);
	let TOP = $derived(44 + (headerClip ? 70 : 0));
	const BOTTOM = 62;
	// the names start at the left edge; the plot takes the rest of the width
	let LEFT = $derived(narrow ? 2 : 6);
	let NAMES = $derived(LEFT + (narrow ? 90 : 190));
	// on a phone the frame is the screen, so the far Fox end keeps room for a
	// whole face (Cunningham sits past the edge line)
	let PLOT = $derived(
		Math.max(200, WIDTH - NAMES - (narrow ? FACE_R.phone + 6 : 24))
	);
	let ROW = $derived(
		Math.max(28, (avail - TOP - BOTTOM) / Math.max(1, people.length))
	);
	let R = $derived(
		Math.min(narrow ? FACE_R.phone : FACE_R.desktop, ROW * FACE_OF_ROW)
	);
	const radiusOf = () => R;
	let MAX_R = $derived(R);
	let height = $derived(TOP + people.length * ROW + BOTTOM);

	// symmetric about equal and fixed at 5× either way
	let x = $derived(
		scaleLinear()
			.domain([-reach, reach])
			.range([NAMES + 24, NAMES + PLOT])
	);
	let unit = $derived(x(1) - x(0));
	let overflowScale = $derived(narrow ? 0.35 : 0.5);
	// where a value sits: on the axis, or past its end
	let xOf = $derived((times) => {
		const clamped = Math.max(-reach, Math.min(reach, times));
		const beyond = Math.abs(times) - reach;
		if (beyond <= 0) return x(clamped);
		const extra = Math.min(beyond * unit * overflowScale, R * 2.2);
		return x(clamped) + Math.sign(times) * extra;
	});
	const beyondAxis = (person) => Math.abs(person.times) > reach;
	let rowY = $derived((index) => TOP + index * ROW + ROW / 2);
	let ticks = $derived.by(() => {
		const [lo, hi] = x.domain();
		const out = [{ at: 0, label: "Equal", sub: "" }];
		// 4×, 6× and 8×: enough to read the scale, not a ruler; a longer axis
		// (the cast page) ticks every 5×
		const marks = reach > 8 ? [4, 9, 14, 19, 24, 29] : [3, 5, 7];
		for (const k of marks) {
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
	const SHORT = { ...SHORT_NAMES, ...POOL_SHORT };
	let themShort = $derived(
		against === ALL ? "others" : (SHORT[against] ?? against)
	);
	// "3.1× Fox" or "2.4× ESPN" — the ratio, read off for a named player so the
	// reader need not squint at the axis
	const ratioTag = (person) => {
		const k = Math.abs(person.times) + 1;
		if (Math.abs(person.times) < 0.05) return "1× (equal)";
		return `${k.toFixed(k < 10 ? 1 : 0)}× ${person.times > 0 ? topShort : themShort}`;
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

	// Where the equal line really is on screen
	let svgEl = $state(null);
	let equalLeft = $state(null);
	let shift = $state(0);
	// the axis ends as shares of the frame, so the title can span them (shares,
	// not measured pixels: the title's height feeds back into the frame)
	let axisLeft = $derived(((NAMES + 24) / WIDTH) * 100);
	let axisWidth = $derived(((PLOT - 24) / WIDTH) * 100);
	$effect(() => {
		if (!svgEl) return;
		// read these here so the effect re-runs when the layout flips (the
		// ResizeObserver callback alone would not track them)
		const shifting = centerLine && !narrow;
		const measure = () => {
			const box = svgEl.closest(".outlet-gap");
			if (!box) return;
			const head = box.querySelector(".titles");
			const slot = box.querySelector(".clip-slot");
			const w = Math.round(box.clientWidth);
			const h = Math.round(
				box.clientHeight -
					(head?.offsetHeight ?? 0) -
					(slot?.offsetHeight ?? 0) -
					10
			);
			// a static frame (no fixed height) reports the drawing's own height:
			// keep the natural rows then
			const next = { w, h: box.clientHeight > 0 && h > 200 ? h : 0 };
			if (next.w !== frame.w || next.h !== frame.h) frame = next;
			const r = svgEl.getBoundingClientRect();
			if (!r.width || !r.height) return;
			const scale = Math.min(r.width / WIDTH, r.height / height);
			const offset = (r.width - WIDTH * scale) / 2;
			equalLeft = offset + x(0) * scale;
			if (!shifting) {
				shift = 0;
				return;
			}
			// how far left the box must move for the line to sit at its centre,
			// but never past the viewport's left edge
			const bb = box.getBoundingClientRect();
			const baseLeft = bb.left - shift;
			shift = Math.max(bb.width / 2 - equalLeft, -(baseLeft - 8));
		};
		measure();
		// the frame's size is set by the page, so watching it cannot loop
		const ro = new ResizeObserver(measure);
		ro.observe(svgEl.closest(".outlet-gap"));
		return () => ro.disconnect();
	});

	// drawing order: plain faces first, the named ones on top. A face goes up
	// the stack the moment a step names it — before it swells, and before its
	// slide starts (the placement above waits a frame for this) — and comes
	// back down only once the step's slides have settled, so a face sliding
	// home is never moved in the DOM mid-transition
	let SETTLE_MS = $derived(SLIDE_MS + 300);
	let litSettled = $state(new Set());
	$effect(() => {
		const next = new Set(
			people
				.filter(
					(p) => (lit.size > 0 && isLit(p.name)) || centeredSet.has(key(p.name))
				)
				.map((p) => p.name)
		);
		const current = untrack(() => litSettled);
		// a face the step drops comes down at once, unless its placement is
		// changing too — then it stays up until its slide has settled
		const shown = untrack(() => placedShown);
		const sliding = (n) => {
			const k = key(n);
			const to = placedSet === null || placedSet.has(k);
			const from = shown === null || shown.has(k);
			return to !== from;
		};
		// the named faces go to the top now; the ones the step drops come down,
		// except those sliding home, which hold a middle tier (their relative
		// order unchanged, so nothing moves in the DOM mid-slide) until the
		// slide has settled
		const held = untrack(() => heldUp);
		heldUp = new Set([...current, ...held].filter((n) => !next.has(n) && sliding(n)));
		if (next.size !== current.size || [...next].some((n) => !current.has(n))) litSettled = next;
		const timer = setTimeout(() => (heldUp = new Set()), SETTLE_MS);
		return () => clearTimeout(timer);
	});
	let heldUp = $state(new Set());
	const stackOrder = (person) =>
		hovered === person.name ? 3 : litSettled.has(person.name) ? 2 : heldUp.has(person.name) ? 1 : 0;
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
	// a tap shows a face's tooltip and nothing hides it on touch: a click
	// anywhere else takes it away
	function clickAway(event) {
		if (!event.target.closest?.(".face-mark")) tooltip = null;
	}
</script>

<svelte:window onclick={clickAway} />

<div
	class="outlet-gap"
	class:narrow
	style:transform={shift ? `translateX(${shift}px)` : undefined}
	style:--slide="{SLIDE_MS}ms"
>
	<!-- on screen and live for the whole scrolly, so the reader can switch at any step -->
	<!-- the title over the axis, end to end; the menu switches who Fox is compared with -->
	<div
		class="titles"
		style:--axis-left={narrow ? null : `${axisLeft}%`}
		style:--axis-width={narrow ? null : `${axisWidth}%`}
	>
		<p class="heading">{or(heading, HEADING)}</p>
		<!-- a div, not a p: the menu inside renders block elements -->
		<div class="subheading">
			<span>{or(comparedWith, "Compared with")}</span>
			<LogoSelect
				options={[...AGGREGATES, ...outlets]}
				bind:value={against}
				logoOf={(o) => LOGO[o] ?? null}
				nameOf={againstName}
				label="Compared with"
			/>
		</div>
		{#if checks.on}
			<!-- a check: see `college` above -->
			<div class="picker college-pick">
				<button class="all" class:active={college === "with"} onclick={() => (college = "with")}>With college</button>
				<button class="all" class:active={college === "without"} onclick={() => (college = "without")}>Without college</button>
			</div>
		{/if}
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
			width={WIDTH}
			{height}
			role="img"
			aria-label="Whether Fox News or {against} gives each player a larger share of its WNBA headlines"
		>
			<text
				class="head"
				x={narrow ? NAMES + 24 + 10 : x(0) - 22}
				y={TOP - (narrow ? 22 : 0)}
				text-anchor={narrow ? "start" : "end"}
				fill={THEM}>← More {narrow ? themShort : them}</text
			>
			<text
				class="head"
				x={narrow ? NAMES + PLOT - 10 : x(0) + 22}
				y={TOP - (narrow ? 22 : 0)}
				text-anchor={narrow ? "end" : "start"}
				fill={FOX}>{narrow ? `More ${topShort} →` : `More ${topName} →`}</text
			>
			<!-- the ends of the axis, in each side's colour -->
			<line
				class="edge"
				x1={NAMES + 24}
				x2={NAMES + 24}
				y1={TOP - 14}
				y2={axisY}
				stroke={THEM}
			/>
			<line
				class="edge"
				x1={NAMES + PLOT}
				x2={NAMES + PLOT}
				y1={TOP - 14}
				y2={axisY}
				stroke={FOX}
			/>
			{#each ticks as tick (tick.at)}
				{#if tick.at === 0 || Math.abs(tick.at) === 3 || Math.abs(tick.at) === 5}
					<!-- the equal line, and faint lines at 4× and 6× either way -->
					<line
						class="grid"
						class:middle={tick.at === 0}
						x1={x(tick.at)}
						x2={x(tick.at)}
						y1={TOP - 14}
						y2={axisY}
					/>
				{/if}
				<g class="tick-g" style="transform: translate({x(tick.at)}px, 0)">
					<text class="tick" x="0" y={axisY + 16} text-anchor="middle"
						>{tick.label}</text
					>
					{#if tick.sub}
						<text class="tick sub" x="0" y={axisY + 27} text-anchor="middle"
							>{tick.sub}</text
						>
					{/if}
				</g>
			{/each}
			<!-- <text
				class="note"
				x={(NAMES + 24 + NAMES + PLOT) / 2}
				y={axisY + 46}
				text-anchor="middle">{PERIOD}</text
			> -->

			{#each people as person, index (person.name)}
				{@const slug = slugOf(person.name)}
				{@const y = rowY(index)}
				{@const r = radiusOf(person)}
				{@const on = isPlaced(person.name)}
				<!-- a centered player is shown bright, named or not: she is the point of the step -->
				{@const named =
					(lit.size > 0 ? isLit(person.name) : on) ||
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
						{narrow || pairs ? shortName(person) : person.name}
					</text>
				</g>
			{/each}

			<!-- the faces in a second pass, so they sit over every row's rule and
			     name; the highlighted (and hovered) ones drawn last, on top -->
			{#each people.toSorted((a, b) => stackOrder(a) - stackOrder(b)) as person (person.name)}
				{@const index = people.indexOf(person)}
				{@const slug = slugOf(person.name)}
				{@const y = rowY(index)}
				{@const r = radiusOf(person)}
				{@const on = isPlaced(person.name)}
				<!-- a centered player is shown bright, named or not: she is the point of the step -->
				{@const named =
					(lit.size > 0 ? isLit(person.name) : on) ||
					centeredSet.has(key(person.name))}
				<!-- a face the step names grows a third larger than the rest -->
				{@const grow = on && named && lit.size > 0 && !litAll ? 1.35 : 1}
				<g
					class="row"
					class:lit={hovered === person.name}
					class:dim={on && !isLit(person.name)}
					class:waiting={!on && !named}
					onmouseenter={() => (hovered = person.name)}
					onmouseleave={() => (hovered = null)}
					role="presentation"
				>
					<g
						class="face-mark"
						style:transform="translate({on ? xOf(person.times) : x(0)}px, {y}px)"
						onpointerenter={(e) => on && showFace(e, person)}
						onpointermove={(e) => on && showFace(e, person)}
						onpointerleave={hideFace}
						role="presentation"
					>
						<g class="face-scale" style:transform="scale({grow})">
						{#if person.names}
							<!-- a pair: two smaller faces, side by side and overlapping -->
							{#each person.names as who, k (who)}
								{@const ws = slugOf(who)}
								{@const rr = r * 0.78}
								{@const dx = (k === 0 ? -1 : 1) * r * 0.55}
								<clipPath id="gap-clip-{slug}-{k}">
									<circle cx={dx} cy="0" r={Math.max(0, rr - 1)} />
								</clipPath>
								{#if faceFiles[ws]}
									<circle cx={dx} cy="0" r={rr} fill="#f6e7d6" />
									<image
										href="{base}/net/{ws}{faceFiles[ws]}"
										x={dx - rr * 1.2}
										y={-rr * 1.05}
										width={rr * 2.4}
										height={rr * 2.4}
										clip-path="url(#gap-clip-{slug}-{k})"
										preserveAspectRatio="xMidYMid slice"
									/>
								{:else}
									<circle cx={dx} cy="0" r={rr} fill="var(--color-sand)" />
								{/if}
								<circle
									cx={dx}
									cy="0"
									r={rr}
									class="ring"
									style="stroke:{ringColor(person)}"
								/>
							{/each}
						{:else}
							<clipPath id="gap-clip-{slug}">
								<circle cx="0" cy="0" r={Math.max(0, r - 1)} />
							</clipPath>
							{#if faceFiles[slug]}
								<circle cx="0" cy="0" {r} fill="#f6e7d6" />
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
								<circle cx="0" cy="0" {r} fill="var(--color-sand)" />
							{/if}
							<circle
								cx="0"
								cy="0"
								{r}
								class="ring"
								style="stroke:{ringColor(person)}"
							/>
						{/if}
						{#if !on && !named}
							<!-- waiting on the equal line: veiled, unless this step names her -->
							<circle cx="0" cy="0" r={r + 1.5} class="veil" />
						{/if}
						</g>
						{#if on && ((named && lit.size > 0 && !litAll) || hovered === person.name)}
							<!-- the tag, for the players a step names (the closing step lights
							     everyone and needs none). It sits right of the face — on the
							     "others" side that keeps it clear of her name — unless she is off
							     the Fox end of the axis or it would run past the frame -->
							{@const label = ratioTag(person)}
							{@const fits =
								xOf(person.times) + r * grow + 9 + label.length * 7.5 <= WIDTH}
							{@const rightOf =
								fits && !(person.times >= 0 && beyondAxis(person))}
							<text
								class="ratio"
								x={rightOf ? r * grow + 9 : -r * grow - 9}
								y="4.5"
								text-anchor={rightOf ? "start" : "end"}
								fill={ringColor(person)}>{label}</text
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
				{pct(tooltip.person.top.share)} of Fox's WNBA headlines
				<!-- the raw count beside every share (2026-09-30) -->
				<span class="count">({tooltip.person.top.n.toLocaleString()})</span>
			</div>
			<div>
				<span class="swatch" style="background:{THEM}"></span>
				{pct(tooltip.person.them.share)} of {them === "other outlets"
					? "the other outlets'"
					: them + "'s"}
				<span class="count">({tooltip.person.them.n.toLocaleString()})</span>
			</div>
			{#if tooltip.person.ex}
				<p class="ex">“{tooltip.person.ex.headline}” <span class="count">Fox, {tooltip.person.ex.date.slice(0, 4)}</span></p>
			{/if}
		</div>
	{/if}
</div>

<style>
	/* the chart in the graphics sans, like the other charts */
	.outlet-gap {
		position: relative;
		font-family: var(--font-graphic);
		max-width: 1040px;
		margin: 0 auto;
	}

	.head {
		text-transform: uppercase;
		font-size: 11px;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
		overflow: visible;
	}

	.tip .ex {
		margin: 9px 0 0;
		padding-left: 9px;
		border-left: 3px solid var(--tip-rule);
		font: var(--tip-quote);
		max-width: 260px;
	}
	.tip {
		position: absolute;
		transform: translate(-50%, -100%);
		background: var(--tip-bg);
		color: var(--color-ink-dark);
		border: 1px solid var(--tip-border);
		border-radius: var(--tip-radius);
		box-shadow: var(--tip-shadow);
		font: var(--tip-body);
		color: var(--tip-ink);
		padding: var(--tip-pad);
		pointer-events: none;
		width: 270px;
		z-index: 6;
		text-align: left;
	}
	.tip strong {
		display: block;
		margin-bottom: 3px;
		font: var(--tip-title);
		color: var(--tip-ink);
	}
	.tip .count {
		font: var(--tip-small);
		color: var(--tip-sub);
	}
	.tip .swatch {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 2px;
		margin-right: 5px;
		vertical-align: -1px;
	}

	.college-pick {
		margin-top: 6px;
	}
	.picker {
		display: flex;
		justify-content: center;
		align-items: center;
		gap: 5px;
		margin-bottom: 6px;
		/* named pills, two rows on a desktop rather than one unreadable row of logos */
		flex-wrap: wrap;
		row-gap: 5px;
		max-width: 760px;
	}
	/* the title, and who Fox is compared with, as on the words charts; on a
	   desktop it spans the axis from end to end */
	.titles {
		margin: 0 0 14px var(--axis-left, 0px);
		width: var(--axis-width, auto);
		max-width: 100%;
	}
	.heading {
		margin: 0;
		font-family: var(--font-graphic);
		font-size: 24px;
		font-weight: 700;
		line-height: 1.22;
		letter-spacing: -0.01em;
		text-wrap: pretty;
		color: var(--color-ink);
	}
	.subheading {
		display: flex;
		align-items: center;
		gap: 6px;
		margin: 4px 0 0;
		font-family: var(--font-graphic);
		font-size: 15px;
		color: rgba(42, 21, 3, 0.75);
	}
	.subheading > span {
		flex: 0 0 auto;
		white-space: nowrap;
	}
	.subheading :global(.logo-select) {
		flex: 0 1 auto;
		width: auto;
		min-width: 0;
	}
	/* the menu sits in the line as a quiet underlined word */
	.subheading :global(.logo-select .current) {
		height: auto;
		padding: 0 18px 0 0;
		border: 0;
		border-bottom: 1.5px solid currentColor;
		border-radius: 0;
		background: transparent;
		font-family: var(--font-graphic);
		font-size: 15px;
		color: var(--color-ink);
	}
	.subheading :global(.logo-select .current::after) {
		right: 0;
	}
	@media (max-width: 640px) {
		.titles {
			padding: 0 12px;
		}
		.heading {
			font-size: 20px;
		}
		.subheading,
		.subheading :global(.logo-select .current) {
			font-size: 14px;
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
		white-space: nowrap;
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
	.picker .all {
		padding: 3px 9px;
		font-size: 11px;
	}
	/* a phone: the header centres on the box (the equal line sits too far right
	   for the title and pills to fit), and the pills shrink and may wrap */
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
		font-size: 11px;
		font-weight: 700;
	}
	.grid {
		stroke: var(--wnba-tan-dark);
		stroke-width: 1;
	}
	.grid.middle {
		stroke: var(--wnba-tan-dark);
		stroke-width: 2;
	}
	.edge {
		stroke-width: 3;
		stroke-linecap: round;
	}
	.guide {
		stroke: rgba(42, 21, 3, 0.3);
		stroke-width: 1;
		stroke-dasharray: 3 4;
	}
	.tick {
		font-size: 11px;
		font-weight: 600;
		fill: rgba(42, 21, 3, 0.72);
	}
	.ratio {
		font-size: 13px;
		font-weight: 700;
		paint-order: stroke;
		stroke: var(--wnba-tan-bg);
		stroke-width: 4px;
		stroke-linejoin: round;
	}
	.tick.sub {
		font-size: 9.5px;
		fill: rgba(42, 21, 3, 0.5);
	}
	.note {
		font-size: 13px;
		fill: rgba(42, 21, 3, 0.55);
	}

	.name {
		font-size: 15px;
		fill: rgba(42, 21, 3, 0.85);
	}
	.name.short {
		font-size: 13.5px;
	}
	/* a phone's axis is short: the direction labels shrink to fit beside each other */
	.narrow .head {
		font-size: 12px;
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
		fill: var(--wnba-tan-bg);
		opacity: 0.72;
	}

	.face-mark {
		cursor: pointer;
		transition: transform var(--slide, 1500ms) cubic-bezier(0.22, 0.8, 0.3, 1);
	}
	/* the named faces swell and settle back as steps change */
	.face-scale {
		transition: transform 500ms cubic-bezier(0.22, 0.8, 0.3, 1);
		transform-origin: 0 0;
		cursor: pointer;
	}
	/* the ticks slide with the axis as it stretches; new ones fade in */
	.tick-g {
		transition: transform 900ms cubic-bezier(0.22, 0.8, 0.3, 1);
		animation: tick-in 600ms ease both;
	}
	@keyframes tick-in {
		from {
			opacity: 0;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.face-mark,
		.tick-g {
			transition: none;
			animation: none;
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
