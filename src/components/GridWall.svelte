<script>
    import { getContext, onMount } from "svelte";
	import { base } from "$app/paths";
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import HeadlineClip from "$components/HeadlineClip.svelte";
	import { fade } from "svelte/transition";
	import { cubicOut } from "svelte/easing";
	import { faces, clipPops } from "$utils/clips.js";
	import { titleCase } from "$utils/titleCase.js";
	import { sound, clipSound, wallVideos, toggleSound, preloadSound } from "$utils/sound.svelte.js";
	import arrowSvg from "$svg/arrow-up-right.svg";
	// the corner bubble and the sound button's icons, from Lucide (lucide.dev)
	import MessageCircle from "@lucide/svelte/icons/message-circle";
	import Volume2 from "@lucide/svelte/icons/volume-2";
	import VolumeOff from "@lucide/svelte/icons/volume-off";
    const copy = getContext("copy");

	let { id = "intro", steps = [], header, highlights, videos } = $props();

	// the announcer's call on the intro title, from the Doc's top section:
	//   logoCallStyle: corner | bubble | byline | none   (a small bubble in the top-right
	//                  corner, a speech bubble by the image, or a line over the byline)
	//   logoCall: You bet! From beyond the logo!
	//   logoCredit: ESPN’s Ryan Ruocco
	//   logoCallShort: From the logo!   (the corner bubble's words)
	//   logoLink: …   (the corner bubble links to the clip)
	//   logoCallSpot: upper | lower   (the corner bubble in the upper right, its tail
	//                  pointing up and out, or beside the byline, pointing down and out
	//                  toward the broadcast table)
	const LOGO_CALL = "You bet! From beyond the logo!";
	const LOGO_CREDIT = "ESPN’s Ryan Ruocco";
	const LOGO_CALL_SHORT = "From the logo!";
	const LOGO_LINK = "https://x.com/IndianaFever/status/1919143866818515093";
	// once the wall comes in, the title drops down onto it, in red, for this many steps:
	// how big it gets there (share of its size on the title page) and how far from the top
	const TITLE_STEPS = 1;
	const TITLE_SCALE = 0.75;
	const TITLE_TOP = 14; // px
	const callStyle = String(copy.meta?.logoCallStyle ?? "corner").trim().toLowerCase();
	const callText = copy.meta?.logoCall || LOGO_CALL;
	const callCredit = copy.meta?.logoCredit || LOGO_CREDIT;
	const callShort = copy.meta?.logoCallShort || LOGO_CALL_SHORT;
	const callLink = copy.meta?.logoLink || LOGO_LINK;
	const CALL_SPOT = "upper";
	const callSpot = String(copy.meta?.logoCallSpot || CALL_SPOT).trim().toLowerCase();

	// sound: off until the reader turns it on (one switch for the whole page, see
	// utils/sound.svelte.js). Turning it on from the title page plays the call.
	const CALL = `${base}/audio/logo-call.mp3`;
	onMount(() => {
		// fetched now so it plays the moment the switch is tapped
		if (config.header && id === "intro") preloadSound(CALL);
	});

	// The copy doc sets up the wall. Each step can carry its own scene:
	//   text: …
	//   wall: images | text | cleared
	//   pull: clips | heads        (optional)
	//   images: gridFox | gridOther (optional, which screenshot folder; a step without
	//                 one keeps the folder of the step before, starting with gridFox)
	//   [.videos] or [.highlights] (optional, what this step's pull-out shows)
	//   players: Angel Reese       (optional, on a text wall: only headlines naming these
	//                 people, comma-separated, as in the explore table)
	//   tone: negative             (optional, on a text wall: only headlines of this tone,
	//                 negative, neutral or positive, as in the explore table)
	//   transition: wipe | off     (optional, on a step that changes `images:`. wipe: a band
	//                 of static sweeps across and wipes the wall over to the new screenshots.
	//                 off: the wall switches off like an old TV, to a line, a dot and black,
	//                 then switches back on showing the new screenshots. Without it the tiles
	//                 swap one by one. A step with a transition but no `images:` switches to
	//                 the next different folder a later step names)
	//   audio: storm-doppler       (optional, on a step that pulls clips: that clip plays
	//                 with its sound, from the start, once the reader has turned sound on.
	//                 Several, comma-separated, take turns in that order: each is heard to
	//                 its end, then the next starts, then back to the first. The page’s
	//                 one sound switch sits in the top-right corner)
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
		return steps.map((s, i) => {
			const wall = s.wall?.trim() || last;
			last = wall;
			const scene = { wall };
			if (s.pull?.trim()) scene.pull = s.pull.trim();
			// what this step itself says (blank if it inherits), for the kicker
			scene.ownImages = s.images?.trim() || "";
			// a transition is a change of screenshots: a step that asks for one without
			// naming a folder switches to the next different folder a later step names
			if (s.transition?.trim() && !scene.ownImages) {
				const next = steps
					.slice(i + 1)
					.map((t) => t.images?.trim())
					.find((f) => f && f !== folder);
				if (next) scene.ownImages = next;
			}
			folder = scene.ownImages || folder;
			if (folder) scene.images = folder;
			const v = list(s.videos);
			if (v) scene.videos = v;
			const h = list(s.highlights);
			if (h) scene.highlights = h;
			const pool = poolKey(s);
			if (pool) scene.pool = pool;
			if (s.transition?.trim()) scene.transition = s.transition.trim().toLowerCase();
			const audio = String(s.audio ?? "")
				.split(",")
				.map((a) => a.trim())
				.filter(Boolean);
			if (audio.length) scene.audio = audio;
			return scene;
		});
	}

	// a step's headline filter (players and tone) as one key; "" is every headline
	function poolKey(s) {
		const players = String(s.players ?? "")
			.split(",")
			.map((p) => p.trim())
			.filter(Boolean);
		const tone = String(s.tone ?? "").trim().toLowerCase();
		return players.length || tone ? `${players.join(",")}|${tone}` : "";
	}

	let config = $derived.by(() => {
		const fallback = WALLS[id] ?? WALLS.intro;
		return {
			// the doc sends `header: false` as the text "false"
			header:
				header === undefined || header === null || header === ""
					? fallback.header
					: header !== false && String(header).trim().toLowerCase() !== "false",
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
	// a step with a transition (wipe, off) starts it as soon as its card comes up from
	// the bottom of the screen, rather than once it's the step most in view
	const TRANSITION_LINE = 0.9;
	let early = $state(-1);
	// how fast the reader is scrolling, in screens a second (smoothed)
	let scrollSpeed = 0;
	let lastScroll = { y: 0, t: 0 };
	function measure() {
		const now = performance.now();
		const moved = Math.abs(scrollY - lastScroll.y) / innerHeight;
		const secs = (now - lastScroll.t) / 1000;
		if (secs > 0 && secs < 0.5) scrollSpeed = 0.6 * scrollSpeed + 0.4 * (moved / secs);
		else scrollSpeed = 0;
		lastScroll = { y: scrollY, t: now };
		if (stepsEl) beforeSteps = stepsEl.getBoundingClientRect().top > window.innerHeight * 0.5;
		let e = -1;
		stepsEl?.querySelectorAll(".step").forEach((el, i) => {
			if (!config.scenes[i]?.transition) return;
			const top = (el.querySelector(".card") ?? el).getBoundingClientRect().top;
			if (top < window.innerHeight * TRANSITION_LINE) e = i;
		});
		early = e;
	}
	onMount(measure);
	let shownIndex = $state(undefined);
	$effect(() => {
		if (beforeSteps) shownIndex = undefined;
		else if (stepIndex !== undefined || early >= 0) shownIndex = Math.max(stepIndex ?? -1, early);
	});

	// the title on the wall: each half moves from where it sits on the title page to meet
	// the other at the top, scaled down, in one line. It stays there (and fades out there)
	// once the steps start; measured after the page has laid it out for the wall.
	// offsetLeft/Top ignore the transform. Wide screens only.
	let titleOnWall = $derived(id === "intro" && shownIndex !== undefined);
	let hedLeftEl = $state(),
		hedRightEl = $state(),
		viewW = $state(0);
	let titleMoves = $state({ left: "", right: "" });
	$effect(() => {
		viewW; // again when the window changes size
		// on smaller screens the title fades out instead (see the CSS)
		if (!titleOnWall || !hedLeftEl || !hedRightEl || viewW <= 900) {
			titleMoves = { left: "", right: "" };
			return;
		}
		const L = hedLeftEl,
			R = hedRightEl;
		// a frame later, once the page has laid the words out for the wall
		const frame = requestAnimationFrame(() => {
			const W = L.offsetParent.clientWidth;
			const both = L.offsetWidth + R.offsetWidth;
			const k = Math.min(TITLE_SCALE, (W - 2 * 160) / both);
			const start = (W - both * k) / 2;
			const move = (el, x) =>
				`translate(${x - el.offsetLeft}px, ${TITLE_TOP - el.offsetTop}px) scale(${k})`;
			// the right half tucks a pixel under the left's edge, so no sliver of wall shows
			// between them (their widths are whole pixels, scaled to fractions)
			titleMoves = {
				left: move(L, start),
				right: move(R, start + L.offsetWidth * k - 1)
			};
		});
		return () => cancelAnimationFrame(frame);
	});

	// the scene for the step in view
	let sceneIndex = $derived(
		shownIndex === undefined ? undefined : Math.min(shownIndex, config.scenes.length - 1)
	);
	// with no title card (header: false), the wall shows its first look, without the
	// pull-out, as it scrolls in, so there's no empty screen before the first step
	let scene = $derived(
		sceneIndex === undefined
			? !config.header && config.scenes[0]
				? { wall: config.scenes[0].wall, images: config.scenes[0].images }
				: { wall: "empty" }
			: config.scenes[sceneIndex] ?? { wall: "empty" }
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
	// the closing step (wall: cleared): the whole wall fades out together, and whatever
	// the step before pulled out stays where it is and fades with it
	let closing = $derived(sceneIndex !== undefined && scene.wall === "cleared");
	let heldGroup = $derived(closing ? pulls.sceneGroup[sceneIndex - 1] ?? -1 : -1);
	// the clips the next step pulls out are already lit and playing in their places on
	// the wall, so that step only has to lift them out. -1 when there are none: the next
	// step doesn't pull clips, or this one shows no screenshots or pulls out its own.
	// (i = -1 is before the first step: a wall with no title card already shows then)
	const readyAt = (i) => {
		if (CLIPS_EARLY === "off") return -1;
		const first = config.scenes[0];
		const now = i < 0 ? !config.header && first && { wall: first.wall } : config.scenes[i],
			next = config.scenes[i + 1];
		if (!now || now.pull || now.wall !== "images" || next?.pull !== "clips") return -1;
		return pulls.sceneGroup[i + 1];
	};
	// (only while this wall is on screen, so clips don't play, or talk, from further up
	// or down the page; the clips below check it too)
	let wallInView = $state(false);
	// and whether it's filling the screen (crossing its middle): the section menu on the
	// right steps aside then, so it doesn't sit over the pulled-out clips
	let wallFilling = $state(false);
	function watchView(node) {
		const io = new IntersectionObserver(([e]) => (wallInView = e.isIntersecting));
		const middle = new IntersectionObserver(([e]) => (wallFilling = e.isIntersecting), {
			rootMargin: "-45% 0px -45% 0px"
		});
		io.observe(node);
		middle.observe(node);
		return {
			destroy: () => {
				io.disconnect();
				middle.disconnect();
			}
		};
	}
	let readyGroup = $derived(wallInView ? readyAt(sceneIndex ?? -1) : -1);
	// the pulled-out clips were lit on the step before, so they lift out straight away
	let liftNow = $derived(
		CLIPS_EARLY === "lit" && activeGroup >= 0 && readyAt(sceneIndex - 1) === activeGroup
	);
	// what the background wall shows, and which tiles (if any) are pulled out
	let wall = $derived(scene.wall);
	let pull = $derived(scene.pull);
	let imageSet = $derived(scene.images ?? DEFAULT_IMAGES);
	// a wipe runs when the screenshots change on the way into or out of a step that asks
	// for one; each run gets a new key so the band starts over
	let wipeKey = $state(0);
	let wiping = $state(false);
	// the switch-off: the old screenshots stay up until the screen has gone dark
	let powerKey = $state(0);
	let powering = $state(false);
	let powerTime = $state(0); // this switch-off's length, set as it starts: POWER, or POWER_FAST
	let poweringNow = false; // (the same as powering, without the effect below watching it)
	let heldSet = $state(undefined);
	let shownSet = $derived(heldSet ?? imageSet);
	let lastSet;
	let lastIndex;
	let wipeTimer;
	let powerTimers = [];
	$effect(() => {
		const set = imageSet;
		const idx = sceneIndex;
		const kind = [idx, lastIndex].map((i) => config.scenes[i]?.transition).find(Boolean);
		if (lastSet && set !== lastSet && kind === "wipe") {
			wiping = true;
			wipeKey += 1;
			clearTimeout(wipeTimer);
			wipeTimer = setTimeout(() => (wiping = false), (WIPE + 0.4) * 1000);
		}
		const endPower = () => {
			powerTimers.forEach(clearTimeout);
			heldSet = undefined;
			powering = poweringNow = false;
		};
		if (lastSet && set !== lastSet && kind === "off") {
			powerTimers.forEach(clearTimeout);
			powerTime = scrollSpeed > FAST_SCROLL ? POWER_FAST : POWER;
			heldSet = lastSet;
			powering = poweringNow = true;
			powerKey += 1;
			powerTimers = [
				setTimeout(() => (heldSet = undefined), powerTime * 0.45 * 1000),
				setTimeout(endPower, (powerTime + 0.1) * 1000)
			];
		} else if (poweringNow && idx !== lastIndex) {
			// scrolled on to another step mid-switch: finish it now
			endPower();
		}
		lastSet = set;
		lastIndex = idx;
	});
	// kicker in the top-left corner: whose coverage the wall is showing. A screenshot wall
	// follows its folder (carried over or not); a headline wall is Fox unless the step
	// itself names a folder.
	const KICKERS = { gridFox: "Fox News", gridOther: "Other outlets" };
	let kickerSet = $derived(
		wall === "images"
			? shownSet
			: ("ownImages" in scene ? scene.ownImages : scene.images) || DEFAULT_IMAGES
	);
	let kickerNow = $derived(KICKERS[kickerSet] ?? KICKERS[DEFAULT_IMAGES]);
	// the label waits a moment for the change to settle: on a switch-off the old
	// screenshots are held only after the step changes, and the label shouldn't flicker
	let kicker = $state(KICKERS.gridFox);
	$effect(() => {
		const next = kickerNow;
		const wait = setTimeout(() => (kicker = next), 60);
		return () => clearTimeout(wait);
	});
	// when the coverage changes, the old label wipes away into its left edge and the new
	// one wipes back out of it, like a picture switching off and on (seconds)
	const KICKER_OUT = 0.25;
	const KICKER_IN = 0.4;
	function wipeLabel(node, { delay = 0, duration }) {
		return {
			delay: delay * 1000,
			duration: duration * 1000,
			css: (t) => `clip-path: inset(0 ${(1 - cubicOut(t)) * 100}% 0 0)`
		};
	}
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
	// the pools for steps that filter their headlines, by poolKey()
	let filteredHeadlines = $state({});
	// every pool a text wall uses ("" is the full set), and the one showing now
	let poolKeys = $derived(["", ...new Set(config.scenes.map((s) => s.pool).filter(Boolean))]);
	let activePool = $derived(scene.pool ?? "");
	// highlight headlines from every step, keyed by norm(): { text, styled, date }
	let featuredHeadlines = $state(new Map());
	onMount(() => {
		let alive = true;
		fetch(`${base}/data/framing_swarm.json`)
			.then((r) => r.json())
			.then((D) => {
				if (!alive) return;
				// each tile: the headline in Title Case, with the people it names marked,
				// and its month for the line above it
				const tile = (r) => {
					const text = titleCase(r[1]);
					return { text, html: markNames(text, r[3].map((n) => D.names[n])), date: shortDate(r[0]) };
				};
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
							? { tile: tile(row), styled: h, date: formatDate(row[0]) }
							: { tile: { text: plain(h), html: escape(plain(h)), date: "" }, styled: h, date: "" }
					);
				}
				featuredHeadlines = found;
				const picked = new Set(found.keys());
				const fits = (r) => r[1].length <= HEADLINE_MAX && !picked.has(norm(r[1]));
				headlines = shuffle(D.headlines.filter(fits).map(tile), 7);
				// a step that filters its headlines (players: …, tone: …) gets its own pool.
				// Each row is [date, headline, url, [name index], [topic index], score, tone]
				const pools = {};
				for (const key of poolKeys.filter(Boolean)) {
					const [players, tone] = key.split("|");
					const want = players
						.split(",")
						.filter(Boolean)
						.map((p) => D.names.indexOf(p));
					pools[key] = shuffle(
						D.headlines
							.filter(
								(r) =>
									want.every((n) => r[3].includes(n)) &&
									(!tone || r[6] === tone) &&
									fits(r)
							)
							.map(tile),
						11
					);
				}
				filteredHeadlines = pools;
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

	// "2025-05-20" -> "May 2025" for the tiles' small date line
	function shortDate(iso) {
		return new Date(`${iso}T00:00:00Z`).toLocaleDateString("en-US", {
			month: "short",
			year: "numeric",
			timeZone: "UTC"
		});
	}

	const escape = (t) => t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
	// the people a headline names, in <b>: their full name, or their surname alone
	function markNames(text, names) {
		const html = escape(text);
		if (!names.length) return html;
		const forms = [...new Set(names.flatMap((n) => [n, n.split(" ").slice(1).join(" ")]))]
			.filter((f) => f.length > 2)
			.sort((a, b) => b.length - a.length)
			.map((f) => escape(f).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
		return html.replace(new RegExp(`\\b(${forms.join("|")})\\b`, "g"), '<b class="name">$1</b>');
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
	// how long a wipe (transition: wipe) takes to cross the wall, in seconds
	const WIPE = 1.3;
	// how long the TV switch-off and back on (transition: off) takes, in seconds; the
	// screenshots change halfway, in the dark
	const POWER = 1.6;
	// ...and when the reader is scrolling fast (more than FAST_SCROLL screens a second),
	// a quicker one, so the wall isn't still switching when they've moved on
	const POWER_FAST = 0.6;
	const FAST_SCROLL = 1.2;
	// a wall without a title card (header: false) ends quickly, so the text after it
	// comes up soon: how tall its closing blank step is, as a share of the screen
	const END_SPACE = 0.25;

	// background wall: tiles share the screenshot's shape so they sit edge to edge.
	// tiles are at most 100px wide, and at least 16 fit across on narrow screens.
	const TILE_RATIO = 1164 / 2076; // height / width of everything's-racist-fox.png
	const MAX_TILE_W = 180;
	const MIN_COLS = 6;
	// screenshots in static/images/<folder>/grid-N.png (how many each folder has),
	// repeated in order to fill the wall
	const IMAGE_COUNTS = { gridFox: 40, gridOther: 40 };
	const DEFAULT_IMAGES = "gridFox";
	const imageSrc = (set, i) => `${base}/images/${set}/grid-${i % (IMAGE_COUNTS[set] ?? 40)}.png`;

	let gridW = $state(0);
	let gridH = $state(0);
	// the screen's height with the browser's toolbars showing: the pull-outs are placed
	// within it. The wall of tiles behind runs taller, to the height with the toolbars
	// hidden, so a phone shows no empty band at the bottom once they slide away
	let stickyH = $state(0);
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
			const headline = pinned
				? pinned.tile
				: headlines.length
					? headlines[i % headlines.length]
					: null;
			return {
				delay: (order / Math.max(1, cols * rows)) * STAGGER,
				// how far across the wall the tile sits, for the wipe
				across: cols > 1 ? (i % cols) / (cols - 1) : 0,
				headline,
				// one headline per pool; the wall shows the current step's
				texts: Object.fromEntries(
					poolKeys.map((k) => {
						const pool = k ? filteredHeadlines[k] ?? [] : null;
						// a tile that lifts out a headline shows that one in every pool
						if (pinned || !pool) return [k, headline];
						return [k, pool.length ? pool[i % pool.length] : null];
					})
				),
				styled: pinned?.styled ?? "",
				date: pinned?.date ?? ""
			};
		})
	);

	// pull-outs: up to three tiles (five on a step that lists more) lift out of the wall and grow, one per video or
	// highlight in the step's list. Each step's group gets its own tiles and the next
	// layout in the list below, so the pull-outs land somewhere new on every step.
	// Cards are centered and at most 460px wide, so on wide screens they go in the side
	// gutters; on narrow screens there are no gutters, so they go in strips along the
	// top and bottom.
	const CARD_HALF = 460 / 2 + 32; // half the card plus breathing room
	const PAD = 16;
	const TOP_CLEAR = 5; // rem kept clear at the top of the screen
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
	// a step with four or five pull-outs: three on one side, two on the other. Narrow
	// screens have no room for more than three readable cards, so they show the first three
	const WIDE_LAYOUTS_FIVE = [
		[["L", 0.2], ["R", 0.33], ["L", 0.5], ["R", 0.67], ["L", 0.8]],
		[["R", 0.2], ["L", 0.33], ["R", 0.5], ["L", 0.67], ["R", 0.8]]
	];
	// tile index -> { g: group, type, k: place in its list, dx, dy, scale }
	let tiles = $derived.by(() => {
		const map = new Map();
		if (!cols || !rows) return map;
		const gutter = gridW / 2 - CARD_HALF;
		const wide = gutter >= 160;
		const H = stickyH || gridH;
		// pull-outs stay out of the top 5rem of the screen
		const remPx =
			typeof document === "undefined"
				? 16
				: parseFloat(getComputedStyle(document.documentElement).fontSize) || 16;
		const top = TOP_CLEAR * remPx;
		let w, layouts, layoutsFive;
		if (wide) {
			w = Math.min(320, gutter - 2 * PAD, (H * 0.4) / TILE_RATIO);
			const xL = gutter / 2;
			const xR = gridW - xL;
			// heights are shares of the screen below the top band
			const place = (l) => l.map(([side, y]) => [side === "L" ? xL : xR, top + (H - top) * y]);
			layouts = WIDE_LAYOUTS.map(place);
			layoutsFive = WIDE_LAYOUTS_FIVE.map(place);
		} else {
			w = Math.min(gridW * 0.44, (H * 0.2) / TILE_RATIO);
			const h = w * TILE_RATIO;
			const Y = {
				top: top + h / 2,
				top2: top + h / 2 + h * 0.35,
				bottom: H - PAD - h / 2,
				bottom2: H - PAD - h / 2 - h * 0.35
			};
			const place = (l) => l.map(([x, y]) => [gridW * x, Y[y]]);
			layouts = NARROW_LAYOUTS.map(place);
		}
		// the grid is centered, so its overflow is split evenly on each side
		const x0 = (gridW - cols * tileW) / 2;
		const y0 = (gridH - rows * tileH) / 2;
		const scale = w / tileW;
		// a big card on a short screen could still reach the band: nudge it down
		const minY = top + (w * TILE_RATIO) / 2;
		// one tile per video / highlight headline; a single one takes the middle spot
		const spotsFor = (list, n) => (n === 1 ? [list[1]] : list.slice(0, n));
		pulls.groups.forEach((group, g) => {
			const many = group.items.length > 3 && wide;
			const spots = many ? layoutsFive[g % layoutsFive.length] : layouts[g % layouts.length];
			spotsFor(spots, Math.min(group.items.length, spots.length)).forEach(([tx, spotY], k) => {
				const ty = Math.max(spotY, minY);
				// take the tile nearest the spot so it only has a short way to travel,
				// skipping tiles another group already uses
				let col = Math.min(cols - 1, Math.max(0, Math.floor((tx - x0) / tileW)));
				let row = Math.min(rows - 1, Math.max(0, Math.floor((ty - y0) / tileH)));
				while (map.has(row * cols + col)) col = (col + 1) % cols;
				const cx = x0 + (col + 0.5) * tileW;
				const cy = y0 + (row + 0.5) * tileH;
				// k staggers the pull-outs, one after another. `low`: in the lower half of the
				// screen, where a headline card taller than its tile grows upward, not off
				// the bottom (the upper ones grow downward)
				map.set(row * cols + col, { g, type: group.type, k, dx: tx - cx, dy: ty - cy, scale, low: ty > H / 2 });
			});
		});
		return map;
	});

	// a clip tile plays the video at its place in its group's list
	const videoName = (t) => pulls.groups[t.g].items[t.k];
	const videoSrc = (t) => `${base}/video/${videoName(t)}.mp4`;
	const posterSrc = (t) => `${base}/video/${videoName(t)}.jpg`;
	const FEATURE_STAGGER = 0.15; // seconds between each pull-out
	// a clip tile first lights up and starts playing where it sits in the wall, then
	// lifts out: how long it plays in place, and how long the lift takes (seconds)
	const CLIP_LIGHT_UP = 0.8;
	const CLIP_LIFT = 1.1;
	// on the step before a step that pulls clips (when it shows screenshots), those clips:
	//   "off"     wait as stills
	//   "playing" already play in their places, as faint as the rest of the wall
	//   "lit"     already lit, outlined and playing, so their own step only lifts them out
	const CLIPS_EARLY = "off";
	// pulled-out clips and headlines get an outline: red for Fox News (clips are told
	// apart by file name; the headlines are all Fox), black for the rest
	const FOX_CLIPS = /^(fox|watters)-/;
	const OUTLINE = { fox: "var(--wnba-red)", other: "#000" };
	const OUTLINE_W = 3; // px, at the clip's pulled-out size
	// the clip being heard: a thicker outline in its own colour, set off by a thin white gap
	const ACTIVE_OUTLINE = "var(--wnba-orange)";
	const ACTIVE_OUTLINE_W = 5; // px
	const ACTIVE_GAP = 2; // px of white between the clip and its outline
	// the screenshots in the wall: in colour or gray, and how faintly they show
	const WALL_COLOR = false;
	const WALL_OPACITY = 0.15;
	// the headline tiles: longest headline used (so few get cut off), and whether the
	// people named in them stand out in bold (Doc: wallNames: true | false)
	const HEADLINE_MAX = 95; // characters
	const WALL_NAMES = String(copy.meta?.wallNames ?? "true").trim().toLowerCase() !== "false";
	const outlineOf = (t) => (FOX_CLIPS.test(videoName(t)) ? OUTLINE.fox : OUTLINE.other);

	// a clip is heard only while it's pulled out on a step that names it (audio: …), it's
	// that clip's turn, and the reader has turned sound on; it starts again from the top
	// when its turn comes, and turning sound on joins it wherever it's got to. When it
	// loops back round, its turn is over (done). The video is unmuted for its turn
	// (clipSound).
	let turn = $state(0);
	// a clip the reader clicked, heard in place of the step's own turns until it ends
	let picked = $state(null);
	$effect(() => {
		// each step starts with the first clip named
		sceneIndex;
		turn = 0;
		picked = null;
	});
	// the clips the step names for sound that are actually pulled out (a phone shows only
	// the first three), so the turn never passes to a clip that isn't on screen
	let shownClips = $derived(
		new Set([...tiles.values()].filter((t) => t.g === activeGroup && t.type === "clips").map(videoName))
	);
	let voices = $derived(scene.audio ? scene.audio.filter((name) => shownClips.has(name)) : []);
	let speaking = $derived(picked ?? (voices.length ? voices[turn % voices.length] : null));
	// a clip's turn is over: after a clicked clip, the step's turns carry on from it (from
	// the next named clip, or where they left off); with none named, the clicked clip
	// keeps playing
	function nextTurn() {
		if (!picked) return (turn += 1);
		if (!voices.length) return;
		const i = voices.indexOf(picked);
		if (i >= 0) turn = i + 1;
		picked = null;
	}
	// a click on any pulled-out clip makes it the one heard, from the top. If sound is
	// off, the click turns it on too (inside the tap, so a phone allows it).
	function pickClip(name, cell) {
		if (closing) return;
		const soundOff = !sound.on || sound.blocked;
		if (speaking === name && !soundOff) return;
		const i = voices.indexOf(name);
		if (i >= 0) {
			turn = i;
			picked = null;
		} else picked = name;
		const video = cell.querySelector("video");
		if (video && soundOff) {
			video.currentTime = 0;
			clipSound.play(name, video);
			toggleSound();
		}
	}
	// while the title page is up, the corner sound switch plays the call
	$effect(() => {
		if (!(config.header && id === "intro" && wallInView && shownIndex === undefined)) return;
		sound.call = CALL;
		return () => (sound.call = null);
	});
	// tell the corner sound switch whether this wall can play sound right now
	$effect(() => {
		sound.playable[id] = wallInView && !closing && activeGroup >= 0 && (!!scene.audio || !!picked);
		return () => delete sound.playable[id];
	});
	// `on`: it's this clip's turn to be heard (whether or not sound is on, so a tap on
	// a sound switch can start it straight away)
	function audible(node, opts) {
		let { on, name, done } = opts;
		let last = 0;
		const watch = () => {
			if (on && node.currentTime + 0.3 < last) done();
			last = node.currentTime;
		};
		node.addEventListener("timeupdate", watch);
		const start = () => {
			node.currentTime = last = 0;
			clipSound.play(name, node);
		};
		if (on) start();
		return {
			update(next) {
				const was = on;
				({ on, name, done } = next);
				if (on && !was) start();
				else if (!on && was) clipSound.stop(node);
			},
			destroy() {
				node.removeEventListener("timeupdate", watch);
				if (on) clipSound.stop(node);
			}
		};
	}

	// only play while pulled out, so the hidden clips don't run in the background
	function playWhen(node, on) {
		wallVideos.add(node);
		const set = (v) => {
			wallVideos.want(node, v);
			v ? node.play().catch(() => {}) : node.pause();
		};
		set(on);
		return { update: set, destroy: () => wallVideos.remove(node) };
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

<svelte:window onscroll={measure} onresize={measure} bind:innerWidth={viewW} />

<div
	class="grid-wall grid-wall-{id}"
	class:no-title={!config.header}
	class:filling={wallFilling}
	style="--end-space: {END_SPACE * 100}svh"
	use:watchView
>
	<div class="sticky" bind:clientHeight={stickyH}>
        {#if config.header && id == "intro"}
        <header
            class="intro-wall-header"
            class:off={shownIndex !== undefined && shownIndex >= TITLE_STEPS}
            class:title-down={titleOnWall}
            class:call-in-byline={callStyle === "byline"}
        >
            <h1>
                <span class="hedLeft"><span class="hed-words" bind:this={hedLeftEl} style:transform={titleMoves.left}>{copy.meta.hedLeft}</span></span>
                <span class="glitch" style="--src: url({base}/images/cc-combo.png)">
                    <img class="base" src="{base}/images/cc-combo.png" width="494" height="1200" alt="Caitlin Clark shoots over the Fox News logo"/>
                    {#each strips as s}
                        <img
                            class="strip"
                            src="{base}/images/cc-combo.png"
                            width="494"
                            height="1200"
                            alt=""
                            aria-hidden="true"
                            style="--top: {s.top}%; --bottom: {100 - s.bottom}%; --dx: {s.dx}px; animation-delay: {s.delay}s;"
                        />
                    {/each}
                    <span class="static" aria-hidden="true"></span>
                    {#if callStyle === "bubble"}
                        <span class="call-bubble">
                            <span class="call-words">{@html callText}</span>
                            <span class="call-credit">— {@html callCredit}</span>
                        </span>
                    {/if}
                </span>
                <span class="hedRight"><span class="hed-words" bind:this={hedRightEl} style:transform={titleMoves.right}>{copy.meta.hedRight}</span></span>
            </h1>
            {#if callStyle === "corner"}
                <a class="call-corner {callSpot}" href={callLink} target="_blank" rel="noopener">
                    <MessageCircle strokeWidth={1.25} fill="#fff" aria-hidden="true" />
                    <span class="call-corner-words">“{@html callShort}”</span>
                </a>
            {/if}
            <div class="byline">
                <p>
                    {#if callStyle === "byline"}
                        <span class="call-line">“{@html callText}” <span class="call-credit">— {@html callCredit}</span></span>
                    {/if}
                    By {@html copy.meta.byline}, with {@html copy.meta.with}
                    <span class="scroll-hint" aria-hidden="true">{@html arrowSvg}</span>
                </p>
            </div>
        </header>
        {:else if config.header && id == "outro"}
            <div class="outro-header" class:off={shownIndex !== undefined}>
                <h2>This coverage matters</h2>
            </div>
        {/if}
        <div class="kicker-spot" class:off={wall === "empty" || closing}>
            {#key kicker}
                <p
                    class="kicker"
                    class:other={kicker == "Other outlets"}
                    in:wipeLabel={{ delay: KICKER_OUT, duration: KICKER_IN }}
                    out:wipeLabel={{ duration: KICKER_OUT }}
                >
                    <span class="live-dot" aria-hidden="true"></span>Now Playing {kicker}
                </p>
            {/key}
        </div>
        <!-- the switch-off: a black screen behind the wall, and the bright line and dot -->
        {#key powerKey}
            {#if powering}
                <div class="crt-black" style="--power: {powerTime}s" aria-hidden="true"></div>
                <div class="crt-line" style="--power: {powerTime}s" aria-hidden="true"></div>
            {/if}
        {/key}
        <!-- the band of static a wipe sends across the wall -->
        {#key wipeKey}
            {#if wiping}
                <div class="wipe-band" style="--wipe: {WIPE}s" aria-hidden="true"></div>
            {/if}
        {/key}
        <!-- wall of screenshots / headlines behind the steps -->
        <div
            class="bg-grid"
            class:wiping
            class:powering
            class:closing
            class:names={WALL_NAMES}
            class:harsh={activePool.endsWith("|negative")}
            aria-hidden="true"
            bind:clientWidth={gridW}
            bind:clientHeight={gridH}
            style="--cols: {cols}; --rows: {rows}; --tile-w: {tileW}px; --tile-h: {tileH}px; --light-up: {CLIP_LIGHT_UP}s; --lift: {CLIP_LIFT}s; --wipe: {WIPE}s; --power: {powerTime}s; --outline-w: {OUTLINE_W}px; --active-outline: {ACTIVE_OUTLINE}; --active-outline-w: {ACTIVE_OUTLINE_W}px; --active-gap: {ACTIVE_GAP}px; --outline-fox: {OUTLINE.fox}; --wall-filter: {WALL_COLOR ? 'none' : 'grayscale(100%)'}; --wall-opacity: {WALL_OPACITY};"
        >
            {#each gridCells as cell, i (i)}
                {@const spot = tiles.get(i)}
                {@const f = spot && (spot.g === activeGroup || spot.g === heldGroup) ? spot : undefined}
                {@const ready = !!spot && spot.g === readyGroup}
                {@const pickable = f?.type === "clips" && !closing}
                <!-- each grid spot. A tile that pulls out leaves a copy of itself behind
                     (the stand-in), so the wall keeps no gap where it was -->
                <div class="slot">
                {#if spot}
                    <div
                        class="cell {wall} stand-in"
                        class:hidden={ready && CLIPS_EARLY === "playing"}
                        style="--d: {cell.delay}s; --across: {cell.across};"
                    >
                        {#each imageSets as set (set)}
                            <img
                                src={spot.type === "clips" ? posterSrc(spot) : imageSrc(set, i)}
                                alt=""
                                class:on={set === shownSet}
                            />
                        {/each}
                        {#each poolKeys as k (k)}
                            {@const h = cell.texts[k]}
                            <p class:on={k === activePool}>
                                {#if h}
                                    <span class="tile-meta">Fox News{#if h.date} · {h.date}{/if}</span>
                                    <span class="tile-head">{@html h.html}</span>
                                {/if}
                            </p>
                        {/each}
                    </div>
                {/if}
                <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
                <div
                    class="cell {wall}"
                    class:lifter={!!spot}
                    class:featured={f}
                    class:pickable
                    class:speaking={f?.type === "clips" && !closing && sound.on && speaking === videoName(spot)}
                    onclick={pickable ? (e) => pickClip(videoName(spot), e.currentTarget) : undefined}
                    class:pull-clips={f?.type === "clips"}
                    class:ready={ready && CLIPS_EARLY === "lit"}
                    class:quiet={ready && CLIPS_EARLY === "playing"}
                    class:lift-now={f?.type === "clips" && liftNow}
                    class:pull-heads={f?.type === "heads"}
                    class:low={f?.low}
                    class:has-clip={!!cell.date}
                    class:quick={featureSeen && !!spot}
                    style="--d: {cell.delay}s; --across: {cell.across}; {f ? `--dx: ${f.dx}px; --dy: ${f.dy}px; --s: ${f.scale}; --fd: ${f.k * FEATURE_STAGGER}s;` : ''} {f?.type === 'clips' || ready ? `--outline: ${outlineOf(spot)};` : ''}"
                >
                    <!-- a tile that plays a clip shows that clip's own frame in the wall,
                         so the screenshot comes to life when it lifts out -->
                    {#each imageSets as set (set)}
                        <img
                            src={spot?.type === "clips" ? posterSrc(spot) : imageSrc(set, i)}
                            alt=""
                            class:on={set === shownSet}
                        />
                    {/each}
                    {#if spot?.type === "clips"}
                        <video
                            src={videoSrc(spot)}
                            poster={posterSrc(spot)}
                            muted
                            loop
                            playsinline
                            preload="metadata"
                            use:playWhen={wallInView && ((!!f && !closing) || ready)}
                            use:audible={{
                                on: wallInView && !!f && !closing && speaking === videoName(spot),
                                name: videoName(spot),
                                done: nextTurn
                            }}
                        ></video>
                    {/if}
                    <!-- one headline per pool, stacked; the current step's shows -->
                    {#each poolKeys as k (k)}
                        {@const h = cell.texts[k]}
                        <p class:on={k === activePool}>
                            {#if h}
                                <span class="tile-meta">Fox News{#if h.date} · {h.date}{/if}</span>
                                <span class="tile-head">{@html h.html}</span>
                            {/if}
                        </p>
                    {/each}
                </div>
                {#if f?.type === "heads" && cell.date}
                    <!-- the headline card sits outside the tile, at its pulled-out size, so
                         it isn't scaled up (Safari would blur it). It flies out from the
                         tile and ends with no transform. Mounted on pull-out so the
                         headline's scramble plays as it arrives. -->
                    <div
                        class="clip-out"
                        class:low={spot?.low}
                        style="--dx: {spot?.dx ?? 0}px; --dy: {spot?.dy ?? 0}px; --s: {spot?.scale ?? 1}; --fd: {(spot?.k ?? 0) * FEATURE_STAGGER}s; --d: {cell.delay}s; --w: {tileW * (spot?.scale ?? 1)}px; --h: {tileH * (spot?.scale ?? 1)}px;"
                        transition:fade={{ duration: 300, delay: (spot?.k ?? 0) * FEATURE_STAGGER * 1000 }}
                    >
                        <div class="clip-wrap">
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
						<p class="card">
							{@html clipPops(faces(step.text, base), base)}
						</p>
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
    /* looks come from the global .kicker in app.css; this only places it. The old and
       new labels share the spot while one wipes out and the other wipes in */
    .kicker-spot {
        position: absolute;
        top: 16px;
        left: 16px;
        z-index: 2;
        transition: opacity 300ms ease;
    }
    .kicker-spot .kicker {
        position: absolute;
        top: 0;
        left: 0;
        margin: 0;
        white-space: nowrap;
    }
    /* hidden before the first step, while the header is up */
    .kicker-spot.off {
        opacity: 0;
    }
    .kicker.other {
        background-color: var(--color-fg);
    }
    /* blinking "live" dot before the label */
    .live-dot {
        display: inline-block;
        width: 6px;
        height: 6px;
        margin-right: 5px;
        border-radius: 50%;
        background: #fff;
        vertical-align: 1px;
        animation: live-blink 1.2s ease-in-out infinite;
    }
    @keyframes live-blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.15; }
    }
    @media (prefers-reduced-motion: reduce) {
        .live-dot {
            animation: none;
        }
    }
    .bg-grid {
        position: absolute;
        inset: 0;
        /* past the bottom of the frame by however much taller the screen gets when a
           phone's toolbars slide away (nothing on desktop) */
        bottom: calc(100svh - 100lvh);
        z-index: 0;
        display: grid;
        grid-template-columns: repeat(var(--cols), var(--tile-w));
        grid-template-rows: repeat(var(--rows), var(--tile-h));
        /* center the wall so any clipped overflow is split evenly between edges */
        place-content: center;
        overflow: hidden;
        transition: opacity 600ms ease;
        /* nothing in the wall can be highlighted or dragged, even by a drag that starts
           outside it */
        -webkit-user-select: none;
        user-select: none;
        -webkit-touch-callout: none;
    }
    .bg-grid :is(img, video) {
        -webkit-user-drag: none;
    }
    /* each tile holds a screenshot and a headline stacked on top of each other;
       the wall state decides which one shows */
    .cell {
        position: relative;
        overflow: hidden;
        transition:
            transform 600ms cubic-bezier(0.2, 0.7, 0.2, 1),
            opacity 400ms ease;
    }
    /* a grid spot: the tile, and (for a tile that pulls out) its stand-in under it */
    .slot {
        position: relative;
        pointer-events: none;
    }
    .slot > .cell {
        position: absolute;
        inset: 0;
    }
    /* the copy that stays in the wall while its tile is pulled out */
    .stand-in.hidden {
        visibility: hidden;
    }
    /* a tile that pulls out shows nothing of its own while it sits in the wall (its
       stand-in shows the wall there), only once it lights up or lifts out */
    .bg-grid .cell.lifter:not(.featured):not(.ready) :is(img, p) {
        opacity: 0;
    }
    /* step 1: lifted out of the wall, moved to its spot and scaled up */
    /* pull-outs go one after another (--fd); going back they all return at once */
    .cell.featured {
        z-index: 1;
        transform: translate(var(--dx), var(--dy)) scale(var(--s));
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
        transition-delay: var(--fd);
    }
    /* a clip lights up and plays where it sits first (--light-up), then lifts out
       slowly (--lift) */
    .cell.featured.pull-clips {
        transition-duration: var(--lift);
        transition-delay: calc(var(--fd) + var(--light-up));
        /* the outline is drawn before the scale-up, so it's thinned to match */
        box-shadow: 0 0 0 calc(var(--outline-w) / var(--s)) var(--color-fg);
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
        transition: opacity 500ms ease var(--fd);
    }
    /* the next step's clips, lit and playing in place, outlined, ahead of their step */
    .cell.ready {
        z-index: 1;
        box-shadow: 0 0 0 var(--outline-w) var(--outline);
    }
    .cell.ready video,
    .cell.images.ready img.on {
        opacity: 1;
        filter: none;
        transition:
            opacity 500ms ease,
            filter 500ms ease;
    }
    /* playing early but not lit: the clip shows as faintly as the screenshots around it */
    .cell.quiet video {
        opacity: var(--wall-opacity);
        filter: var(--wall-filter);
    }
    .cell.images.quiet img.on {
        opacity: 0;
    }
    /* the clip being heard: its own thicker outline, past a thin white gap, above the
       other clips (drawn before the scale-up, so thinned to match) */
    .cell.featured.pull-clips.speaking {
        z-index: 2;
        box-shadow:
            0 0 0 calc(var(--active-gap) / var(--s)) #fff,
            0 0 0 calc((var(--active-gap) + var(--active-outline-w)) / var(--s)) var(--active-outline);
    }
    /* the wall's tiles don't catch the pointer (no text cursor, no selecting the
       hidden headlines); only a pulled-out clip does: click it to hear it */
    .cell {
        pointer-events: none;
    }
    .cell.pickable {
        pointer-events: auto;
        cursor: pointer;
    }
    .cell.pickable :is(img, p) {
        pointer-events: none;
    }
    /* already lit, so they lift out without waiting */
    .cell.featured.pull-clips.lift-now {
        transition-delay: var(--fd);
    }
    /* the closing step (wall: cleared): the tiles fade out one by one, each at its own
       scattered delay (--d), the pulled-out ones along with the rest */
    .bg-grid.closing .slot > .cell {
        opacity: 0;
        transition: opacity 500ms ease var(--d);
    }
    .cell.images.quick img,
    .cell.text.quick p {
        transition-delay: 0s;
    }
    /* "heads" pull-out: the pulled-out headline at full strength */
    .cell.pull-heads p.on {
        opacity: 1;
        transition-delay: var(--fd);
    }
    /* the screenshot comes up to full color in place, as its clip starts */
    .cell.images.pull-clips img.on {
        opacity: 1;
        filter: none;
        transition:
            opacity 500ms ease,
            filter 500ms ease;
        transition-delay: var(--fd);
    }
    /* a pulled-out headline becomes a gallery clipping (.clip-out, below); the tile
       itself lifts out empty underneath it */
    .cell.has-clip.pull-heads {
        overflow: visible;
        box-shadow: none;
    }
    .cell.has-clip.pull-heads p.on {
        opacity: 0;
    }
    /* the headline card's box: where the pulled-out tile ends up, at that size,
       placed without a transform so the text stays sharp */
    .clip-out {
        position: absolute;
        z-index: 2;
        left: calc(50% + var(--dx) - var(--w) / 2);
        top: calc(50% + var(--dy) - var(--h) / 2);
        width: var(--w);
        height: var(--h);
        pointer-events: none;
    }
    .bg-grid.closing .clip-out {
        opacity: 0;
        transition: opacity 500ms ease var(--d);
    }
    /* a headline card is taller than its tile: it hangs from the tile's top edge, or in
       the lower half of the screen stands on its bottom edge, so it stays on screen */
    .clip-wrap {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        /* flies out from the tile, like the clips, and ends with no transform */
        animation: clip-fly 600ms cubic-bezier(0.2, 0.7, 0.2, 1) var(--fd) backwards;
    }
    .clip-out.low .clip-wrap {
        align-items: flex-end;
    }
    @keyframes clip-fly {
        from {
            transform: translate(calc(var(--dx) * -1), calc(var(--dy) * -1)) scale(calc(1 / var(--s)));
        }
    }
    .clip-inner {
        flex: 0 0 auto;
        width: 100%;
    }
    .clip-inner :global(.clip) {
        border: 2px solid var(--color-fg);
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
        filter: var(--wall-filter);
    }
    /* a headline tile: a small source-and-month line, then the headline, set like a
       page of clippings with a thin rule above each instead of a box */
    .cell p {
        margin: 0;
        padding: 0.55em 0.7em 0;
        background: var(--wnba-tan-bg);
        border-top: 1px solid rgba(0, 0, 0, 0.18);
        font-size: calc(var(--tile-h) / 8.5);
        overflow: hidden;
    }
    .tile-meta {
        display: block;
        margin-bottom: 0.35em;
        font-family: var(--font-sans);
        font-size: 0.68em;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--wnba-red);
    }
    .tile-head {
        font-family: var(--font-serif);
        line-height: 1.2;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .tile-head :global(b.name) {
        font-weight: inherit;
    }
    /* the names version: the people stand out, the rest of the headline sits back */
    .names .tile-head {
        color: var(--color-gray-500, #888);
    }
    .names .tile-head :global(b.name) {
        font-weight: 700;
        color: var(--color-fg);
    }
    /* on a step of harsh headlines, the names go red */
    .names.harsh .tile-head :global(b.name) {
        color: var(--color-fg);
    }
    /* only the current step's headlines show; when a step filters them (players,
       tone), each tile swaps over at its own scattered delay */
    .cell.text p {
        transform: none;
        transition-delay: var(--d);
    }
    .cell.text p.on {
        opacity: 0.5;
    }
    /* screenshots sit back faintly. Only the current folder's shows; when the folder
       changes, each tile swaps old for new at its own scattered delay */
    .cell.images img {
        transition-delay: var(--d);
    }
    /* a wipe: each column swaps as the band of static passes over it, left to right */
    .bg-grid.wiping .cell.images img {
        transition-duration: 120ms;
        transition-delay: calc(var(--across) * var(--wipe));
    }
    .wipe-band {
        position: absolute;
        top: 0;
        bottom: 0;
        left: 0;
        width: 180px;
        z-index: 1;
        pointer-events: none;
        background:
            repeating-linear-gradient(to bottom, rgb(0 0 0 / 0.25) 0 1px, transparent 1px 3px),
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"),
            #bdb6a8;
        /* soft trailing edge, hard leading edge */
        mask: linear-gradient(to right, transparent, #000 70%, #000);
        -webkit-mask: linear-gradient(to right, transparent, #000 70%, #000);
        box-shadow: 4px 0 0 rgb(255 255 255 / 0.9);
        animation:
            wipe-across var(--wipe) linear forwards,
            wipe-snow 0.12s steps(1) infinite;
    }
    @keyframes wipe-across {
        0% {
            transform: translateX(-180px);
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        100% {
            transform: translateX(calc(100vw + 20px));
            opacity: 0;
        }
    }
    @keyframes wipe-snow {
        0% { background-position: 0 0, 0 0, 0 0; }
        33% { background-position: 0 1px, -40px 30px, 0 0; }
        66% { background-position: 0 2px, 50px -20px, 0 0; }
    }
    /* the switch-off (transition: off): the wall squeezes to a line, the line to a dot,
       a beat of black, then the same in reverse with the new screenshots */
    .bg-grid.powering {
        animation: crt-wall var(--power) ease-in-out forwards;
    }
    .bg-grid.powering .cell.images img {
        transition: none;
    }
    /* the next step's clips wait until the wall is back on */
    .bg-grid.powering .cell.featured,
    .bg-grid.powering .cell.pull-clips video,
    .bg-grid.powering .cell.images.pull-clips img.on {
        transition-delay: calc(var(--power) * 0.9 + var(--fd));
    }
    @keyframes crt-wall {
        0% { transform: scale(1, 1); opacity: 1; filter: brightness(1); }
        22% { transform: scale(1, 0.004); opacity: 1; filter: brightness(3); }
        23% { opacity: 0; }
        70% { transform: scale(1, 0.004); opacity: 0; }
        71% { opacity: 1; filter: brightness(3); }
        100% { transform: scale(1, 1); opacity: 1; filter: brightness(1); }
    }
    .crt-black {
        position: absolute;
        inset: 0;
        z-index: 0;
        background: var(--color-fg);
        pointer-events: none;
        animation: crt-black var(--power) ease-in-out forwards;
    }
    @keyframes crt-black {
        0% { opacity: 0; }
        12% { opacity: 1; }
        82% { opacity: 1; }
        100% { opacity: 0; }
    }
    .crt-line {
        position: absolute;
        left: 0;
        right: 0;
        top: 50%;
        height: 3px;
        margin-top: -1.5px;
        z-index: 1;
        background: #fff;
        border-radius: 3px;
        box-shadow:
            0 0 8px 2px rgb(255 255 255 / 0.9),
            0 0 24px 6px rgb(190 220 255 / 0.6);
        pointer-events: none;
        opacity: 0;
        animation: crt-line var(--power) ease-in-out forwards;
    }
    @keyframes crt-line {
        0%, 20% { opacity: 0; transform: scaleX(1); }
        22% { opacity: 1; transform: scaleX(1); }
        34% { opacity: 1; transform: scaleX(0.004); }
        42% { opacity: 0; transform: scaleX(0.004); }
        56% { opacity: 0; transform: scaleX(0.004); }
        60% { opacity: 1; transform: scaleX(0.004); }
        70% { opacity: 1; transform: scaleX(1); }
        73%, 100% { opacity: 0; transform: scaleX(1); }
    }
    @media (prefers-reduced-motion: reduce) {
        .bg-grid.powering,
        .crt-black,
        .crt-line {
            animation: none;
        }
        .crt-line {
            display: none;
        }
    }
    @media (prefers-reduced-motion: reduce) {
        .wipe-band {
            display: none;
        }
    }
    .cell.images img.on {
        opacity: var(--wall-opacity);
        transform: none;
    }
    /* step 2: headlines leave in the same scattered order they arrived */
    .cell.cleared p {
        transition-delay: var(--d);
    }
    .intro-wall-header {
        position: relative;
        z-index: 1;
        width: 100%;
        height: 100%;
        transition:
            opacity 400ms ease,
            visibility 0s;
    }
    /* a plain fade; visibility flips after the fade so it can't be clicked or read once gone */
    .intro-wall-header.off {
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
        width: 100%;
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: center;
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

    @media (max-width: 900px) {
		h1 {
            --img-h: 60svh;
            --img-w: calc(var(--img-h) * 494 / 1200);
			font-size: 2rem;
            margin-left: 3%;
		}
        /* a max-width stops grid items stretching, so pin each one to the image side */
        .hedLeft {
            max-width: 120px;
            justify-self: end;
        }
        .hedRight {
            max-width: 200px;
            justify-self: start;
        }
        .hedLeft,
        .hedRight {
            text-wrap: balance;
        }
	}

    @media (max-width: 550px) {
		h1 {
			font-size: 1.5rem;
            --img-h: 40svh;
            --img-w: calc(var(--img-h) * 494 / 1200);
            margin-left: 5%;
		}
	}

    h1 img {
        display: block;
        height: var(--img-h);
        max-height: 800px;
        width: auto;
    }
    /* --- TV static + glitch --- */
    .glitch {
        position: relative;
        display: block;
    }
    /* the announcer's call as a speech bubble, popping in beside the image; its tail
       points off the right edge, toward the broadcast booth, not at Clark */
    .call-bubble {
        position: absolute;
        top: 6%;
        left: 58%;
        z-index: 2;
        width: max-content;
        max-width: 15em;
        padding: 0.55em 0.8em 0.5em;
        background: #fff;
        border: 2px solid #000;
        border-radius: 1.2em;
        font-family: var(--font-sans);
        font-size: 1.05rem;
        font-style: normal;
        line-height: 1.2;
        text-align: left;
        animation: bubble-pop 450ms cubic-bezier(0.2, 1.4, 0.4, 1) 0.9s both;
    }
    .call-bubble::after {
        content: "";
        position: absolute;
        right: -14px;
        bottom: 10px;
        width: 18px;
        height: 14px;
        background: #fff;
        border: 2px solid #000;
        border-left: none;
        border-bottom: none;
        transform: skewY(-35deg);
    }
    .call-words {
        display: block;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.01em;
    }
    .call-bubble .call-credit {
        display: block;
        margin-top: 0.3em;
        font-size: 0.7em;
        color: var(--color-gray-700, #555);
    }
    @keyframes bubble-pop {
        from {
            opacity: 0;
            transform: scale(0.6) rotate(-4deg);
        }
        to {
            opacity: 1;
            transform: scale(1) rotate(-2deg);
        }
    }
    /* the call over the byline takes a line's room: the image gives it up */
    .call-in-byline h1 {
        --img-h: 68svh;
    }
    /* the call as an epigraph over the byline */
    .call-line {
        display: block;
        margin-bottom: 0.6em;
        font-family: var(--font-serif);
        font-style: italic;
        font-size: 1.1rem;
    }
    .call-line .call-credit {
        font-style: normal;
        font-family: var(--font-sans);
        font-size: 0.8em;
        color: var(--color-gray-700, #555);
    }
    /* the short call in a speech bubble in the top-right corner, linking to the clip;
       its tail points down and left, toward the title */
    /* (kept left of the corner sound button) */
    .call-corner {
        position: fixed;
        top: 2.5rem;
        right: 2.5rem;
        z-index: 2;
        display: grid;
        place-items: center;
        width: 6.5rem;
        height: 6.5rem;
        color: #000;
        text-decoration: none;
        animation: bubble-pop 450ms cubic-bezier(0.2, 1.4, 0.4, 1) 0.9s both;
    }
    .call-corner :global(svg) {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
    }
    /* the icon's tail is at its lower left: flipped so it points out of the page */
    /* to the right of the byline, a little above it */
    .call-corner.lower {
        top: auto;
        right: auto;
        left: 74%;
        bottom: 9svh;
    }
    .call-corner.lower :global(svg) {
        transform: scaleX(-1);
    }
    .call-corner.upper :global(svg) {
        transform: scale(-1, -1);
    }
    /* the line keeps its thin weight however big the bubble is drawn */
    .call-corner :global(svg path) {
        vector-effect: non-scaling-stroke;
    }
    .call-corner-words {
        position: relative;
        max-width: 5.6em;
        font-family: var(--font-display);
        font-size: 1.15rem;
        font-style: italic;
        font-weight: 400;
        line-height: 1.05;
        text-align: center;
    }
    .call-corner:hover .call-corner-words {
        text-decoration: underline;
    }
    /* the title dropped down onto the wall: the rest of the title page fades, and the
       words (moved by titleMoves) turn red on a strip of the page colour. When the steps
       move on, the whole header fades, the title with it, where it is. */
    .hed-words {
        display: inline-block;
        padding: 0 0.15em;
        transform-origin: 0 0;
        transition:
            transform 700ms cubic-bezier(0.2, 0.9, 0.3, 1),
            color 500ms ease,
            background-color 500ms ease;
    }
    .title-down .hed-words {
        color: var(--color-fg);
        background-color: var(--wnba-tan-bg);
    }
    .intro-wall-header .glitch,
    .intro-wall-header .byline,
    .intro-wall-header .call-corner {
        transition: opacity 300ms ease, filter 300ms ease;
    }
    .title-down .glitch,
    .title-down .byline {
        opacity: 0;
        pointer-events: none;
    }
    /* (the bubble's pop-in holds its opacity, so it fades with a filter) */
    .title-down .call-corner {
        filter: opacity(0);
        pointer-events: none;
    }
    /* smaller screens: the title doesn't move onto the wall, it fades out with the rest
       of the title page (titleMoves stays empty at this width) */
    @media (max-width: 900px) {
        .title-down .hed-words {
            color: inherit;
            background-color: transparent;
        }
        .intro-wall-header .hedLeft,
        .intro-wall-header .hedRight {
            transition: opacity 300ms ease;
        }
        .title-down .hedLeft,
        .title-down .hedRight {
            opacity: 0;
        }
    }
    @media (max-width: 600px) {
        .call-corner {
            right: 2.5rem;
            width: 5.5rem;
            height: 5.5rem;
        }
        /* the title fills the lower right on phones, so the bubble always sits up top,
           its tail pointing up and out */
        .call-corner.lower {
            top: 0.75rem;
            right: 3.5rem;
            bottom: auto;
            left: auto;
        }
        .call-corner.lower :global(svg) {
            transform: scale(-1, -1);
        }
        .call-corner-words {
            font-size: 0.95rem;
        }
    }
    /* phones: the bubble keeps inside the image's right edge, a little smaller */
    @media (max-width: 600px) {
        .call-bubble {
            left: auto;
            right: -4px;
            top: 1%;
            max-width: 9.5em;
            font-size: 0.8rem;
        }
    }
    @media (prefers-reduced-motion: reduce) {
        .call-bubble,
        .call-corner {
            animation: none;
        }
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
        pointer-events: none;
	}
	/* no title card to scroll past: the first step comes up over the wall sooner */
	.no-title .steps {
		margin-top: -60svh;
	}
	.step {
		min-height: 90svh;
		display: flex;
		align-items: center;
		justify-content: center;
        pointer-events: none;
	}
    .step:last-of-type {
        opacity: 0;
        pointer-events: none;
    }
    /* no title card: the closing blank step is short, so the wall clears and lets go
       of the screen soon after the last card */
    .no-title .step:last-of-type {
        min-height: var(--end-space);
    }
	.card {
        font-size: 18px;
        line-height: 1.5;
		max-width: 460px;
		padding: 14px 18px;
		background: var(--color-white);
		/* a black outline, so the card stands clear of the wall */
		border: 1px solid var(--color-rule);
        border-radius: 4px;
		opacity: 0.4;
		transition: opacity 300ms ease;
        pointer-events: auto;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);

	}
	.step.active .card {
		opacity: 1;
	}
	/* phones: the cards keep 2rem clear of the screen's edges, as the other scrollies' do */
	@media (max-width: 640px) {
        .card {
            font-size: 16px;
        }
		.step {
			padding: 0 2rem;
		}
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
