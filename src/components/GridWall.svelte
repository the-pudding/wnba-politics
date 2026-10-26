<script>
    import { getContext, onMount } from "svelte";
	import { base } from "$app/paths";
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import HeadlineClip from "$components/HeadlineClip.svelte";
	import { fade } from "svelte/transition";
	import { faces, clipPops } from "$utils/clips.js";
	import arrowSvg from "$svg/arrow-up-right.svg";
    const copy = getContext("copy");

	let { id = "intro", steps = [], header, highlights, videos } = $props();

	// The copy doc sets up the wall. Each step can carry its own scene:
	//   text: …
	//   wall: images | text | cleared
	//   pull: clips | heads        (optional)
	//   images: gridFox | gridOther (optional, which screenshot folder; a step without
	//                 one keeps the folder of the step before, starting with gridFox)
	//   [.videos] or [.highlights] (optional, what this step's pull-out shows)
	// plus `header: true` on the block. [.highlights] / [.videos] on the block itself
	// are the default for any pulling step that doesn't list its own.
	// Anything the doc leaves out falls back to WALLS below.
	//
	// what each wall does, by the `id` in the copy doc. `scenes` has one entry per step:
	//   wall: "images" (screenshots), "text" (headlines) or "cleared" (headlines fade away)
	//   pull: "clips" (tiles lift out and play the videos, one tile per video) or "heads"
	//         (headline tiles lift out as clippings, one per highlight), or leave it off
	//   images: which folder in static/images/ the screenshots come from (default "gridFox").
	//         Changing it between steps swaps the tiles over in a scattered order.
	// videos: file names in static/video/, without .mp4 (each needs a matching .jpg poster)
	// Steps past the end of the list keep the last scene. Before the first step the wall is empty.
	const WALLS = {
		intro: {
			header: true,
			// written like the copy doc: <b>bold</b>, ==highlight==, ((Name|face)) for a portrait
			highlights: [
				"<b>Caitlin Clark</b> ((Caitlin Clark|face)) fans <b>==unload==</b> on WNBA, <b>Alyssa Thomas</b> ((Alyssa Thomas|face)) after <b>==violent sequence==</b> leaves Fever star battered",
				"WNBA star who <b>==hurt Caitlin Clark's ((Caitlin Clark|face)) eye==</b> calls for league to take action <b>==against Trump administration policies==</b>",
				"<b>Dave Portnoy</b> calls <b>Angel Reese ((Angel Reese|face)) ==a jacka-- for jealousy of Caitlin Clark</b>== ((Caitlin Clark|face)) in response to ESPN analyst"
			],
			videos: ["watters-tv", "watters-tv", "watters-tv"],
			scenes: [
				{ wall: "images" },
				{ wall: "images", pull: "clips" },
				{ wall: "text" },
				{ wall: "text", pull: "heads" },
				{ wall: "cleared" }
			]
		},
		// draft: swap in the outro's own scenes, headlines and clip
		outro: {
			header: true,
			// one headline tile pulls out per highlight; with none listed, "heads" pulls out nothing
			highlights: [],
			videos: ["watters-tv"],
			scenes: [
				{ wall: "images" }, // Fox in the conservative media machine
				{ wall: "images", pull: "clips" }, // Watters: Fox doesn't care about women's hoops
				{ wall: "images", images: "gridOther" }, // swap to the other outlets' screenshots
				{ wall: "text" }, // sports have always been political
				{ wall: "text", pull: "heads" }, // narratives at odds with the players
				{ wall: "cleared" } // inclusivity, ragebait, blank
			]
		}
	};
	// a doc list comes through as an array of strings; trim them and drop blanks
	const list = (v) =>
		Array.isArray(v) ? v.map((s) => String(s).trim()).filter(Boolean) : undefined;

	// one scene per step from the doc. A step with no `wall:` keeps the wall of the
	// step before it (but doesn't repeat its pull-out). `images:` carries over the same way.
	function scenesFromSteps(steps) {
		let last = "empty";
		let folder;
		return steps.map((s) => {
			const wall = s.wall?.trim() || last;
			last = wall;
			const scene = { wall };
			if (s.pull?.trim()) scene.pull = s.pull.trim();
			// what this step itself says (blank if it inherits), for the kicker
			scene.ownImages = s.images?.trim() || "";
			folder = scene.ownImages || folder;
			if (folder) scene.images = folder;
			const v = list(s.videos);
			if (v) scene.videos = v;
			const h = list(s.highlights);
			if (h) scene.highlights = h;
			return scene;
		});
	}

	let config = $derived.by(() => {
		const fallback = WALLS[id] ?? WALLS.intro;
		return {
			header: header ?? fallback.header,
			highlights: list(highlights) ?? fallback.highlights,
			videos: list(videos) ?? fallback.videos,
			scenes: steps.some((s) => s.wall?.trim()) ? scenesFromSteps(steps) : fallback.scenes
		};
	});

	// undefined until the first step scrolls into view (Scrolly sets it back to
	// undefined when no step is in view)
	let stepIndex = $state(undefined);

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
		else if (stepIndex !== undefined) shownIndex = stepIndex;
	});

	// the scene for the step in view
	let sceneIndex = $derived(
		shownIndex === undefined ? undefined : Math.min(shownIndex, config.scenes.length - 1)
	);
	let scene = $derived(
		sceneIndex === undefined ? { wall: "empty" } : config.scenes[sceneIndex] ?? { wall: "empty" }
	);

	// every distinct pull-out on this wall: its kind ("clips" or "heads") and what it
	// shows. A step that pulls without listing its own uses the block's list. Every
	// pulling step gets its own group, so each one lifts out tiles in a different place.
	let pulls = $derived.by(() => {
		const groups = [];
		const sceneGroup = config.scenes.map((s) => {
			if (!s.pull) return -1;
			const items =
				s.pull === "clips" ? s.videos ?? config.videos : s.highlights ?? config.highlights;
			groups.push({ type: s.pull, items });
			return groups.length - 1;
		});
		return { groups, sceneGroup };
	});
	// the group pulled out right now, or -1
	let activeGroup = $derived(sceneIndex === undefined ? -1 : pulls.sceneGroup[sceneIndex] ?? -1);
	// what the background wall shows, and which tiles (if any) are pulled out
	let wall = $derived(scene.wall);
	let pull = $derived(scene.pull);
	let imageSet = $derived(scene.images ?? DEFAULT_IMAGES);
	// kicker in the top-left corner: whose coverage the wall is showing. A screenshot wall
	// follows its folder (carried over or not); a headline wall is Fox unless the step
	// itself names a folder.
	const KICKERS = { gridFox: "Fox News", gridOther: "Other outlets" };
	let kickerSet = $derived(
		wall === "images"
			? imageSet
			: ("ownImages" in scene ? scene.ownImages : scene.images) || DEFAULT_IMAGES
	);
	let kicker = $derived(KICKERS[kickerSet] ?? KICKERS[DEFAULT_IMAGES]);
	// every image folder this wall uses; each tile stacks one screenshot per folder
	let imageSets = $derived([
		...new Set([DEFAULT_IMAGES, ...config.scenes.map((s) => s.images).filter(Boolean)])
	]);

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
	// highlight headlines from every step, keyed by norm(): { text, styled, date }
	let featuredHeadlines = $state(new Map());
	onMount(() => {
		let alive = true;
		fetch(`${base}/data/framing_swarm.json`)
			.then((r) => r.json())
			.then((D) => {
				if (!alive) return;
				const all = D.headlines.map((r) => r[1]);
				const highlights = pulls.groups.filter((g) => g.type === "heads").flatMap((g) => g.items);
				// the wall tile shows the plain text from the data; the pull-out card shows
				// the styled version typed in the doc. No date if it isn't found in the data.
				const found = new Map();
				for (const h of highlights) {
					const key = norm(h);
					const row = D.headlines.find((r) => norm(r[1]) === key);
					found.set(
						key,
						row
							? { text: row[1], styled: h, date: formatDate(row[0]) }
							: { text: plain(h), styled: h, date: "" }
					);
				}
				featuredHeadlines = found;
				const picked = new Set(found.keys());
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
	// screenshots in static/images/<folder>/grid-N.png (how many each folder has),
	// repeated in order to fill the wall
	const IMAGE_COUNTS = { gridFox: 41, gridOther: 40 };
	const DEFAULT_IMAGES = "gridFox";
	const imageSrc = (set, i) => `${base}/images/${set}/grid-${i % (IMAGE_COUNTS[set] ?? 40)}.png`;

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
			// the pull-out tiles always carry their highlight headline, so it's on the wall
			// the whole time and the same one lifts out on its step
			const t = tiles.get(i);
			const pinned =
				t?.type === "heads"
					? featuredHeadlines.get(norm(pulls.groups[t.g].items[t.k]))
					: undefined;
			return {
				delay: (order / Math.max(1, cols * rows)) * STAGGER,
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

	// pull-outs: up to three tiles lift out of the wall and grow, one per video or
	// highlight in the step's list. Each step's group gets its own tiles and the next
	// layout in the list below, so the pull-outs land somewhere new on every step.
	// Cards are centered and at most 460px wide, so on wide screens they go in the side
	// gutters; on narrow screens there are no gutters, so they go in strips along the
	// top and bottom.
	const CARD_HALF = 460 / 2 + 32; // half the card plus breathing room
	const PAD = 16;
	// wide screens: [side, height as a share of the screen] for up to three pull-outs
	const WIDE_LAYOUTS = [
		[["L", 0.27], ["R", 0.5], ["L", 0.73]],
		[["R", 0.27], ["L", 0.5], ["R", 0.73]],
		[["R", 0.73], ["L", 0.35], ["R", 0.27]],
		[["L", 0.73], ["R", 0.4], ["L", 0.27]]
	];
	// narrow screens: [share of the width, "top" | "top2" (a little lower) | "bottom" | "bottom2" (a little higher)]
	const NARROW_LAYOUTS = [
		[[0.27, "top"], [0.73, "top2"], [0.5, "bottom"]],
		[[0.73, "top"], [0.27, "top2"], [0.5, "bottom"]],
		[[0.5, "top"], [0.27, "bottom2"], [0.73, "bottom"]],
		[[0.5, "top"], [0.73, "bottom2"], [0.27, "bottom"]]
	];
	// tile index -> { g: group, type, k: place in its list, dx, dy, scale }
	let tiles = $derived.by(() => {
		const map = new Map();
		if (!cols || !rows) return map;
		const gutter = gridW / 2 - CARD_HALF;
		const wide = gutter >= 160;
		let w, layouts;
		if (wide) {
			w = Math.min(320, gutter - 2 * PAD, (gridH * 0.4) / TILE_RATIO);
			const xL = gutter / 2;
			const xR = gridW - xL;
			layouts = WIDE_LAYOUTS.map((l) => l.map(([side, y]) => [side === "L" ? xL : xR, gridH * y]));
		} else {
			w = Math.min(gridW * 0.44, (gridH * 0.2) / TILE_RATIO);
			const h = w * TILE_RATIO;
			const Y = {
				top: PAD + h / 2,
				top2: PAD + h / 2 + h * 0.35,
				bottom: gridH - PAD - h / 2,
				bottom2: gridH - PAD - h / 2 - h * 0.35
			};
			layouts = NARROW_LAYOUTS.map((l) => l.map(([x, y]) => [gridW * x, Y[y]]));
		}
		// the grid is centered, so its overflow is split evenly on each side
		const x0 = (gridW - cols * tileW) / 2;
		const y0 = (gridH - rows * tileH) / 2;
		const scale = w / tileW;
		// one tile per video / highlight headline; a single one takes the middle spot
		const spotsFor = (list, n) => (n === 1 ? [list[1]] : list.slice(0, n));
		pulls.groups.forEach((group, g) => {
			spotsFor(layouts[g % layouts.length], group.items.length).forEach(([tx, ty], k) => {
				// take the tile nearest the spot so it only has a short way to travel,
				// skipping tiles another group already uses
				let col = Math.min(cols - 1, Math.max(0, Math.floor((tx - x0) / tileW)));
				let row = Math.min(rows - 1, Math.max(0, Math.floor((ty - y0) / tileH)));
				while (map.has(row * cols + col)) col = (col + 1) % cols;
				const cx = x0 + (col + 0.5) * tileW;
				const cy = y0 + (row + 0.5) * tileH;
				// k staggers the pull-outs, one after another
				map.set(row * cols + col, { g, type: group.type, k, dx: tx - cx, dy: ty - cy, scale });
			});
		});
		return map;
	});

	// a clip tile plays the video at its place in its group's list
	const videoName = (t) => pulls.groups[t.g].items[t.k];
	const videoSrc = (t) => `${base}/video/${videoName(t)}.mp4`;
	const posterSrc = (t) => `${base}/video/${videoName(t)}.jpg`;
	const FEATURE_STAGGER = 0.15; // seconds between each pull-out

	// only play while pulled out, so the hidden clips don't run in the background
	function playWhen(node, on) {
		const set = (v) => (v ? node.play().catch(() => {}) : node.pause());
		set(on);
		return { update: set };
	}

	// once a pull-out has shown, the picked tiles skip the staggered fade so they settle
	// back into the wall right away on the way up. Reset when the wall empties.
	let featureSeen = $state(false);
	$effect(() => {
		if (pull) featureSeen = true;
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
</script>

<svelte:window onscroll={measure} onresize={measure} />

<div class="grid-wall grid-wall-{id}">
	<div class="sticky">
        {#if config.header && id == "intro"}
        <header class="intro-wall-header" class:off={shownIndex !== undefined}>
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
        {:else if config.header && id == "outro"}
            <div class="outro-header" class:off={shownIndex !== undefined}>
                <h2>This coverage matters</h2>
            </div>
        {/if}
        <p class="kicker" class:off={wall === "empty"} class:other={kicker == "Other outlets"}>{kicker}</p>
        <!-- wall of screenshots / headlines behind the steps -->
        <div
            class="bg-grid"
            aria-hidden="true"
            bind:clientWidth={gridW}
            bind:clientHeight={gridH}
            style="--cols: {cols}; --rows: {rows}; --tile-w: {tileW}px; --tile-h: {tileH}px;"
        >
            {#each gridCells as cell, i (i)}
                {@const spot = tiles.get(i)}
                {@const f = spot && spot.g === activeGroup ? spot : undefined}
                <div
                    class="cell {wall}"
                    class:featured={f}
                    class:pull-clips={f?.type === "clips"}
                    class:pull-heads={f?.type === "heads"}
                    class:has-clip={!!cell.date}
                    class:quick={featureSeen && !!spot}
                    style="--d: {cell.delay}s; {spot ? `--s0: ${spot.scale};` : ''} {f ? `--dx: ${f.dx}px; --dy: ${f.dy}px; --s: ${f.scale}; --fd: ${f.k * FEATURE_STAGGER}s;` : ''}"
                >
                    {#each imageSets as set (set)}
                        <img src={imageSrc(set, i)} alt="" class:on={set === imageSet} />
                    {/each}
                    {#if spot?.type === "clips"}
                        <video
                            src={videoSrc(spot)}
                            poster={posterSrc(spot)}
                            muted
                            loop
                            playsinline
                            preload="metadata"
                            use:playWhen={!!f}
                        ></video>
                    {/if}
                    <p>{cell.headline}</p>
                    {#if f?.type === "heads" && cell.date}
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
	</div>

	<div class="steps" bind:this={stepsEl}>
		<Scrolly bind:value={stepIndex}>
			{#each steps as step, i}
				<div class="step" class:active={stepIndex === i}>
					{#if step.text?.trim()}
						<p class="card">{@html clipPops(faces(step.text, base), base)}</p>
					{/if}
				</div>
			{/each}
		</Scrolly>
	</div>
</div>

<style>
	.grid-wall {
        width: 100%;
		position: relative;
	}
	.sticky {
		position: sticky;
		top: 0;
        width: 100%;
		height: 100svh;
	}
    /* looks come from the global .kicker in app.css; this only places it */
    .kicker {
        position: absolute;
        top: 16px;
        left: 16px;
        z-index: 2;
        margin: 0;
        transition: opacity 300ms ease;
    }
    /* hidden before the first step, while the header is up */
    .kicker.off {
        opacity: 0;
    }
    .kicker.other {
        background-color: var(--color-fg);
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
    .cell.pull-clips video {
        opacity: 1;
        transition-delay: var(--fd);
    }
    .cell.images.quick img,
    .cell.text.quick p {
        transition-delay: 0s;
    }
    /* "heads" pull-out: the pulled-out headline at full strength */
    .cell.pull-heads p {
        opacity: 1;
        transition-delay: var(--fd);
    }
    .cell.images.pull-clips img.on {
        opacity: 1;
        filter: none;
        transition-delay: var(--fd);
    }
    /* a pulled-out headline becomes a gallery clipping. It's laid out at its pulled-out
       width and shrunk by 1/--s0 to fit the tile, so the cell's scale-up brings it back to
       full size and sharp. */
    .cell.has-clip.pull-heads {
        overflow: visible;
        box-shadow: none;
    }
    .cell.has-clip.pull-heads p {
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
    .cell.text p {
        opacity: 0.5;
        transform: none;
        transition-delay: var(--d);
    }
    /* screenshots sit back faintly. Only the current folder's shows; when the folder
       changes, each tile swaps old for new at its own scattered delay */
    .cell.images img {
        transition-delay: var(--d);
    }
    .cell.images img.on {
        opacity: 0.15;
        transform: none;
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

    .outro-header {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        transition:
            opacity 400ms ease,
            visibility 0s;
    }

    .outro-header.off {
        opacity: 0;
        visibility: hidden;
        pointer-events: none;
        transition:
            opacity 400ms ease,
            visibility 0s 400ms;
    }
</style>
