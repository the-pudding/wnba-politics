<script>
    import { getContext, onMount } from "svelte";
	import { base } from "$app/paths";
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import { faces, clipPops } from "$utils/clips.js";
    const copy = getContext("copy");

	let { steps = [] } = $props();

	// undefined until the first step scrolls into view (Scrolly sets it back to
	// undefined when no step is in view)
	let introIndex = $state(undefined);

	// what the wall and header actually show. Scrolly also reports undefined once
	// you've scrolled past the steps; holding the last step there stops the header
	// flashing back in on the way up. Only reset when the steps are below the viewport.
	let stepsEl = $state();
	let shownIndex = $state(undefined);
	$effect(() => {
		if (introIndex !== undefined) shownIndex = introIndex;
		else if (stepsEl && stepsEl.getBoundingClientRect().top > 0) shownIndex = undefined;
	});

	// what the background wall shows: nothing, then screenshots, then headlines,
	// then the headlines clear away one by one (step 2 on)
	let wall = $derived(
		shownIndex === undefined
			? "empty"
			: shownIndex === 1
				? "images"
				: shownIndex === 2
					? "text"
					: "cleared"
	);

	// headlines for the text tiles, from the same file the swarm uses
	let headlines = $state([]);
	onMount(() => {
		let alive = true;
		fetch(`${base}/data/framing_swarm.json`)
			.then((r) => r.json())
			.then((D) => {
				if (alive) headlines = shuffle(D.headlines.map((r) => r[1]), 7);
			});
		return () => (alive = false);
	});

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
		).map((order, i) => ({
			delay: (order / Math.max(1, cols * rows)) * STAGGER,
			src: GRID_IMAGES[i % GRID_IMAGES.length],
			headline: headlines.length ? headlines[i % headlines.length] : ""
		}))
	);

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
            <p class="byline">By {@html copy.meta.byline}, with {@html copy.meta.with}</p>
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
                <div class="cell {wall}" style="--d: {cell.delay}s">
                    <img src={cell.src} alt="" />
                    <p>{cell.headline}</p>
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
    }
    .cell img,
    .cell p {
        position: absolute;
        inset: 0;
        opacity: 0;
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
        min-height: 50vh
    }
	.card {
        font-size: 17px;
        line-height: 1.5;
		max-width: 460px;
		padding: 14px 18px;
		background: var(--color-white);
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
