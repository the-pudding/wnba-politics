<script>
    import { getContext, onMount } from "svelte";
	import { base } from "$app/paths";
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import HeadlineClip from "$components/HeadlineClip.svelte";
	import { fade } from "svelte/transition";
	import { faces, clipPops } from "$utils/clips.js";
	import arrowSvg from "$svg/arrow-up-right.svg";
    const copy = getContext("copy");

	let { steps = [] } = $props();

	// undefined until the first step scrolls into view (Scrolly sets it back to
	// undefined when no step is in view)
	let introIndex = $state(undefined);

	// what the wall and header actually show. Scrolly counts a step as in view while
	// any of it is on screen, so on the way back up the first step never leaves and
	// the header never returned. Instead the header comes back by scroll position:
	// whenever the steps start below the middle of the screen.
	// Scrolly also reports undefined once you've scrolled past the steps; holding the
	// last step there stops the header flashing back in.
	let stepsEl = $state();
	let beforeSteps = $state(true);
	function measure() {
		if (stepsEl) beforeSteps = stepsEl.getBoundingClientRect().top > window.innerHeight * 0.5;
	}
	onMount(measure);
	let shownIndex = $state(undefined);
	$effect(() => {
		if (beforeSteps) shownIndex = undefined;
		else if (introIndex !== undefined) shownIndex = introIndex;
	});

	// what the background wall shows: nothing, then screenshots, then headlines,
	// then the headlines clear away one by one (step 4 on)
	let wall = $derived(
		shownIndex === undefined
			? "empty"
			: shownIndex < 2
				? "images"
				: shownIndex <= 3
					? "text"
					: "cleared"
	);

    // written like the copy doc: <b>bold</b>, ==highlight==, ((Name|face)) for a portrait
    let highlightHeadlines = [
        "<b>Caitlin Clark</b> ((Caitlin Clark|face)) fans <b>==unload==</b> on WNBA, <b>Alyssa Thomas</b> ((Alyssa Thomas|face)) after <b>==violent sequence==</b> leaves Fever star battered",
        "WNBA star who <b>==hurt Caitlin Clark's ((Caitlin Clark|face)) eye==</b> calls for league to take action <b>==against Trump administration policies==</b>",
        "<b>Dave Portnoy</b> calls <b>Angel Reese ((Angel Reese|face)) ==a jacka-- for jealousy of Caitlin Clark</b>== ((Caitlin Clark|face)) in response to ESPN analyst"
    ]

	// the headline without its markup: tags and == go, a ((Name|face)) portrait goes
	// entirely (the name is already written next to it), and ((Name)) becomes the name
	const plain = (t) =>
		t
			.replace(/\(\([^()|]+\|\s*face\s*\)\)/g, "")
			.replace(/\(\(([^()]+)\)\)/g, "$1")
			.replace(/<[^>]*>/g, "")
			.replace(/==/g, "")
			.replace(/\s+/g, " ")
			.trim();

	// compare headlines on letters and digits only, so quote marks and dashes don't matter
	const norm = (t) => plain(t).toLowerCase().replace(/[^a-z0-9]/g, "");

	// headlines for the text tiles, from the same file the swarm uses.
	// the highlight headlines are taken out of the pool and given to the pull-out tiles instead.
	let headlines = $state([]);
	let featuredHeadlines = $state([]);
	onMount(() => {
		let alive = true;
		fetch(`${base}/data/framing_swarm.json`)
			.then((r) => r.json())
			.then((D) => {
				if (!alive) return;
				const all = D.headlines.map((r) => r[1]);
				const wanted = highlightHeadlines.map(norm);
				// the wall tile shows the plain text from the data; the pull-out card shows
				// the styled version typed above. No date if it isn't found in the data.
				featuredHeadlines = highlightHeadlines.map((h, k) => {
					const row = D.headlines.find((r) => norm(r[1]) === wanted[k]);
					return row
						? { text: row[1], styled: h, date: formatDate(row[0]) }
						: { text: plain(h), styled: h, date: "" };
				});
				const picked = new Set(wanted);
				headlines = shuffle(
					all.filter((t) => !picked.has(norm(t))),
					7
				);
			});
		return () => (alive = false);
	});

	// "2025-05-20" -> "May 2025", the way the gallery clips are dated. Read as UTC so the day doesn't shift with the reader's timezone.
	function formatDate(iso) {
		return new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-US", {
			month: "long",
			year: "numeric",
			timeZone: "UTC"
		});
	}

	// seeded shuffle so the wall looks random but stays the same on every visit
	function shuffle(arr, seed) {
		const a = arr.slice();
		let s = seed;
		const rand = () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646;
		for (let i = a.length - 1; i > 0; i--) {
			const j = Math.floor(rand() * (i + 1));
			[a[i], a[j]] = [a[j], a[i]];
		}
		return a;
	}

	// how long the whole wall takes to fill in, in seconds
	const STAGGER = 1.2;

	// background wall: tiles share the screenshot's shape so they sit edge to edge.
	// tiles are at most 100px wide, and at least 16 fit across on narrow screens.
	const TILE_RATIO = 1164 / 2076; // height / width of everything's-racist-fox.png
	const MAX_TILE_W = 100;
	const MIN_COLS = 16;
	// screenshots in static/images/grid/, repeated in order to fill the wall
	const GRID_IMAGES = Array.from({ length: 40 }, (_, i) => `${base}/images/grid/grid-${i}.png`);

	let gridW = $state(0);
	let gridH = $state(0);
	// whole pixels avoid hairline seams between tiles
	let tileW = $derived(Math.floor(Math.min(MAX_TILE_W, gridW / MIN_COLS)));
	let tileH = $derived(Math.round(tileW * TILE_RATIO));
	// enough tiles to cover the screen; the overflow gets clipped
	let cols = $derived(tileW ? Math.ceil(gridW / tileW) : 0);
	let rows = $derived(tileH ? Math.ceil(gridH / tileH) : 0);
	// each tile gets a scattered delay so the wall fills in randomly, not row by row
	let gridCells = $derived(
		shuffle(
			Array.from({ length: cols * rows }, (_, i) => i),
			cols * rows
		).map((order, i) => {
			// the pull-out tiles always carry the highlight headlines, so they're on the wall
			// the whole time and the same ones lift out on step 3
			const pinned = featuredHeadlines[headTiles.get(i)?.k];
			return {
				delay: (order / Math.max(1, cols * rows)) * STAGGER,
				src: GRID_IMAGES[i % GRID_IMAGES.length],
				headline: pinned
					? pinned.text
					: headlines.length
						? headlines[i % headlines.length]
						: "",
				styled: pinned?.styled ?? "",
				date: pinned?.date ?? ""
			};
		})
	);

	// steps 1 and 3: three tiles lift out of the wall and grow (clips on step 1,
	// headlines on step 3). The two sets use different tiles, with the headlines
	// mirrored to the other side. Cards are centered and
	// at most 460px wide, so on wide screens they go in the side gutters; on narrow
	// screens there are no gutters, so they go in strips along the top and bottom.
	const CARD_HALF = 460 / 2 + 32; // half the card plus breathing room
	const PAD = 16;
	let featured = $derived.by(() => {
		if (!cols || !rows) return { clips: new Map(), heads: new Map() };
		const gutter = gridW / 2 - CARD_HALF;
		let w, spots;
		if (gutter >= 160) {
			w = Math.min(320, gutter - 2 * PAD, (gridH * 0.4) / TILE_RATIO);
			const xL = gutter / 2;
			const xR = gridW - xL;
			spots = [
				[xL, gridH * 0.27],
				[xR, gridH * 0.5],
				[xL, gridH * 0.73]
			];
		} else {
			w = Math.min(gridW * 0.44, (gridH * 0.2) / TILE_RATIO);
			const h = w * TILE_RATIO;
			spots = [
				[gridW * 0.27, PAD + h / 2],
				[gridW * 0.73, PAD + h / 2 + h * 0.35],
				[gridW / 2, gridH - PAD - h / 2]
			];
		}
		// the grid is centered, so its overflow is split evenly on each side
		const x0 = (gridW - cols * tileW) / 2;
		const y0 = (gridH - rows * tileH) / 2;
		const scale = w / tileW;
		// tiles already used by either set, so the two never share one
		const taken = new Set();
		const pick = (list) => {
			const map = new Map();
			list.forEach(([tx, ty], k) => {
				// take the tile nearest the spot so it only has a short way to travel
				let col = Math.min(cols - 1, Math.max(0, Math.floor((tx - x0) / tileW)));
				let row = Math.min(rows - 1, Math.max(0, Math.floor((ty - y0) / tileH)));
				while (taken.has(row * cols + col)) col = (col + 1) % cols;
				taken.add(row * cols + col);
				const cx = x0 + (col + 0.5) * tileW;
				const cy = y0 + (row + 0.5) * tileH;
				// k staggers the three pull-outs, one after another
				map.set(row * cols + col, { dx: tx - cx, dy: ty - cy, scale, k });
			});
			return map;
		};
		const clips = pick(spots);
		const heads = pick(spots.map(([x, y]) => [gridW - x, y]));
		return { clips, heads };
	});
	let clipTiles = $derived(featured.clips);
	let headTiles = $derived(featured.heads);

	// pulled-out tiles swap to a clip (the same one for now)
	const FEATURE_VIDEO = `${base}/video/watters-tv.mp4`;
	const FEATURE_POSTER = `${base}/video/watters-tv.jpg`;
	const FEATURE_STAGGER = 0.15; // seconds between each pull-out

	// only play while pulled out, so the hidden clips don't run in the background
	function playWhen(node, on) {
		const set = (v) => (v ? node.play().catch(() => {}) : node.pause());
		set(on);
		return { update: set };
	}

	const FEATURE_STEPS = [1, 3];

	// once a pull-out has shown, the picked tiles skip the staggered fade so they settle
	// back into the wall right away on the way up. Reset when the wall empties.
	let featureSeen = $state(false);
	$effect(() => {
		if (FEATURE_STEPS.includes(shownIndex)) featureSeen = true;
		else if (shownIndex === undefined) featureSeen = false;
	});

	// horizontal bands (% of image height) and how far each one jumps during a glitch.
	// uneven cuts and offsets read more like a bad signal than a regular grid.
	const cuts = [0, 6, 14, 21, 33, 39, 50, 57, 68, 76, 85, 92, 100];
	const offsets = [0, 10, -14, 0, 6, -22, 0, 16, -8, 0, 12, -6];
	const strips = offsets.map((dx, i) => ({
		top: cuts[i],
		bottom: cuts[i + 1],
		dx,
		delay: -(i % 3) * 0.06
	}));

    $effect(() => {
        console.log(introIndex)
    });
</script>

<svelte:window onscroll={measure} onresize={measure} />

<div class="intro-wall">
	<div class="sticky">
        <header class="intro-wall-header" class:off={shownIndex >= 0}>
            <h1>
                <span class="hedLeft">{copy.meta.hedLeft}</span>
                <span class="glitch" style="--src: url({base}/images/cc-combo.png)">
                    <img class="base" src="{base}/images/cc-combo.png" alt="Caitlin Clark shoots over the Fox News logo"/>
                    {#each strips as s}
                        <img
                            class="strip"
                            src="{base}/images/cc-combo.png"
                            alt=""
                            aria-hidden="true"
                            style="--top: {s.top}%; --bottom: {100 - s.bottom}%; --dx: {s.dx}px; animation-delay: {s.delay}s;"
                        />
                    {/each}
                    <span class="static" aria-hidden="true"></span>
                </span>
                <span class="hedRight">{copy.meta.hedRight}</span>
            </h1>
            <p class="byline">
                By {@html copy.meta.byline}, with {@html copy.meta.with}
                <span class="scroll-hint" aria-hidden="true">{@html arrowSvg}</span>
            </p>
        </header>
        <!-- 16×9 wall of screenshots behind the title -->
        <div
            class="bg-grid"
            aria-hidden="true"
            bind:clientWidth={gridW}
            bind:clientHeight={gridH}
            style="--cols: {cols}; --rows: {rows}; --tile-w: {tileW}px; --tile-h: {tileH}px;"
        >
            {#each gridCells as cell, i (i)}
                {@const clipSpot = clipTiles.get(i)}
                {@const headSpot = headTiles.get(i)}
                {@const spot = clipSpot ?? headSpot}
                {@const f = shownIndex === 1 ? clipSpot : shownIndex === 3 ? headSpot : undefined}
                <div
                    class="cell {wall}"
                    class:featured={f}
                    class:has-clip={!!cell.date}
                    class:quick={featureSeen && !!spot}
                    style="--d: {cell.delay}s; {spot ? `--s0: ${spot.scale};` : ''} {f ? `--dx: ${f.dx}px; --dy: ${f.dy}px; --s: ${f.scale}; --fd: ${f.k * FEATURE_STAGGER}s;` : ''}"
                >
                    <img src={cell.src} alt="" />
                    {#if clipSpot}
                        <video
                            src={FEATURE_VIDEO}
                            poster={FEATURE_POSTER}
                            muted
                            loop
                            playsinline
                            preload="metadata"
                            use:playWhen={!!f && shownIndex === 1}
                        ></video>
                    {/if}
                    <p>{cell.headline}</p>
                    {#if f && wall === "text" && cell.date}
                        <!-- mounted on pull-out so the headline's scramble plays as it arrives -->
                        <div
                            class="clip-wrap"
                            transition:fade={{ duration: 300, delay: (spot?.k ?? 0) * FEATURE_STAGGER * 1000 }}
                        >
                            <div class="clip-inner">
                                <HeadlineClip
                                    clip={{ date: cell.date, title: cell.styled }}
                                    rot={0}
                                    small={(spot?.scale ?? 1) * tileW < 260}
                                    scramble={false}
                                    dateAfter
                                />
                            </div>
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
		<!-- the visual goes here; introIndex says which step is in view -->
	</div>

	<div class="steps" bind:this={stepsEl}>
		<Scrolly bind:value={introIndex}>
			{#each steps as step, i}
				<div class="step" class:active={introIndex === i}>
					{#if step.text?.trim()}
						<p class="card">{@html clipPops(faces(step.text, base), base)}</p>
					{/if}
				</div>
			{/each}
		</Scrolly>
	</div>
</div>

<style>
	.intro-wall {
        width: 100%;
		position: relative;
	}
	.sticky {
		position: sticky;
		top: 0;
        width: 100%;
		height: 100svh;
	}
    .bg-grid {
        position: absolute;
        inset: 0;
        z-index: 0;
        display: grid;
        grid-template-columns: repeat(var(--cols), var(--tile-w));
        grid-template-rows: repeat(var(--rows), var(--tile-h));
        /* center the wall so any clipped overflow is split evenly between edges */
        place-content: center;
        overflow: hidden;
    }
    /* each tile holds a screenshot and a headline stacked on top of each other;
       the wall state decides which one shows */
    .cell {
        position: relative;
        overflow: hidden;
        transition: transform 600ms cubic-bezier(0.2, 0.7, 0.2, 1);
    }
    /* step 1: lifted out of the wall, moved to its spot and scaled up */
    /* pull-outs go one after another (--fd); going back they all return at once */
    .cell.featured {
        z-index: 1;
        transform: translate(var(--dx), var(--dy)) scale(var(--s));
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
        transition-delay: var(--fd);
    }
    .cell video {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        opacity: 0;
        transition: opacity 300ms ease;
    }
    .cell.images.featured video {
        opacity: 1;
        transition-delay: var(--fd);
    }
    .cell.images.quick img,
    .cell.text.quick p {
        transition-delay: 0s;
    }
    /* step 3: the pulled-out headline at full strength */
    .cell.text.featured p {
        opacity: 1;
        transition-delay: var(--fd);
    }
    .cell.images.featured img {
        opacity: 1;
        filter: none;
        transition-delay: var(--fd);
    }
    /* a pulled-out headline becomes a gallery clipping. It's laid out at its pulled-out
       width and shrunk by 1/--s0 to fit the tile, so the cell's scale-up brings it back to
       full size and sharp. */
    .cell.has-clip.text.featured {
        overflow: visible;
        box-shadow: none;
    }
    .cell.has-clip.text.featured p {
        opacity: 0;
    }
    .clip-wrap {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        pointer-events: none;
    }
    .clip-inner {
        flex: 0 0 auto;
        width: calc(100% * var(--s0));
        transform: scale(calc(1 / var(--s0)));
    }
    .cell img,
    .cell p {
        position: absolute;
        inset: 0;
        opacity: 0;
        font-style: italics;
        /* transform: scale(0.85); */
        transition:
            opacity 300ms ease,
            transform 300ms ease;
        /* leaving is instant-ish and all at once; arriving is staggered (below) */
        transition-delay: 0s;
    }
    .cell img {
        display: block;
        width: 100%;
        height: 100%;
        object-fit: cover;
        filter: grayscale(100%);
    }
    .cell p {
        margin: 0;
        padding: 0.5em 0.5em;
        background: var(--wnba-tan-bg);
        border: 0.5px solid var(--wnba-tan-light);
        font-family: var(--font-serif);
        font-size: calc(var(--tile-h) / 8);
        line-height: 1.15;
        display: -webkit-box;
        -webkit-line-clamp: 4;
        line-clamp: 4;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .cell.images img,
    .cell.text p {
        opacity: 0.5;
        transform: none;
        transition-delay: var(--d);
    }
    /* screenshots sit back at half strength */
    .cell.images img {
        opacity: 0.15;
    }
    /* step 2: headlines leave in the same scattered order they arrived */
    .cell.cleared p {
        transition-delay: var(--d);
    }
    header {
        position: relative;
        z-index: 1;
        width: 100%;
        height: 100%;
        transition:
            opacity 400ms ease,
            visibility 0s;
    }
    /* a plain fade; visibility flips after the fade so it can't be clicked or read once gone */
    header.off {
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
        transition:
            opacity 400ms ease,
            visibility 0s 400ms;
    }
    .byline {
        color: var(--color-fg);
        font-family: var(--font-sans);
        position: absolute;
        bottom: 0;
        left: 50%;
        transform: translate(-50%, 0);
    }
    .scroll-hint {
        display: inline-block;
        vertical-align: middle;
        width: 2rem;
        height: 2rem;
        border: 2px solid var(--color-fg); 
        border-radius: 100%; 
        padding: 0.25rem;
        margin-left: 0.25rem;
    }
    .scroll-hint :global(svg) {
        width: 100%;
        height: 100%;
        transform: rotate(135deg);
    }
    /* a gentle downward nudge, only for people who haven't asked for less motion */
    @media (prefers-reduced-motion: no-preference) {
        .scroll-hint {
            animation: hint-bounce 1s ease-in-out infinite;
        }
    }
    @keyframes hint-bounce {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(4px); }
    }
    h1 {
        /* image height drives everything; width follows from its 494×1200 ratio */
        --img-h: 80svh;
        --img-w: calc(var(--img-h) * 494 / 1200);
        --gap: 1rem;
        /* how far the right span tucks in, as a share of the image width */
        --right-inset: 0.5;

        margin: 0;
        display: grid;
        grid-template-columns: 1fr auto 1fr;
        align-items: center;
        column-gap: var(--gap);
        font-size: 2.5rem;
        width: 100%;
        height: 100%;
    }
    h1 img {
        display: block;
        height: var(--img-h);
        width: auto;
    }
    /* --- TV static + glitch --- */
    .glitch {
        position: relative;
        display: block;
    }
    .strip,
    .static {
        position: absolute;
        inset: 0;
        pointer-events: none;
    }
    /* the full image stays for layout + alt text; the strips draw what you see */
    .base {
        opacity: 0;
    }
    .strip {
        clip-path: inset(var(--top) 0 var(--bottom) 0);
        animation: strip-shift 4s steps(1) infinite;
    }
    /* noise + scanlines, masked to the image's own shape so transparent areas stay clean */
    .static {
        background:
            repeating-linear-gradient(to bottom, rgb(0 0 0 / 0.15) 0 1px, transparent 1px 3px),
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
        mask: var(--src) center / 100% 100% no-repeat;
        -webkit-mask: var(--src) center / 100% 100% no-repeat;
        mix-blend-mode: overlay;
        opacity: 0.35;
        animation: static-flicker 0.4s steps(1) infinite;
    }

    @keyframes static-flicker {
        0%   { background-position: 0 0, 0 0; }
        25%  { background-position: 0 1px, -60px 40px; }
        50%  { background-position: 0 2px, 80px -30px; }
        75%  { background-position: 0 1px, -20px -90px; }
    }
    /* mostly still, then a short jitter: out, back the other way, out again, settle */
    @keyframes strip-shift {
        0%, 100% { transform: none; }
        84% { transform: translateX(var(--dx)); }
        86% { transform: translateX(calc(var(--dx) * -0.6)); }
        88% { transform: none; }
        89% { transform: translateX(calc(var(--dx) * 0.4)); }
        91% { transform: none; }
    }

    @media (prefers-reduced-motion: reduce) {
        .strip { animation: none; }
        .static { animation: none; }
        .cell img,
        .cell p { transition: none; transform: none; }
        .cell,
        .cell video { transition: none; }
    }

    .hedLeft {
        text-align: right;
    }
    .hedRight {
        text-align: left;
        margin-left: calc(var(--img-w) * var(--right-inset) * -1);
    }
	.steps {
		position: relative;
		margin-top: 0;
		z-index: 1;
	}
	.step {
		min-height: 90svh;
		display: flex;
		align-items: center;
		justify-content: center;
	}
    .step:last-of-type {
        opacity: 0;
        pointer-events: none;
    }
	.card {
        font-size: 17px;
        line-height: 1.5;
		max-width: 460px;
		padding: 14px 18px;
		background: var(--wnba-tan-bg);
		border: 1px solid var(--color-rule);
        border-radius: 4px;
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
		opacity: 0.4;
		transition: opacity 300ms ease;
	}
	.step.active .card {
		opacity: 1;
	}
</style>
